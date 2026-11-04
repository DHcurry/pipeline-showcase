---
type: source
title: qBittorrent 5.x WebUI ini 键位与 GUI 退出三坑
status: insight
category: devops
created: 2026-10-10
updated: 2026-10-10
slug: qbittorrent-webui-ini-and-exit-pitfalls
---

# qBittorrent 5.x WebUI ini 键位与 GUI 退出三坑

qBittorrent v5.2.3（Windows）无人值守配置要点：

1. **WebUI 配置必须写在 ini 的 `[Preferences]` 段下**（源码 preferences.cpp 路径为 `Preferences/WebUI/...`）：`WebUI\Enabled=true`、`WebUI\Address=127.0.0.1`、`WebUI\Port`、`WebUI\Username`、`WebUI\Password_PBKDF2`。顶层 `[WebUI]` 段会被**静默忽略不报错**——这是最坑的失败模式（服务不监听、日志无错误）。
2. `Password_PBKDF2="@ByteArray(base64(salt16):base64(hash64))"`，PBKDF2-HMAC-SHA512 迭代 100000。
3. 探测 WebUI 存活不能用未认证 `GET /api/v2/app/version`（403 误判为宕机）；401/403 也算在线。
4. **GUI 退出三坑**：WM_CLOSE 在托盘设置下不退；真正拦路的是退出确认对话框"一些文件正在传输中"（`Preferences/General/ExitConfirm` 默认 true），它弹出后一切关闭信号无效，必须点"是(Y)"（相对坐标 55,134）；更新提示弹窗是模态的会挡菜单点击，用 `Advanced\updateCheck=false` 永久关。可靠流程：SW_RESTORE → focus → Alt+F → 点"退出"(窗口相对 70,143) → 确认"是"。
5. 无进行中下载时强杀可接受（fastresume 损失仅触发小规模 recheck）。

相关：[[daily-movie-download-pipeline]]

*Category: devops*

---
*Captured: 2026-10-10*

## Related

_Add links to related pages._
