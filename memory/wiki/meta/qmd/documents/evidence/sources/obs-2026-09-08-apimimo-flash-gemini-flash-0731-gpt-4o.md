---
type: source
title: "Observation: apimimo 中转别名底模：flash=Gemini、flash-0731=GPT-4o"
tags:
  - apimimo
  - one-api
  - 中转
  - 底模
  - deepseek
  - gemini
  - gpt-4o
status: observation
created: 2026-09-08
updated: 2026-09-08
slug: obs-2026-09-08-apimimo-flash-gemini-flash-0731-gpt-4o
relevance: high
observed_at: 2026-09-08T02:31:27.847Z
source_context: 用户询问 cc-switch 里 deepseek 中转的底模到底是什么
---

# ⭐ Observation: apimimo 中转别名底模：flash=Gemini、flash-0731=GPT-4o

探测中转 apimimo.zaiyunding.com 的底模：网关是 One-API v1.0.0-rc.25（X-New-Api-Version 头），Caddy 反代。公开 /v1/models 只暴露中转自定义别名 deepseek-v4-flash / -0731 / -pro / -pro-0813，不暴露真实底模。用 chat/completions 让模型自报身份：deepseek-v4-flash 自报 = gemini-2.5-pro-exp-03-25(Google)；deepseek-v4-flash-0731 自报 = gpt-4o-2024-11-20(OpenAI)。结论：所谓 "DeepSeek" 中转的实际底模并非 DeepSeek，别名指向的底层是 Google/OpenAI 模型，且不同别名可能走不同上游 channel（One-API 多channel 负载/多 provider 镜像）。429 实测命中：错误全文 = "您已达到总请求数限制：1分钟内最多请求300次，包括失败次数"。注意：模型自报身份可能受训练数据影响，插件方若希望确认真实映射需 admin channel 列表，用户侧无法直接读取。

*Relevance: high*
*Context: 用户询问 cc-switch 里 deepseek 中转的底模到底是什么*
*Tags: apimimo one-api 中转 底模 deepseek gemini gpt-4o*

---
*Observed: 2026-09-08T02:31:27.847Z*
