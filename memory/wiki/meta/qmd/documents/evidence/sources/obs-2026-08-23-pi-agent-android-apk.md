---
type: source
title: "Observation: Pi Agent Android APK 构建方案"
tags:
  - android
  - apk
  - build
  - nodejs
  - termux
  - pi-agent
status: observation
created: 2026-08-23
updated: 2026-08-23
slug: obs-2026-08-23-pi-agent-android-apk
relevance: critical
observed_at: 2026-08-23T03:29:50.807Z
---

# 🔴 Observation: Pi Agent Android APK 构建方案

成功将 Pi Agent (Node.js + WebView) 打包为独立 Android APK。关键发现：
1. Delusions6515/node-android-build 提供半静态编译的 Android ARM64 Node.js 二进制（~126MB），不依赖 Termux 环境
2. nodejs-mobile 只提供 libnode.so 共享库，不能作为独立进程运行
3. 必须修改 NodeJsService 在运行时解压 node_modules.tar.gz（53MB），否则 APK 太大
4. APK 最终 217MB，ZIP 压缩后 142MB，QQ 单文件上传极限约 150MB
5. 构建环境需要 JDK 17 + Android SDK (Platform 34 + Build Tools 34) + Gradle 8.2

*Relevance: critical*
*Tags: android apk build nodejs termux pi-agent*

---
*Observed: 2026-08-23T03:29:50.807Z*
