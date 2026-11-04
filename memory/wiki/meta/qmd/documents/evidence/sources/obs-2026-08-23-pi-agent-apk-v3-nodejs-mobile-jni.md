---
type: source
title: "Observation: Pi Agent APK v3: nodejs-mobile JNI 方案成功"
tags:
  - android
  - apk
  - nodejs-mobile
  - jni
  - libnode
  - w^x
status: observation
created: 2026-08-23
updated: 2026-08-23
slug: obs-2026-08-23-pi-agent-apk-v3-nodejs-mobile-jni
relevance: critical
observed_at: 2026-08-23T04:04:44.038Z
---

# 🔴 Observation: Pi Agent APK v3: nodejs-mobile JNI 方案成功

成功使用 nodejs-mobile + JNI 方案构建 Pi Agent Android APK。

关键架构变更：
1. 不再使用 ProcessBuilder 运行独立 node 二进制（会被 Android W^X 安全机制阻止）
2. 改用 System.loadLibrary("node") 加载 libnode.so 共享库
3. 通过 JNI native-lib.cpp 调用 node::Start() 启动 Node.js 运行时
4. libnode.so 放在 app/libnode/bin/{abi}/ 目录，通过 jniLibs.srcDirs 配置
5. CMakeLists.txt 需要正确配置 include_directories 和 target_link_libraries

构建环境：
- JDK 17.0.2
- Android SDK Platform 34
- Android NDK 26.1.10909125
- CMake 3.22.1
- nodejs-mobile v18.20.4 (libnode.so 62MB)

APK 最终大小：215MB (ZIP: 115MB)

*Relevance: critical*
*Tags: android apk nodejs-mobile jni libnode w^x*

---
*Observed: 2026-08-23T04:04:44.038Z*
