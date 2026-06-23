# 验证码经验库

本目录沉淀 Web/H5 验证码逆向经验,记录 provider 通用流程、站点绑定参数、接口调用链、token/状态生命周期、业务 API 解锁关系、图谱更新和回归验证的实战记忆库。

## GitHub 边界

GitHub 只保留 README、`_templates/`、`providers/` 和 `_example.com/` 示例。`domains/<真实域名>/` 是本地项目经验库，默认不上传。

provider 通用流程可以上传；真实站点绑定、真实 token、挑战响应、浏览器 profile、抓包文件、完整请求/响应和可还原业务数据只能本地保存。对外沉淀只写脱敏后的流程、失败模式、状态生命周期判断和下次复测步骤。

## 正式沉淀准入

验证码经验库只收真实复测后的精炼结论:

- `browser_automated_verified`: 授权浏览器自动化完成,且最终业务 API 后端接受并 repeat_verified。
- `human_reviewed_verified`: 人工只完成可见 challenge,后续证据完整且 repeat_verified。
- `blocked_by_manual_challenge` / `blocked_by_protection`: 可以记录为失败模式和下次处理边界,不能写成自动通过。
- `unverified`: 只留在临时项目库或待复核清单,不能进入成功经验。

正式条目只写 token 字段名、存在性、长度、TTL、状态绑定、JSON Pointer 和脱敏流程;不写 token 值、挑战 payload、真实请求体或业务数据。

## 目录

```text
验证码经验库/
  _templates/          通用模板
  providers/           provider 通用流程,不写站点私有结论
  domains/<domain>/    站点绑定、真实抓包、旧新对照、影响回归
```

## 使用顺序

1. 先读 `providers/<provider>.md`。
2. 再读 `domains/<domain>/captcha-memory.md`。
3. 新抓包前写 capture plan。
4. 抓 `clean_unverified`、`verified`、`repeat_verified` 三组。
5. 更新站点绑定、图谱、影响回归和失败样本。

## 记录范围

每条经验必须写清:

- provider / type / site binding。
- capture_id / run_id / captured_at / browser_profile_id / state_reset。
- verified-vs-unverified diff。
- token/state lifecycle。
- business API unlock / deny relation。
- graph delta and impact regression。
- old-vs-new reuse decision。
