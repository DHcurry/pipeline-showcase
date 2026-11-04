---
type: source
title: "Observation: QQ 链路验证通过；pi-tui 依赖声明改为 peerDeps"
tags:
  - qqbot
  - pi-hermes-memory
  - peerDependencies
  - lock
  - leader-election
status: observation
created: 2026-10-28
updated: 2026-10-28
slug: obs-2026-10-28-qq-pi-tui-peerdeps
relevance: low
observed_at: 2026-10-28T09:48:40.313Z
source_context: 验证 QQ Bot 连接状态并修复扩展依赖告警
---

# 📝 Observation: QQ 链路验证通过；pi-tui 依赖声明改为 peerDeps

QQ Bot 链路端到端验证正常（2026-10-28）：leader 25836 持锁并认领 c2c 会话 22E11125B720CD40ECF968D809F7357A，本会话作为 follower 连接属正常选主行为。用模块自带 auth.js+api-client.js 发被动回复测试消息成功（initialMsgSeqMap 设 msgId seq=900 避免与 leader 已用 seq 撞车去重），返回 msg_id ROBOT1.0_QGnQD5AN...。另修复了 pi-hermes-memory@0.9.9 的扩展加载告警：把 @earendil-works/pi-tui 从 dependencies 移到 peerDependencies 值 "*"（宿主提供）。注意：该修复是改已安装包，下次 npm 更新该包会被覆盖，届时需重打或向上游提 PR。

*Relevance: low*
*Context: 验证 QQ Bot 连接状态并修复扩展依赖告警*
*Tags: qqbot pi-hermes-memory peerDependencies lock leader-election*

---
*Observed: 2026-10-28T09:48:40.313Z*
