---
type: source
title: "Observation: UU远程开机诊断：Windows侧WOL全对，疑点在BIOS与校园网辅助设备"
tags:
  - WOL
  - UU远程
  - 网络唤醒
  - HP
  - BIOS
  - 校园网
status: observation
created: 2026-10-10
updated: 2026-10-10
slug: obs-2026-10-10-uu-windows-wol-bios
relevance: high
observed_at: 2026-10-10T05:04:22.269Z
source_context: 诊断 UU远程远程开机失败
---

# ⭐ Observation: UU远程开机诊断：Windows侧WOL全对，疑点在BIOS与校园网辅助设备

2026-10-10 诊断「UU远程无法远程开机」。本机 HP 台式机（主板 8575，AMI BIOS F.29 2023-12），Realtek RTL8168 (VEN_10EC&DEV_8168) 有线网卡驱动 10.43.723.2020。Windows 侧 WOL 全部正常：*WakeOnMagicPacket=1、S5WakeOnLan=1、*WakeOnPattern=1、WolShutdownLinkSpeed=0(10Mbps优先)、powercfg wake_armed 含 Realtek、快速启动/休眠均未启用(hiberfil 不存在)、PnPCapabilities=256。UU远程 v4.27.2 装于 D:\Program Files\Netease\GameViewer，GameViewerService 服务 Running/Auto，HKCU Run 有 GameViewer --auto-run，config auto_run=1。网络环境：有线 IP 172.16.88.21/网关 172.16.88.1，JWT 记录公网出口 59.52.36.233 → 校园网大 NAT。UU官方机制：跨网远程开机必须依赖「同局域网在线辅助设备(UU客户端/Android需开远程开机WOL开关)」或「支持列表路由器(华为X1/部分中兴/TP-LINK)」转发魔术包。疑点：①校园网无支持列表路由器且可能有客户端隔离 → 魔术包到不了；②HP BIOS 需查 Advanced→Device Options→S5 Wake on LAN=Enabled、Power→Hardware Power Management→S5 Maximum Power Savings=Disabled（无法从系统读取）。事件日志：10/10 9:17-9:37 有5次开机4次关机，其中3次关机由 GameViewerServer.exe 发起（UU远程关机功能本身可用）。UAC 提权被用户取消，Get-NetAdapterPowerManagement 全部报 System Error 31（疑权限）。日志 .slog 为加密格式无法 grep。

*Relevance: high*
*Context: 诊断 UU远程远程开机失败*
*Tags: WOL UU远程 网络唤醒 HP BIOS 校园网*

---
*Observed: 2026-10-10T05:04:22.269Z*
