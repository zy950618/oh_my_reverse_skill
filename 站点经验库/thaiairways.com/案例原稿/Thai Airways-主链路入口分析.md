# Thai Airways - 主链路入口分析

日期：2026-04-18
范围：非支付链路主认证与后续请求头传播
参考来源：
- [[AI Reverse Toolkit/JS 逆向任务下单模板]]
- /mnt/c/Users/Administrator/Desktop/thaiairways_probe/thaiairways_non_payment_assessment_2026-04-14.md
- /mnt/c/Users/Administrator/Desktop/thaiairways_probe/tg_python_booking_client.py

## 一、分析目标

本笔记只回答一个问题：

Thai Airways 非支付链路里，真正的主入口是不是 identification？

结论：不是。
真正的主入口是：
- POST /flight/auth
- 返回 access_token
- 返回响应头 booking_session_id
- 之后由公共 header 注入逻辑传播到后续 booking API

identification 只是局部识别头，不是主链路统一认证入口。

## 二、主链路结论

### 1. 主链路认证三件套
从本地评估报告可恢复：
- booking_authorization: Bearer <access_token>
- booking_session_id: <flight/auth 响应头返回>
- source / hostName / channel / Accept-Language

对应证据：
- 评估报告第 13-16 行明确指出，核心预订链路主要依赖上述请求头，而不是“所有接口都需要复杂业务加密”。

### 2. 正确入口是 flight/auth
从 Python 客户端可恢复：
- `flight_auth()` 直接调用 `POST /flight/auth`
- payload 包含：
  - itineraries
  - officeId
  - countryCode
  - languageCode
  - user: website
  - userGroup: online
- 响应体读取：`access_token`
- 响应头读取：`booking_session_id`
- 并保存在 `auth_state`

证据：
- tg_python_booking_client.py 第 114-153 行

## 三、flight/auth 的位置与职责

### 1. 请求位置
Python 客户端中：
- `response = self.session.post(self._url("/flight/auth"), headers=self._base_headers(), json=payload)`

证据：
- tg_python_booking_client.py 第 139-144 行

### 2. 请求前基础头
`_base_headers()` 返回：
- content-type: application/json
- source: website
- hostName: https://www.thaiairways.com
- channel: online
- Accept-Language: en-th

证据：
- tg_python_booking_client.py 第 60-67 行

### 3. flight/auth 的职责
它不是普通查询接口，而是“建立 booking 会话”的入口。

flight/auth 返回后，系统拿到：
- access_token
- booking_session_id
- guest_office_id

证据：
- tg_python_booking_client.py 第 147-151 行

## 四、后续 headers 如何传播

### 1. 传播函数
Python 客户端中，后续 headers 都由 `_booking_headers()` 统一构造。

逻辑：
1. 先取 `_base_headers()`
2. 再追加：
   - booking_authorization: Bearer <access_token>
   - booking_session_id: <booking_session_id>

证据：
- tg_python_booking_client.py 第 69-79 行

### 2. 传播到哪些请求
当前客户端中已明确传播到：
- /flight/search/air-calendars
- /flight/search/air-bounds
- 以及后续 cart / order 类 booking API（在整体客户端设计与报告结论中明确）

证据：
- tg_python_booking_client.py 第 185-189 行：air-calendars 使用 `_booking_headers()`
- tg_python_booking_client.py 第 232-236 行：air-bounds 使用 `_booking_headers()`
- 评估报告第 49-67 行：主链路接口列表

## 五、浏览器侧状态保存点

本地评估报告显示，flight/auth 之后前端会把这些值保存到浏览器状态中：
- sessionStorage.officeId
- sessionStorage.sessionId
- store.booking.apiAccessToken
- store.booking.apiOfficeId
- store.booking.api_booking_session_id

证据：
- 评估报告第 95-105 行附近

这说明主链路的传播结构是：
1. /flight/auth 建立会话
2. 响应值进入 sessionStorage / store
3. 后续 interceptor / 公共 header 逻辑从这些状态里取值
4. 注入到 air-calendars / air-bounds / cart / order 请求中

## 六、为什么 identification 不是主入口

### 1. identification 的真实性质
评估报告显示：
- identification 的明文由 `window.fingerPrintValue + input`、timestamp、screenWidth 组成
- 再做 RSA-OAEP-SHA256
- Base64 输出
- 某些情况下写到 sessionStorage.executionDapi

证据：
- 评估报告第 122-158 行

### 2. identification 的适用范围
报告还明确指出：
- 不要假设所有接口都要带 identification
- 它更像某些下游服务/补充业务接口的识别头
- 只有真实调用路径明确使用 identification 时才生成

证据：
- 评估报告第 160-170 行

### 3. 因此优先级判断
对 Thai Airways 来说：
- 第一优先级：flight/auth -> booking_authorization / booking_session_id
- 第二优先级：主链路 headers 传播与状态机
- 第三优先级：局部 identification 入口

## 七、主链路状态机（最小版本）

基于现有证据，可先抽成最小状态机：

1. INIT
   - 尚无 booking 会话

2. AUTH_READY
   - 已调用 /flight/auth
   - 已拿到 access_token
   - 已拿到 booking_session_id

3. SEARCH_READY
   - 可调用 /flight/search/air-calendars
   - 可调用 /flight/search/air-bounds

4. CART_READY
   - 可进入 cart / traveler / regulatory-document

5. ORDER_READY
   - 可进入 /order/remarks / /order/special-keywords / order

当前已知最重要的状态推进字段：
- access_token
- booking_session_id
- guest_office_id
- selectedBoundId
- cart / order 相关实体 ID

## 八、当前最大阻塞

虽然协议主链路已经较清晰，但当前环境仍被前置 challenge 阻断：
- booking 页面注入 AWS WAF challenge.js
- /booking/、/flight/auth、/flight/search/air-calendars 实测会返回 403 CloudFront Request blocked

证据：
- 评估报告第 10-12 行
- 评估报告第 25-27 行
- 评估报告第 174-188 行
- Python 客户端说明第 27-29 行：它假设你已经有 WAF-passed session

## 九、下一步最该继续分析什么

如果继续沿“模板化逆向分析”往下做，下一步最值得做的是：

### 方向 A：主链路状态传播分析
目标：
- 把 `access_token`、`booking_session_id`、`selectedBoundId`、cart/order ID 的字段血缘串起来
- 形成 search -> cart -> order 的状态机图

### 方向 B：按接口逐个确认 header 最小集
目标：
- 明确哪些接口只要 booking_authorization + booking_session_id
- 哪些接口还需要额外 header 或 identification

### 方向 C：把当前证据落成 adapter 结构
目标：
- adapter.yaml
- runbook.md
- API protocol
- workflow state 文档

## 十、一句话总结

Thai Airways 非支付链路的真正主入口不是 identification，而是 `POST /flight/auth`。

其核心传播路径是：
`flight/auth -> access_token + booking_session_id -> sessionStorage/store -> _booking_headers/interceptor -> air-calendars / air-bounds / cart / order`。

因此，后续分析应优先围绕“会话建立与传播链”，而不是先把 identification 当成全局主矛盾。