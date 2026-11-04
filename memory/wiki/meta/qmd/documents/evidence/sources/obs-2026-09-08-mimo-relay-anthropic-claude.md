---
type: source
title: "Observation: mimo-relay 底模验证：实际运行在 Anthropic Claude 上"
tags:
  - mimo-relay
  - 底模
  - anthropic
  - claude
  - billing_usage
  - usage_source
  - apimimo
status: observation
created: 2026-09-08
updated: 2026-09-08
slug: obs-2026-09-08-mimo-relay-anthropic-claude
relevance: critical
observed_at: 2026-09-08T08:14:31.250Z
source_context: 用户要求验证 Pi agent 当前使用的 mimo-relay 底模
---

# 🔴 Observation: mimo-relay 底模验证：实际运行在 Anthropic Claude 上

验证了 Pi agent 当前使用的 mimo-relay 底模。当前配置：provider=mimo-relay, model=mimo-v2.5, apiKey=sk-dee42..., baseUrl=https://apimimo.zaiyunding.com/v1。/v1/models 返回 owned_by=claude, endpoints=['anthropic','openai']。模型自报为 "MiMo-v2.5, developed by Xiaomi LLM Core Team"。但 usage/billing_usage 字段揭露了真正的底模：usage_source='anthropic', billing_usage.source='claude_messages', 含 claude_cache_creation_5_m_tokens 等 Anthropic 专有字段。结论：mimo-v2.5 实际运行在 Anthropic Claude 基础设施上，One-API 中转用 Claude Messages API 作为上游，通过系统提示让 Claude 以 MiMo 身份回答。与之前 DeepSeek relay（alias→Gemini/GPT-4o）不同，这条链路底模一致（Claude）。

*Relevance: critical*
*Context: 用户要求验证 Pi agent 当前使用的 mimo-relay 底模*
*Tags: mimo-relay 底模 anthropic claude billing_usage usage_source apimimo*

---
*Observed: 2026-09-08T08:14:31.250Z*
