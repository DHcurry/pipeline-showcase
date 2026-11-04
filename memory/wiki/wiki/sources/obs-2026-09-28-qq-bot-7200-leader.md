---
type: source
title: "Observation: QQ Bot 断连已修复：坏锁改名后 7200 接管 leader"
tags:
  - qqbot
  - pi-qq-integration
  - lock
  - leader-election
status: observation
created: 2026-09-28
updated: 2026-09-28
slug: obs-2026-09-28-qq-bot-7200-leader
relevance: high
observed_at: 2026-09-28T14:38:47.830Z
source_context: 诊断并修复 QQ Bot 无法连接
---

# ⭐ Observation: QQ Bot 断连已修复：坏锁改名后 7200 接管 leader

QQ Bot 断连已修复（2026-09-28 22:37）。执行：把 79 字节全 NUL 的 ~/.pi/agent/qq-integration.lock 改名为 .bak（持有者 PID 5908 已死）。11 秒后本会话实例 PID 7200 打出「旧 leader 已退出，本实例接管锁成为新 leader」，WS 连上 wss://api.sgroup.qq.com/websocket 并 Ready（session_id 2c42d798），其余 3 个实例（9624/11632/14432）自动转 follower 并同步 settings。端到端实测：\\.\pipe\pi-qq-7200 存在、registry leader=7200 且陈旧 5908 已被 pruneDead 清除、getAppAccessToken 200、POST /v2/users/{openid}/messages → 200 返回 msg_id ROBOT1.0_QGnQD5AN...。修复后日志 0 条「与 leader 断开」。待办（未改代码）：lock.js writeLock 需原子写、readLock 解析失败应视为锁失效、follower 侧也需 pruneDead、"已发回 QQ" 只能真发送成功才打印。

*Relevance: high*
*Context: 诊断并修复 QQ Bot 无法连接*
*Tags: qqbot pi-qq-integration lock leader-election*

---
*Observed: 2026-09-28T14:38:47.830Z*
