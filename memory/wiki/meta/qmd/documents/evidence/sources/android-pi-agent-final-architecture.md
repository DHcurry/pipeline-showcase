---
type: source
title: Android 运行 Pi Agent 的最终架构
status: insight
category: android
created: 2026-08-23
updated: 2026-08-23
slug: android-pi-agent-final-architecture
---

# Android 运行 Pi Agent 的最终架构

## 最终可行的架构

**独立 Node 26 二进制（assets）+ targetSdk 28 + node 自身解压 + ProcessBuilder**

```
APK
├── assets/node/node-arm64|node-x64  (126MB/131MB, NDK r29)
├── assets/node_modules.tar          (53MB gzip, 31842 文件)
├── assets/nodejs-project/
│   ├── extract.cjs                  (tar+gz 解压器, 支持 GNU L/PAX x)
│   ├── pi-web-launch.cjs            (CJS 入口)
│   └── pi-web-launcher.mjs          (ESM, 配置目录 + import pi-web-chat)
└── 运行时:
    1. 解压 node 二进制 → filesDir/node, chmod 755
    2. node extract.cjs node_modules.tar → appDataDir
    3. node pi-web-launch.cjs (ProcessBuilder)
    4. WebView → http://127.0.0.1:3141
```

## 关键教训
1. **pi-coding-agent 0.74+ 需 Node>=20.6，0.84 需 >=22.19**——nodejs-mobile v18 完全不可行
2. **v-flag 正则** (/xxx/v) 是 Node 20+ 特性，pi-tui 用 6 处，需 patch 成 /u 或兼容
3. **jniLibs .so 提取**在 Android 上对非标准 ELF 可能失败（extractNativeLibs=true 也无效），assets 解压 + targetSdk 28 最稳
4. **Kotlin 自写 tar 解压器不可靠**（PAX/GNU long name 处理复杂），用 node 自身 zlib 最稳
5. **Delusions6515/node-android-build** 的 node 二进制：非 stripped 版（131MB）正常，stripped 版（67MB）SIGSEGV——选未 strip 的

*Category: android*

---
*Captured: 2026-08-23*

## Related

_Add links to related pages._
