---
name: "bilibili-transcribe-pipeline"
description: "B站+Whisper 转写全链路（后台队列/回填/防幻觉/乱码）已验证的坑"
version: 1
created: "2026-09-27"
updated: "2026-09-27"
---
## When to Use
在 content-creator-workspace 实现或修复视频转写、素材内容回填、Whisper 输出乱码/繁体/重复幻觉时。

## Procedure
1. 转写点立即返回（0秒）入后台串行队列（GPU 一次跑一个），完成后写 SQLite transcriptions 表，二次打开查库秒回。
2. 流水线：字幕优先→无字幕才下载音频（Node fetch 300s，过期自动重取 playurl）→ffmpeg m4s 转 wav（whisper 无法直接解码 .m4s）→本地 Whisper GPU 推理（1800s）→杀超时子进程后 catch 返结构化 error 而非 500。
3. 防乱码：py 端 sys.stdout.reconfigure(encoding='utf-8') + spawn 注入 PYTHONUTF8=1/PYTHONIOENCODING=utf-8 + encoding:'utf-8'。
4. 防繁体/重复幻觉：language=zh + initial_prompt 简体偏置 + temperature 回退序列 + condition_on_previous_text=False（实证重复幻觉 79→2）。
5. 读取时 getVideoContent/listMaterials LEFT JOIN transcriptions 取最新文本，转写完成后 backfill 回填 project_materials.content。

## Pitfalls
- faster-whisper 在 HF 下载模型卡 401，模型须预下载放 backend/models/whisper/ 并复制进项目目录。
- Windows Python stdout 默认 GBK 而 Node 按 UTF-8 解码 → 中文全成 \ufffd，必须双层修复。
- 媒体 URL（playurl 的 audio/video）会过期，不可缓存，每次重拉。
- 素材保存早于转写完成会导致 content 不回填（曾 161 字推断文本没换成 2878 字转写）。

## Verification
1. 转写文本 replace(/\uFFFD/g,'') 为空、繁体字数为 0、字数与音视频时长匹配。
2. 二次打开素材秒回且显示完整转写内容。