---
title: 仓库漂移历史
tags:
  - metrics
  - drift
  - history
  - ci
---

# 仓库漂移历史

每周一 UTC 01:17 由 CI Job A 自动追加(`.github/workflows/skill-bench.yml` 的 `schedule` 触发)。

本文件是 v0.3.4 创建的初始模板。CI 首次 schedule 触发后会在下面追加第一条快照。

按时间顺序追加,新条目在最下面。

人工读取时关注:**总分趋势下降 ≥ 3 分** 或 **单 Skill 评级降级**(如 90+ → 80-89 区间),需要打开对应 Skill 的 `evals/` 检查是否漂移。

---

<!-- 以下由 CI 自动追加 -->

## 2026-06-15

### 1-业务流程层
- 均分: total=96.5 (s=25.0/o=21.5/d=20.0)
- `imperva-waf-reese84` v0.2.0 total=96 (s=25/o=21/d=20) — 高可用,产出与真实一致
- `reverse-js-crawler` v0.2.0 total=96 (s=25/o=21/d=20) — 高可用,产出与真实一致
- `skills-evaluation-governance` v0.2.0 total=96 (s=25/o=21/d=20) — 高可用,产出与真实一致
- `website-314-api-delivery` v0.2.0 total=98 (s=25/o=23/d=20) — 高可用,产出与真实一致

### 2-JS逆向工具层
- 均分: total=92.5 (s=25.0/o=19.75/d=17.75)
- `ai-reverse-skill-creator` v0.5.0 total=89 (s=25/o=17/d=17) — 可用,一致性证据待补
- `ast-deobfuscate` v0.5.0 total=96 (s=25/o=21/d=20) — 高可用,产出与真实一致
- `env-patch` v0.5.0 total=92 (s=25/o=20/d=17) — 高可用,产出与真实一致
- `find-crypto-entry` v0.5.0 total=93 (s=25/o=21/d=17) — 高可用,产出与真实一致

### 4-通用规范层
- 均分: total=0 (s=0/o=0/d=0)
- `karpathy-guidelines` vunknown total=20 (s=20/o=?/d=?) — 原始材料

### 5-沉淀工具层
- 均分: total=92.0 (s=25.0/o=21.0/d=16.0)
- `site-api-adapter` v0.2.0 total=92 (s=25/o=21/d=16) — 高可用,产出与真实一致

### 6-验证码逆向层
- 均分: total=98.0 (s=25.0/o=23.0/d=20.0)
- `captcha-service-delivery` v0.1.0 total=98 (s=25/o=23/d=20) — 高可用,产出与真实一致

