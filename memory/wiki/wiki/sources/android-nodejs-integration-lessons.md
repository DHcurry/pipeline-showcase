---
type: source
title: Android Node.js 集成关键教训
status: insight
category: android
created: 2026-08-23
updated: 2026-08-23
slug: android-nodejs-integration-lessons
---

# Android Node.js 集成关键教训

## 核心教训

1. **Node.js 只能在进程中启动一次**
   - `node::Start()` 是一个全局初始化函数
   - 调用两次会导致 SIGTRAP 崩溃
   - 解决方案：启动一个长期运行的脚本（如 HTTP 服务器），不要多次启动

2. **环境变量必须通过 JNI 设置**
   - `System.setProperty()` 只设置 Java 系统属性
   - Node.js 读取的是 C 环境变量
   - 必须在 native-lib.cpp 中调用 `setenv()`

3. **Android 会修改 assets 文件名**
   - `.tar.gz` 可能被存储为 `.tar`
   - 需要在代码中尝试多个可能的文件名

4. **Android 15 (SDK 36) 需要 16KB 页面对齐**
   - nodejs-mobile v18.20.4 不支持
   - 需要用 NDK r28+ 重新编译
   - 或者使用 Android 10-14 的模拟器测试

5. **WASM 调试断点问题**
   - 某些 Node.js 模块（如 pi-web-chat）使用 WASM
   - 在 Android 上可能触发 Runtime_WasmDebugBreak 崩溃
   - 需要使用纯 JS 实现的替代方案

*Category: android*

---
*Captured: 2026-08-23*

## Related

_Add links to related pages._
