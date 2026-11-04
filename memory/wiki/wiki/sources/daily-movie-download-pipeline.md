---
type: source
title: 教父.com 磁力下载管线：无 tracker 磁力必须附加 tracker + 启动验证
status: insight
category: bugfix
created: 2026-10-10
updated: 2026-10-10
slug: daily-movie-download-pipeline
---

# 教父.com 磁力下载管线：无 tracker 磁力必须附加 tracker + 启动验证

从中文资源站（教父.com，xn--wcv59z.com，整站登录墙+PoW 验证，注册关闭）自动挑片下载的已验证模式：

1. 挑片 URL：`/mv?sort=rand&res=磁力&quality=1080P`（参数名 sort/quality/res/status/genre/year 由前端 list.js 用 URLSearchParams 拼接）；详情页磁力直接在 `table.bit_list tbody tr` 的 `a[href^=magnet:]` 里，同行 td 含大小/做种/发布时间。
2. **站点磁力只有 xt/dn，不带任何 tracker** → 纯 DHT 冷启动在无头服务器上极易卡死；必须给 magnet 追加 7 个公共 tracker（opentrackr/demonii/torrent.eu.org/exodus 等）。
3. **站点做种数会虚标**：写入后必须轮询验证（300s 内 `total_size>0` = 拿到元数据 = 真连上 peers）。卡在 `metaDL` 且 peers=0 的是死磁力 → 自动删除、回滚台账、换片重试（最多 3 轮）。
4. 会话：Playwright storage_state 存 state.json，检测到"未登录"/login 跳转即用 site.env 凭据自动重登；PoW 浏览器验证无头模式约 5 秒自动过。
5. 去重双台账：history.json（infohash+详情URL）∪ qBittorrent 现有 hash 集合。

失败案例：`A Christmas Switch`（做种0）与 `Built to Kill`（做种1 虚标）均卡 metaDL 超时被自动剔除；`纳粹僵尸`（做种20）15 秒拿到元数据。相关：[[qbittorrent-webui-ini-and-exit-pitfalls]]

*Category: bugfix*

---
*Captured: 2026-10-10*

## Related

_Add links to related pages._
