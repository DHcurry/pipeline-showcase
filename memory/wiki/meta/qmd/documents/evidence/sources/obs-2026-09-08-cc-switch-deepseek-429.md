---
type: source
title: "Observation: cc-switch DeepSeek 中转：上游 429 限流导致间歇性卡住"
tags:
  - cc-switch
  - deepseek
  - 中转
  - "429"
  - 限流
  - proxy_config
status: observation
created: 2026-09-08
updated: 2026-09-08
slug: obs-2026-09-08-cc-switch-deepseek-429
relevance: high
observed_at: 2026-09-08T01:31:33.675Z
source_context: 排查 cc-switch DeepSeek 中转无法继续操作的原因
---

# ⭐ Observation: cc-switch DeepSeek 中转：上游 429 限流导致间歇性卡住

诊断 cc-switch（数据库 ~/.cc-switch/cc-switch.db）的 deepseek-relay 配置：Base URL https://apimimo.zaiyunding.com/v1，apiKey sk-1ac1d311...，api=openai-completions，模型 deepseek-v4-flash / deepseek-v4-pro。当前 Claude provider 'apids' (d27016ed...) 同域名 apimimo.zaiyunding.com，ANTHROPIC_MODEL=deepseek-v4-flash[1M]，auth token 同键。proxy_request_logs 显示今天 09:16-09:18 有 9 次失败 = HTTP 500 内包 429 NEW-API 限流错误（1分钟内最多300次，检查ApiKey），22 次请求中 13 成功。结论：不是 cc-switch 配置损坏，是上游中转网关对该 key 限流（burst 后间歇被拒），窗口滚动恢复。proxy_config(claude): streaming_first_byte_timeout=90, streaming_idle_timeout=180, non_streaming_timeout=600, auto_failover 关。

*Relevance: high*
*Context: 排查 cc-switch DeepSeek 中转无法继续操作的原因*
*Tags: cc-switch deepseek 中转 429 限流 proxy_config*

---
*Observed: 2026-09-08T01:31:33.675Z*
