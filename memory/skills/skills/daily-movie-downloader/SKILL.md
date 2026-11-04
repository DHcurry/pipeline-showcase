---
name: "daily-movie-downloader"
description: "教父.com(xn--wcv59z.com) 每日一部电影自动下载：站点登录/挑片/磁力验证/本机 qBittorrent WebUI 入列的完整流程与已验证坑"
version: 5
created: "2026-10-10"
updated: "2026-10-12"
---
## When to Use
用户询问或需要维护"每天下载一部电影"任务时：脚本在 C:\Users\16575\daily-movie\daily_movie.py，定时 Loop #1 每天20:00，或下载失败需要排查时。

## Procedure
1. 中文配音（dub_zh.py，按音轨生成中文配音）：中文字幕(.srt.hardsub)→本地 Piper TTS(zh_CN-huayan-medium, hf-mirror下载, 476句/83秒)→时间轴对齐(超槽自动微调语速)→原声对白段duck到30%保留BGM→ffmpeg封装：中文配音=第1音轨default、日语原声=第2音轨、视频流copy不重压。缓存 dub_cache/ 断点续跑；封装产物 .dubbing.mkv 保留供秒替。用法 --file X / --all。edge-tts 在此网络 403 不可靠勿用。
2. 占位排查套路：python open(r+b)通过但 os.replace 被拒=占用者共享读写不共享删除；用 PowerShell Restart Manager API 点名进程（实证 qBittorrent 做种句柄是常客）；qBittorrent 占用→release_from_qbt(curl版)移除任务保留文件。
3. Windows python 传中文路径：bash 内联 -c/管道编码易炸→写成 utf-8 脚本文件跑；glob 遇路径中 [全6集] 会当字符类返回0→glob.escape 或 os.listdir+startswith。
## Pitfalls
- 站点磁力只有 xt/dn 不带任何 tracker：daily_movie.py 的 augment_magnet() 必须附加公共 tracker，否则纯 DHT 冷启动大概率卡死。
- 站点做种数虚标：加入后必须过 verify_started（300s 内拿到 total_size>0 才算成功）；metaDL 卡死=死磁力，脚本会自动删除换片，不要手动保留。
- 站点整站需登录且注册关闭；无头浏览器 storage_state(state.json) 掉线时用 site.env 自动重登。
- qBittorrent 退出确认对话框"一些文件正在传输中"会挡住一切关闭信号；更新弹窗是模态的会挡菜单点击（已通过 ini 关闭 updateCheck）。

## Verification
1. daily_movie.py 输出末行 {"ok": true, ...}。
2. qBittorrent API 中该种子 state=downloading 且 progress 增长（分类=每日电影、标签=daily-movie）。
3. history.json 新增当日记录且 infohash 唯一。