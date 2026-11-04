---
name: "bilibili-full-pipeline-pitfalls"
description: "B站搜索/登录/字幕/播放地址全链路已验证的坑与解法"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
实现或修复 B 站搜索、扫码登录、字幕获取、视频下载/playurl 相关功能时。

## Procedure
1. 搜索必须自实现 WBI 签名（bilibili-api 等 npm 包不可用，直连返回 412）；命中范围=标题+标签+简介，hit_columns 透传前端做高亮，匹配是 B 站服务端算法。
2. 扫码登录：官方图片 API 404 → 用 npm qrcode 本地生成 base64；轮询按 code 判断（0 成功/86101 未扫/86090 已扫/86038 过期）兼容旧 status；SESSDATA 提取支持三形状（直字段/cookies 字符串/set-cookie 头），无凭证不报成功。
3. 字幕不可全信（用户纠正）：可能与口播不同步/滚动重复/覆盖不全/乱码/UP主挂稿件文案而非口播 → assessSubtitleQuality 质量评分（字数/时长比3-6字/秒、乱码比例、GBK误解码特征词 锅斤拷/锘逗/烫烫烫/�——GBK乱码是合法汉字靠字符集抓不住），<60分自动转 Whisper 覆盖且转写完成无条件优先于字幕；单测教训：严重项扣分要够狠使分数低于阈值，边界值(恰好60)不能卡阈值。
4. 字幕：匿名返回空 → TV 端 appkey 签名优先（appkey 4409e2ce8ffd12b8 / appsec 59b43e04ad6965f34319062b478f83dd）→ Web API(SESSDATA) 回退 → 仍无字幕则用标题+简介+标签推断并标 source_mode: inferred。
5. .m4s 需先 ffmpeg 转 wav，ffmpeg 路径用 which/where 解析不硬编码。
6. CDN 直连 EAI_AGAIN 走 media-proxy 兜底；playurl 的 audio/video URL 会过期不可缓存（只缓存元数据+source_text，每次重拉 playurl，持久化 sources 结构 + fetchFreshAudioUrl 兜底）；下载失败透传 error 给前端而非静默返空，可自动重取新 playurl 重试。

## Pitfalls
- npm bilibili API 包不可用，必须自行 WBI 签名。
- playurl URL 过期，缓存它会导致后续播放失败。
- 无登录态字幕返回空，不报成功。

## Verification
1. 搜索返回带 hit_columns 的结果；扫码登录能拿到 SESSDATA；字幕或 inferred 兜底正常返回；下载失败时前端收到明确错误。