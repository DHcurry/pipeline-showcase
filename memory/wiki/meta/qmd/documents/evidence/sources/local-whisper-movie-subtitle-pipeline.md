---
type: source
title: 本地 Whisper 电影字幕管线：cublas PATH 注入与16倍实时基线
status: insight
category: local-ml
created: 2026-10-10
updated: 2026-10-10
slug: local-whisper-movie-subtitle-pipeline
---

# 本地 Whisper 电影字幕管线：cublas PATH 注入与16倍实时基线

Windows 无 CUDA Toolkit 机器上跑 faster-whisper（ctranslate2）GPU 转写的已验证方案：

1. **cublas64_12.dll 缺失的解法不是装 CUDA Toolkit**，而是把 `torch/lib` 目录注入 `os.environ["PATH"]`（torch cu121 wheel 自带 cublas64_12/cudnn64_9/cusparse64_12 全套），必须在 import ctranslate2 之前生效（[[daily-movie-download-pipeline]] 的 subtitle.py ensure_cuda_dlls()）。
2. `model.transcribe()` 返回 `(segments_generator, info)` 元组；语言探测要在解包后的 `info.language`（第一遍 beam_size=1 探语言→第二遍固定 language 全量转，防整片语言漂移）。
3. 性能基线：GTX1650 4GB + small + int8_float16 = **约16倍实时**（101分钟电影 373s），显存无压力；这比常见预期快得多，small 对对白质量已够。
4. 防幻觉三件套沿用 [[bilibili-old-player-endpoint-cid-only-resolution]] 同源经验：condition_on_previous_text=False + temperature 回退序列 + 中文 initial_prompt 简体偏置；VAD(vad_filter) 跳过静音段。
5. 自动化要点：跳过 qBittorrent progress<1 的 content_path（防转写半截文件被台账标记完成）、mtime 5分钟内=正在写入、跨进程锁文件防 cron 双开 GPU、srt 写视频同目录同名供播放器自动加载。

*Category: local-ml*

---
*Captured: 2026-10-10*

## Related

_Add links to related pages._
