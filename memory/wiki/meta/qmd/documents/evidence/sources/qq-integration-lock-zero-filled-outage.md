---
type: source
title: QQ Bot 全线断连根因：lock 文件被写零字节
status: insight
category: devops
created: 2026-09-28
updated: 2026-09-28
slug: qq-integration-lock-zero-filled-outage
---

# QQ Bot 全线断连根因：lock 文件被写零字节

现象：`~/.pi/agent/qq-integration.log` 每 30 秒刷「与 leader 断开，进入重连等待」（累计 29917 行），全库 0 次「已连接 ✅」，`\\.\pipe\pi-qq-*` 一个都不存在。

根因：`~/.pi/agent/qq-integration.lock` 在 2026-09-21 06:55:24 被**原地写零**成 79 个 NUL 字节（79 = 原 JSON `{"pid":5908,"startedAt":...,"heartbeatAt":...}` 的精确长度，重建比对逐字节吻合）。lock.js 的 `acquire()` 三段式因此死锁：① `openSync(path,'wx')` → EEXIST；② `readLock()` JSON.parse 失败返回 null → 再试 `wx` → 仍是 EEXIST → 返回 false。**锁文件存在但不可解析** 这条分支被当成「锁被别人删了」，于是永远返回 false，任何实例都无法 `becomeLeader`，QQ WebSocket 无人建立 → 收发全断。

连带问题（pi-qq-integration v0.5.3）：
1. `writeLock()` 用非原子 `writeFileSync`（registry.js 的 `atomicWrite` 是 tmp+rename，锁文件没有），崩溃/休眠即可能留零字节。
2. `pruneDead()` 只在 leader 的定时器里跑，leader 死后 registry 里 `leader=5908 / leaderSock=\\.\pipe\pi-qq-5908` 永不清除，follower 于是对着不存在的管道无限重连（`maybeTakeoverLeader` 每次都被坏锁挡回）。
3. **静默降级**：follower 的 `sendToQq` 走 `_ipcClient.send()`，而 ipc client 未连接时 `send()` 直接 return，随后 message_end 照样打 `已发回 QQ [c2c]` —— 消息根本没出机器却显示成功；另有 `sendToQq 跳过: role=null` 46 次。

验证手段（可复用）：`python` 打开 `\\.\pipe\pi-qq-<pid>` 探测 leader 是否在听；重建 lock JSON 比字节数确认零填充；`POST https://bots.qq.com/app/getAppAccessToken` 拿 200 说明 appId/appSecret 与网络都没问题（本次即如此），故障纯在本地选主。

处置：删除/改名坏锁文件后 ≤30s 内某个实例的 `scheduleRetryFollower → maybeTakeoverLeader` 会拿到锁升级为 leader，日志出现「旧 leader 已退出，本实例接管锁成为新 leader」+「已连接 ✅（leader）」即恢复。

相关：[[concepts/插件vs真hermes-技能维护差异]]

*Category: devops*

---
*Captured: 2026-09-28*

## Related

_Add links to related pages._
