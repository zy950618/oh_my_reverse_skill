# 验证码经验库

本目录沉淀 Web/H5 验证码逆向经验,记录 provider 通用流程、站点绑定参数、接口调用链、token/状态生命周期、业务 API 解锁关系、图谱更新和回归验证的实战记忆库。

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
