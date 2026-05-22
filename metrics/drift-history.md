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
