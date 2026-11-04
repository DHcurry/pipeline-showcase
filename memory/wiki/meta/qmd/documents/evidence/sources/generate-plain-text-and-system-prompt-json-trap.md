---
type: source
title: generate 纯文本化：system prompt 的"始终输出JSON"才是惯凶
status: insight
category: bugfix
created: 2026-09-30
updated: 2026-09-30
slug: generate-plain-text-and-system-prompt-json-trap
---

# generate 纯文本化：system prompt 的"始终输出JSON"才是惯凶

## 问题

用户质问"为什么一定要返回 JSON？大模型输出本来就是文本"——generate 间歇性输出 JSON 壳进文本框、降级丢字段。要求删大纲模式+诊断修复。

## 诊断结论（三层根因）

1. **架构层**：界面贪图一次调用捎带结构化字段（style_match/suggestions/style_profile/outline），用 JSON 契约绑架了纯文本主体——得不偿失
2. **user prompt 层**：DEFAULT_GENERATE_PROMPT 的"输出一行严格合法 JSON"段
3. **真正惯凶——session system prompt**：AgentSession 的 systemPromptOverride 写着"始终只输出严格合法的 JSON"（当初为 analyze 加的），**改了 user prompt 后模型仍输出 `{"mode","platform","script"}` 惯性 JSON**——system 级指令压过 user 级

## 修复（全部验证）

- generate 纯文本化：promptSession 直接拿文本（runSessionJSON/rawFallback/json_fallback 全删），响应只留 generated_text/style_author/style_distilled/self_check/session
- system prompt 分支化："要求 JSON 时才 JSON，否则纯文本，绝不把文案包进 JSON"
- cleanGenerated 壳剥离兜底（session 历史惯性残留时剥出 generated_text/script/content 正文）
- **大纲模式整体删除**：editorMode/outlineText/按大纲生成全文/seed/suggestions/styleMatch/styleProfile chips 全链路清除（tsc 过+CDP 点创作零错误）
- **保留 JSON 的三处**（合理场景）：analyze（思维导图必须结构化）、蒸馏/导入（档案数据）、自检（判定结果）——各自独立调用，不绑架文案

## 验证

generate keys=generated_text,style_author,style_distilled,self_check,session；纯文本无壳 true；首行即文案（带 // 停顿标记）；self_check 90%；CDP 全请求 200 零页面错误。

## 教训

- **改输出格式要三层同查**：user prompt、system prompt（session 级！）、历史惯性——只改其一必留残余
- systemPromptOverride 是 AgentSession 的全局人设，"始终输出X"类绝对指令会污染该 session 所有任务类型，应写成**条件分支**
- 需要结构化的场景（analyze/档案）单独调用，别让文案主体迁就捎带字段

相关：[[session-json-bracket-repair]] [[imitate-style-content-separation]]

*Category: bugfix*

---
*Captured: 2026-09-30*

## Related

_Add links to related pages._
