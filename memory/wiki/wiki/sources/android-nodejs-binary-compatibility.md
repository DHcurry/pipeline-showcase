---
type: source
title: Android Node.js 二进制兼容性要点
status: insight
category: android
created: 2026-08-23
updated: 2026-08-23
slug: android-nodejs-binary-compatibility
---

# Android Node.js 二进制兼容性要点

## 核心发现

1. **nodejs-mobile** (github.com/nodejs-mobile/nodejs-mobile) 提供 `libnode.so` 共享库，设计用于通过 JNI 加载到 Android 进程中，**不能**作为独立可执行文件运行。

2. **Delusions6515/node-android-build** 提供半静态编译的 Android Node.js 二进制（`--partly-static`），可以作为独立可执行文件运行，不依赖 Termux 环境。这些二进制使用 Android NDK 编译，链接到 `/system/bin/linker64`。

3. **Termux 的 node 包**依赖 Termux 的特殊 bionic libc 补丁，不能在普通 Android 环境中运行。

4. 在 Android 上通过 `ProcessBuilder` 运行 Node.js 子进程是可行的，但需要：
   - 真正的 ARM64 ELF 二进制文件
   - 从 assets 解压到应用数据目录
   - 设置可执行权限
   - 确保 node_modules 也正确解压

## 实用技巧

- 将 node_modules 压缩为 tar.gz (53MB vs 400MB+)，运行时用 `tar -xzf` 或 `toybox tar` 解压
- APK 中 assets 超过 200MB 时构建时间会显著增加
- QQ 单文件上传极限约 150MB，超限需要压缩或分卷

*Category: android*

---
*Captured: 2026-08-23*

## Related

_Add links to related pages._
