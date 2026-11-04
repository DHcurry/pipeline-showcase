---
name: "pi-agent-sdk-modelruntime-integration"
description: "Pi Agent SDK 接入：ModelRuntime.completeSimple 调用与配置链路的硬性规则"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
在任何项目中以 Pi Agent SDK 为骨架接入 LLM 时，以及遇到“ModelRuntime 未初始化”报错时。

## Procedure
1. 普通 LLM 调用用 ModelRuntime.completeSimple(model, context)（非流式）；Context.messages 的 Message 必须带 timestamp，否则 TS2345。
2. createAgentSession 仅用于 agent/session 场景（重、易静默失败、每项目一 session 目录）；真正以 Pi 为骨架需 AgentSession + 自定义 tools。
3. 配置流：syncPiFiles → 设置页写 auth.json + models.json → registerProvider → 必须 setRuntimeApiKey → getModel → completeSimple；断任何一环都会报“ModelRuntime 未初始化”。
4. ModelRuntime.create()/initialize() 抛错必须 re-throw，吞掉会只报“未初始化”。
5. base_url 已含 /v1 或以 /chat/completions 结尾时禁止再拼接（双 /v1 导致 404）。
6. JSON 契约三层兜底（Pi 未暴露 response_format）：systemPromptOverride 注入“只输出JSON” + extractJSON/repairTruncatedJson + 调用方字段默认值；pi-ai 具备 ConstrainedSamplingConfig(type:'json_schema', strict)/toolChoice 底层能力（@earendil-works/pi-ai/dist/types.d.ts）但 AgentSession.prompt() 未暴露。AgentSession 天性是对话/agent 运行时，与 workflow 按钮式确定性字段错位——热路径走 AIService.callLLM，AgentRuntime promptSession 承担 project_id 会话记忆。

## Pitfalls
- 禁止因初始化失败改直连 HTTP 绕过 Pi SDK——用户明确纠正过，必须保留 Pi SDK 接入。
- 初始化异常被吞掉时只能看到“未初始化”，丢失真实原因。

## Verification
1. completeSimple 成功返回；故意断开配置链路任一环时能看到真实抛出的错误。