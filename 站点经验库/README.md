---
title: 站点经验库
tags:
  - skills
  - site-memory
  - crawler
  - reverse
---

# 站点经验库

这个目录记录 **测试阶段** 产生的站点经验，不依赖线上运行。

目标是让同一个网站、同类市场、同类币种、同类接口阶段不重复犯错。

## GitHub 边界

GitHub 只保留本目录的 README、`_templates/` 和通用结构说明。真实 domain 目录是本地项目库，默认不上传。

真实项目经验只沉淀可复用的 SKILLS 判断、排查顺序、失败模式、字段/状态含义、影响回归和下次进入任务前必须看的操作细节。禁止把真实抓包数据、完整响应数据、token、cookie、账号、订单、支付、旅客、会话 profile、HAR/jsonl 原始文件或可还原业务数据写入可上传内容。

如果某次实战需要保留数据证据，只能放在本地 domain 目录或交付包里，并在对外总结中改写成脱敏摘要。

## 正式沉淀准入

研发阶段只写本地临时项目库;正式站点经验必须等真实接口测试后再沉淀。每条经验至少写清:

- 已完成确认: 哪个接口/链路/market/stage 真实通过,证据是什么。
- 未完成确认: 哪个保护、字段、状态或链路仍 blocked / incomplete。
- 踩坑点: 哪些错误路径下次不再重复处理。
- 可复用结论: 脱敏字段含义、状态判断、JSON Pointer、回归命令和影响范围。

没有真实接口测试或明确失败证据时,不能写入成功经验,只能留在临时项目库或负例/复核账本。

## 维度

站点经验按这些维度拆分：

- domain：例如 `thaiairways.com`
- market：例如 `CN`、`JP`、`US`、`TH`
- locale：例如 `zh-CN`、`ja-JP`、`en-US`
- currency：例如 `CNY`、`JPY`、`USD`、`THB`
- stage：search、cart、order、payment
- protection：none、js-crypto、waf、reese84、captcha
- framework：standalone、314

## 固定文件

每个站点目录建议包含：

```text
site-memory.md
market-matrix.md
knowledge-graph.md
impact-regression.md
known-failures.md
test-log-lessons.md
route-decisions.md
eval-backlog.md
change-log.md
```

## 使用规则

在处理新网站或同网站新市场前，先查：

1. 是否已有 domain 目录。
2. 是否已有 market/locale/currency 记录。
3. 是否已有相同 stage 的 known failure。
4. 是否已有 endpoint / request-field / response-field / state / protection 节点和边。
5. 是否已有 impact-regression 记录说明改动影响面。
6. 是否已有 eval backlog 尚未沉淀到 Skill。

测试完成后，必须写回：

1. 成功/失败摘要。
2. 从日志提炼的失败模式。
3. 是否更新 Skill。
4. 是否新增 eval。
5. 是否更新版本。
6. 是否更新 knowledge-graph.md 的节点和边。
7. 是否更新 impact-regression.md 的影响面、必跑回归和数据校验。

