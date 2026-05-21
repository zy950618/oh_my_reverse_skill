# Thai Airways - 非支付整条链路结果（最终版）

日期：2026-04-18
范围：搜索 / 选 bound / 加车 / 旅客 / 证件 / 联系方式 / 取 cart / 生单 / remarks / special-keywords
边界：仅整理已恢复并已实证的非支付业务链路结果；不包含支付，也不包含未授权访问控制绕过。

参考证据：
- /mnt/c/Users/Administrator/Desktop/thaiairways_probe/thaiairways_search_payload_and_bounds_validation_2026-04-14.md
- /mnt/c/Users/Administrator/Desktop/thaiairways_probe/thaiairways_guest_post_cart_header_resolution_2026-04-14.md
- /mnt/c/Users/Administrator/Desktop/thaiairways_probe/thaiairways_non_payment_assessment_2026-04-14.md
- /mnt/c/Users/Administrator/Desktop/thaiairways_probe/tg_python_booking_client.py

## 一、最终结论

Thai Airways 非支付链路，已经有完整证据表明在“已建立 booking session 且处于已放行会话”的前提下，可以推进到生单后的 post-order 动作。

已经恢复并实证成功的链路是：

1. /flight/auth
2. /flight/search/air-calendars
3. /flight/search/air-bounds（去程）
4. /flight/search/air-bounds（返程）
5. /cart/
6. /cart/traveler
7. /cart/regulatory-document
8. /cart/contact
9. /cart/retrieve
10. /order/
11. /order/remarks
12. /order/special-keywords

因此，非支付 guest booking chain 可以认为“基本贯通”。

## 二、整条链路的真正主线

这条链路的主线不是 identification，而是：

`flight/auth -> access_token + booking_session_id -> booking headers -> search -> bounds -> cart -> traveler/regulatory -> contact -> retrieve -> order -> remarks/special-keywords`

主认证依赖：
- booking_authorization: Bearer <access_token>
- booking_session_id
- source: website
- hostName
- channel: online
- Accept-Language

## 三、逐步结果

### 第 1 步：建立 booking session
接口：
- POST /flight/auth

作用：
- 建立 guest booking 会话
- 获取后续 booking API 所需的 access_token 和 booking_session_id

已恢复出的关键请求体字段：
- itineraries
- officeId
- countryCode
- languageCode
- user: website
- userGroup: online

已恢复出的关键返回：
- body.access_token
- body.guest_office_id
- header.booking_session_id

结果：
- 已成功建立 booking session

## 第 2 步：calendar 查询
接口：
- POST /flight/search/air-calendars

关键规则：
- calendar payload 和 bounds payload 不同，不能混用
- commercialFareFamilies 必须存在

成功 payload 的关键要点：
- commercialFareFamilies: ["PVBUSINESS", "PVECONOMY"]
- itineraries（往返两段）
- searchPreferences.showUnavailableEntries = true
- searchPreferences.showMilesPrice = false

结果：
- 返回 200
- 已拿到真实 fare calendar 数据

## 第 3 步：bounds 查询（去程）
接口：
- POST /flight/search/air-bounds

关键规则：
- 需要的不是 calendar payload，而是 searchPayload
- 必带：
  - noOfAdt
  - noOfChd
  - noOfInf
  - noOfYth
  - travelers
  - isRequestedBound
  - requested itinerary 上的 flexibility

去程请求关键点：
- 第 1 段 itinerary: isRequestedBound = true
- 第 2 段 itinerary: isRequestedBound = false

结果：
- 返回 200
- 已拿到 outbound airBoundGroups / airBounds / airBoundId / prices 等数据

## 第 4 步：bounds 查询（返程）
接口：
- POST /flight/search/air-bounds

关键规则：
- 必须带 selectedBoundId = 第一段已选 airBoundId
- 第 1 段 itinerary: isRequestedBound = false
- 第 2 段 itinerary: isRequestedBound = true
- flexibility: 3 切到第二段

结果：
- 返回 200
- 已拿到 return side 的 airBoundGroups / airBounds / prices / airOffer

## 第 5 步：创建 cart
接口：
- POST /cart/

关键输入：
- airBoundIds
  - 单程：1 个
  - 往返：2 个（去程 + 返程）

结果：
- 已成功
- 后续可取得 cartId、travelers、airOffers 等信息

Python 客户端对应方法：
- create_cart()
- tg_python_booking_client.py 第 290-300 行

## 第 6 步：旅客信息
接口：
- POST /cart/traveler
- PATCH /cart/traveler

作用：
- 创建或更新 traveler 信息

关键输入：
- cartId
- travelerId
- tid
- passengerTypeCode
- names.firstName / lastName / title
- 可选：gender / dateOfBirth / accompanyingTravelerId

结果：
- 已成功

Python 客户端对应方法：
- upsert_traveler()
- tg_python_booking_client.py 第 302-339 行

## 第 7 步：证件信息
接口：
- POST /cart/regulatory-document
- PATCH /cart/regulatory-document

作用：
- 填充 passport / nationality 等证件信息

关键输入：
- cartId
- travelerId
- nationalityCode
- documentType = passport
- number
- expiryDate
- issuanceCountryCode
- name
- passengerTypeCode

结果：
- 已成功

Python 客户端对应方法：
- upsert_regulatory_document()
- tg_python_booking_client.py 第 341-390 行

## 第 8 步：联系方式
接口：
- POST /cart/contact

关键发现：
- 这个接口不需要 member headers
- 只需要继续沿用 guest booking headers

关键 headers：
- source
- hostName
- channel
- Accept-Language
- booking_authorization
- booking_session_id

示例 payload 形状：
- cartid
- contactRequest: [{contactType, purpose, address}]

结果：
- 201 成功

Python 客户端对应方法：
- create_cart_contact()
- tg_python_booking_client.py 第 392-401 行

## 第 9 步：retrieve cart
接口：
- POST /cart/retrieve

payload：
- {"cartId": "<cartId>"}

结果：
- 200
- 返回完整 cart 数据，包括：
  - travelers
  - regulatoryDetails
  - airOffers
  - prices
  - warnings

Python 客户端对应方法：
- retrieve_cart()
- tg_python_booking_client.py 第 403-411 行

## 第 10 步：创建订单
接口：
- POST /order/

关键修正：
- 之前误判成“必须登录态”，这个判断不准确
- 实测表明：它不需要真实登录态，只需要 booking headers

payload：
- {"cartId": "<cartId>"}

结果：
- 201
- 已成功拿到真实 orderId，例如：DBMQCY / DBNRYC

Python 客户端对应方法：
- create_order()
- tg_python_booking_client.py 第 413-422 行

## 第 11 步：post-order remarks
接口：
- POST /order/remarks

payload 形状：
- orderId
- lastName
- remarks: [{remarkType: GeneralRemark, freetext: ...}]

结果：
- 201

Python 客户端对应方法：
- post_order_remarks()
- tg_python_booking_client.py 第 444-463 行

## 第 12 步：post-order special keywords
接口：
- POST /order/special-keywords

payload 形状：
- orderId
- lastName
- specialKeywords: [{keyword: TFAK, airlineCode: TG}]

结果：
- 201

Python 客户端对应方法：
- post_order_special_keywords()
- tg_python_booking_client.py 第 465-484 行

## 四、哪些接口已证明不需要真实登录态

已实证不需要真实 member login 的接口：
- flight/auth
- flight/search/air-calendars
- flight/search/air-bounds
- cart/
- cart/traveler
- cart/regulatory-document
- cart/contact
- cart/retrieve
- order/
- order/remarks
- order/special-keywords

## 五、哪些接口仍像登录态链路

当前仍更像需要真实 member session 的接口：
- trip/add
- order/retrieve

Python 客户端里也体现了这个区别：
- retrieve_order() 单独要求 Authorization
- add_trip() 单独要求 Authorization

对应位置：
- tg_python_booking_client.py 第 424-442 行

## 六、当前整条链路的最小状态机

1. INIT
   - 尚无 booking session

2. AUTH_READY
   - 已取得 access_token
   - 已取得 booking_session_id

3. CALENDAR_READY
   - 已获得 fare calendar

4. OUTBOUND_BOUND_READY
   - 已选中 outbound bound
   - 已拿到 outbound airBoundId

5. INBOUND_BOUND_READY
   - 已带 selectedBoundId 查询返程
   - 已拿到 inbound bound

6. CART_READY
   - 已创建 cart
   - 已取得 cartId

7. TRAVELER_READY
   - 已写入 traveler
   - 已写入 regulatory-document
   - 已写入 contact

8. ORDER_READY
   - 已 retrieve cart
   - 已 create order
   - 已取得 orderId

9. POST_ORDER_READY
   - 已提交 remarks
   - 已提交 special-keywords

## 七、全链路最关键字段

必须重点跟踪的字段包括：
- access_token
- booking_session_id
- guest_office_id
- commercialFareFamilies
- selectedBoundId
- airBoundIds
- cartId
- travelerId / tid
- regulatory document id（如有）
- orderId
- lastName

## 八、关于 identification 的最终定位

identification 确实存在，且已恢复出其构造逻辑：
- 指纹源：fingerPrintValue + _gid/_ga/device_id_custom
- 加密：RSA-OAEP-SHA256
- 输出：Base64

但它不是这条非支付主链路的统一主认证。

正确定位应是：
- 它是局部接口的识别头
- 不应优先于 booking_authorization / booking_session_id 去处理
- 不应把全链路失败都归因于它

## 九、当前唯一真正的前置阻塞

虽然业务链路已经有完整成功证据，但当前环境前面仍存在 challenge / WAF 阻断。

这意味着：
- 业务协议本身不是主要问题
- 当前真正的外部阻塞仍然发生在“进入已放行会话状态”之前
- 一旦处于已放行的合法 session 环境，上述非支付链路已具备完整可执行证据

## 十、最终一句话结果

Thai Airways 非支付整条链路结果是：

`flight/auth -> air-calendars -> air-bounds(outbound) -> air-bounds(inbound) -> cart -> traveler -> regulatory-document -> contact -> retrieve cart -> order -> remarks -> special-keywords`

这条 guest chain 已有明确实证，且主认证依赖的是 booking session 体系，而不是全局 identification。