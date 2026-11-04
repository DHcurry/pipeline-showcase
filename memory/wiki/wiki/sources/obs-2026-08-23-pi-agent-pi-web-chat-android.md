---
type: source
title: "Observation: Pi Agent + pi-web-chat Android 完整运行成功"
tags:
  - android
  - pi-agent
  - pi-web-chat
  - node26
  - success
status: observation
created: 2026-08-23
updated: 2026-08-23
slug: obs-2026-08-23-pi-agent-pi-web-chat-android
relevance: critical
observed_at: 2026-08-23T13:08:41.426Z
---

# 🔴 Observation: Pi Agent + pi-web-chat Android 完整运行成功

在 Android 10 x86_64 模拟器上完整跑通 Pi Agent + pi-web-chat！

最终方案（v3）：
1. 用 Delusions6515/node-android-build 的独立 Node 26.7.0 二进制（arm64 126MB / x64 131MB，NDK r29 构建，非 stripped 版）
2. 二进制放 assets，运行时解压到 filesDir + chmod 755（targetSdk 28 绕 W^X；sideload 可行）
3. 用 node 自身的 extract.cjs 解压 node_modules.tar（gzip 53MB，31842 文件完整）——Kotlin TarGzExtractor 有 PAX header bug 不可靠
4. ProcessBuilder 启动 node pi-web-launch.cjs → ESM pi-web-launcher.mjs → import pi-web-chat

关键修复链：
- nodejs-mobile v18 的 libnode.so 无法运行 pi-coding-agent（需 Node>=22.19，v-flag 正则、undici File）
- pi-tui utils.js 6 个 /v flag 正则需 patch 成 /u（含 RGI_Emoji→兼容对象、差集→lookahead）
- jniLibs 提取 libnode-bin.so 失败（extractNativeLibs=true 也无效，疑 ELF 校验）
- assets 版 node-x64 第一次下载的是坏 build（67MB stripped SIGSEGV），重新下载 131MB 正常
- 解压目标目录需 appDataDir（tar 内路径含 node_modules/ 前缀）

结果：http://127.0.0.1:3141 正常监听，WebView page finished，pi-web-chat 前端加载成功

*Relevance: critical*
*Tags: android pi-agent pi-web-chat node26 success*

---
*Observed: 2026-08-23T13:08:41.426Z*
