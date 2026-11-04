---
type: source
title: "Observation: Pi Agent Android 模拟器测试成功"
tags:
  - android
  - emulator
  - nodejs
  - success
  - pi-agent
status: observation
created: 2026-08-23
updated: 2026-08-23
slug: obs-2026-08-23-pi-agent-android
relevance: critical
observed_at: 2026-08-23T08:32:37.859Z
---

# 🔴 Observation: Pi Agent Android 模拟器测试成功

在 Android 10 (API 29) x86_64 模拟器上成功运行 Node.js！

关键发现：
1. nodejs-mobile v18.20.4 的 libnode.so 在 Android 10 上正常工作
2. Node.js 只能在进程中调用一次 node::Start()，第二次会崩溃
3. pi-web-chat 的 server.js 有 WASM 兼容性问题（SIGTRAP in Runtime_WasmDebugBreak）
4. 简单的 HTTP 服务器 launcher.js 可以正常运行
5. assets 中的文件名会被 Android 构建工具修改（.tar.gz → .tar）
6. 需要通过 JNI setenv() 设置环境变量，System.setProperty() 不会传递给 Node.js

技术栈验证：
- JDK 17.0.2 + Android SDK 34 + NDK 26.1.10909125
- nodejs-mobile v18.20.4 (libnode.so x86_64)
- Android 10 (API 29) x86_64 模拟器

*Relevance: critical*
*Tags: android emulator nodejs success pi-agent*

---
*Observed: 2026-08-23T08:32:37.859Z*
