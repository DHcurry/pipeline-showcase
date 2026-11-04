---
name: "qq-integration-lock-recovery"
description: "QQ 机器人无法连接/文档发QQ失败时的本地选主锁诊断与恢复"
version: 1
created: "2026-09-28"
updated: "2026-09-28"
---
## When to Use
QQ 机器人无法连接、文档/文件发不到 QQ、或 qq-integration 相关异常时。

## Procedure
1. 先查本地选主锁 C:\Users\16575\.pi\agent\qq-integration.lock：正常应为 JSON；若被原地写成 NUL 字节（如 79B 全 NUL）即锁损坏，QQ 侧不会有报错。
2. 处置：把坏锁改名为 .bak 保留证据，锁管理器 lock.js 会在约 11 秒后自动重建并恢复，无需重启任何会话。
3. 恢复后端到端实测（发一条真实消息确认），并给逐环节状态表。
4. 发文件走 qq-send-file skill（msg_type=7 富媒体，upload_prepare→分片→complete→发送）。

## Pitfalls
- 别误判成 QQ 侧/网络问题——根因曾是本地锁文件损坏。
- 锁文件不要直接删除，改名 .bak 便于取证与回滚。

## Verification
1. qq-integration.lock 为合法 JSON，机器人重连成功。
2. 文档实际送达 QQ（用户确认收到）。
