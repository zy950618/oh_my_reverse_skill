# Thai Airways - JS 逆向任务分析（首轮）

参考模板：[[AI Reverse Toolkit/JS 逆向任务下单模板]]
日期：2026-04-18
范围：非支付链路（搜索 / 加车 / 生单前置分析）
边界：仅做授权自动化、协议理解、系统集成分析；不以绕过未授权访问控制为目标。

## 一、任务判断

该站点不是“纯加签站”，而是混合问题：

- Type C：浏览器态绑定
- Type D：边缘挑战 / WAF challenge
- Type E：业务状态机
- 局部存在 Type B：标准加密（identification 头的 RSA-OAEP-SHA256）

结论：
1. 不应一上来就把目标定义为“完整算法还原”。
2. 应先按模板走“定位入口”，但要区分：
   - 主业务链路认证：booking_authorization + booking_session_id
   - 局部补充识别头：identification
   - 最前置阻塞：AWS WAF challenge / CloudFront Request blocked

## 二、按 JS 逆向任务模板填写

### 模板 1：定位加密入口

目标参数：identification
目标请求：
- 页面：https://www.thaiairways.com/booking/
- 请求特征：booking bundle 中某些下游服务请求头出现 identification
- 参数位置：header

我要的输出（当前已恢复到的程度）：
- 相关脚本：booking bundle helper（报告中记作内部函数 De）
- 函数行为：
  - 明文结构：
    {
      "timestamp": Date.now(),
      "token": window.fingerPrintValue + input,
      "screenWidth": screen.width
    }
  - 加密方式：RSA-OAEP-SHA256
  - 输出：Base64
  - 浏览器侧落点：sessionStorage.executionDapi
- 输入来源优先级：_gid / _ga / localStorage.device_id_custom
- 判断：这是局部识别头，不是所有 booking API 的统一主认证

当前判断：
- identification 更像“补充身份识别 / 反爬识别头”
- 核心 booking API 主链路依赖的并不是它，而是：
  - booking_authorization
  - booking_session_id
  - source / hostName / channel / Accept-Language

### 模板 1 的第二目标：主认证入口

目标参数：booking_authorization / booking_session_id
目标请求：
- 页面：booking 场景
- 请求特征：POST /flight/auth
- 参数位置：header / response header

当前已恢复输出：
- booking_authorization 来源：POST /flight/auth 响应体 access_token
- booking_session_id 来源：POST /flight/auth 响应头 booking_session_id
- 后续公共头：
  - source: website
  - hostName: window.location.origin
  - channel: online
  - Accept-Language
  - booking_authorization: Bearer ...
  - booking_session_id: ...

判断：
- 这才是主预订链路真正应优先追的“认证入口”
- Thai Airways 当前问题不是“先还原 identification 就能跑通”

## 三、适用的模板路径判断

根据 [[AI Reverse Toolkit/JS 逆向任务下单模板]]，本案最适合：

### 路径 C：大型站点稳妥打法
1. 先精确锁定目标函数或模块
2. 只对目标模块解混淆
3. 如果最终要离线跑，再补环境

但本案要拆成两个并行目标：

#### 目标 A：主链路认证与状态机
- flight/auth
- air-calendars
- air-bounds
- cart
- traveler / regulatory / order

#### 目标 B：局部识别头
- identification 的入口、依赖、适用接口范围

其中优先级应为：A > B

## 四、Thai Airways 当前最关键证据

### 1. 主链路协议可行
已有报告显示：
- 纯 Python 做“搜索 / 加车 / 生单”在协议层面可行
- 主链路依赖 booking_authorization + booking_session_id

### 2. 最大阻塞点在 WAF / challenge
已有本地报告显示：
- booking 页面注入 AWS WAF challenge.js
- 当前环境对 /booking/、/flight/auth、/flight/search/air-calendars 等请求实测返回 403 CloudFront Request blocked

### 3. identification 不是主链路统一要求
已有报告显示：
- identification 由 FingerprintJS / _ga / _gid / device_id_custom 衍生
- 使用 RSA-OAEP-SHA256
- 但它更像局部识别头，不应假设所有 booking API 都需要

## 五、第一轮分析结论

### 结论 1
Thai Airways 不能被简单归类为“单纯找 sign 入口”的站点。
它是：
- WAF challenge 前置
- booking auth 建会话
- 多步业务状态机推进
- 局部接口存在 identification 识别头

### 结论 2
若严格按模板下单，当前最应该优先处理的“入口”不是 identification，而是：
- POST /flight/auth 的会话建立入口
- 后续 axios interceptor 中 booking_authorization / booking_session_id 的注入点

### 结论 3
identification 应作为“第二优先级局部加密入口”单独跟踪，而不是作为全站主矛盾。

## 六、建议的下一步处理顺序

1. 先做“主链路入口分析”
   - 目标参数：booking_authorization
   - 目标请求：POST /flight/auth
   - 输出：注入点、状态保存点、后续 headers 传播路径

2. 再做“多步状态机分析”
   - search -> auth -> cart -> traveler/regulatory -> order
   - 输出：关键字段血缘、必须前序步骤、每步最小请求模型

3. 最后做“identification 局部入口分析”
   - 输出：哪些接口真正需要它
   - 不默认把它扩展为全链路必要项

## 七、可直接复用的下一条下单 prompt

```text
$find-crypto-entry
目标参数：booking_authorization / booking_session_id
目标请求：
- 页面：https://www.thaiairways.com/booking/
- 请求特征：POST /flight/auth 以及其后续 booking API 公共请求头注入
- 参数位置：header / response header

我要的输出：
- 生成这两个值的脚本位置
- flight/auth 的调用点
- 响应值写入 sessionStorage/store 的位置
- 后续 interceptor 如何把它们注入 air-calendars / air-bounds / cart / order 请求
- 区分是业务代码、拦截器还是外部 SDK

只定位入口和传播链，不要先尝试完整算法还原。
```

## 八、附：当前不应误判的点

- 不要把所有问题都归因于 identification
- 不要把所有接口都视为“统一加密接口”
- 不要把 WAF challenge 误判成普通业务签名
- 不要在未区分主认证和局部识别头之前，直接进入全量 env-patch
