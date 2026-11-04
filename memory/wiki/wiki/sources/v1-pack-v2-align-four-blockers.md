---
type: source
title: V1备料+V2拍后对齐落地：whisperx 三坑与分镜/对齐双链路
status: insight
category: bugfix
created: 2026-09-30
updated: 2026-09-30
slug: v1-pack-v2-align-four-blockers
---

# V1备料+V2拍后对齐落地：whisperx 三坑与分镜/对齐双链路

## 交付（2026-09-30，content-creator-workspace）

**V1 备料**：创作页「⚡备料」→ `POST /api/pack/enqueue` → mimo 分镜分析（storyboard.ts，7段含 visual_type/keywords/motion/emphasis）→ Pexels 拉取（key 读 video-asset-hub skill config.json）→ `runtime/deliverables/p{pid}_{ts}/01_分镜表.md + 02_broll/`（实测16素材）。分镜卡片区在编辑器下方：类型徽标/关键词/缩略图/打开素材包/分镜表。

**V2 拍后**：「⏱拍后处理」上传实拍 → `POST /api/align/upload`(multipart) → ffmpeg规范化 → 本地whisperx → LLM句段匹配+NG → SRT+拍后分镜表。实测输出：`[4.7-13.5s] 按照妇女报的说法…` + NG「转写错字'所才'作'索财'，**非口误**」（模型能区分转写错字vs口误）+ 标准SRT剪映可导。

## whisperx 直连的三个坑（全修复）

1. **格式**：服务只收标准 PCM WAV——`hypit media cut` 产 EXTENSIBLE/24bit/44.1k 会被拒 "not a valid WAV" → align-job 先 `ffmpeg -ar 16000 -ac 1 -c:a pcm_s16le` 规范化
2. **白名单** `HYPIT_WHISPERX_INPUT_ROOTS` **默认=OS temp 目录**（config.py `tempfile.gettempdir()`，CLI 不注入）——demo 能用正因在 AppData\Local\Temp 下；uploads/E盘全拒 → 规范化输出写 `os.tmpdir()/ccw-align/` 用完删
3. **响应形态**：HTTP 返回 `{segments:[{words:[{text,start,end,score}]}]}`（**非** transcript.json 的 start_seconds 命名、非 passages）→ whisperxAlign 做字段归一（start ?? start_seconds），否则 undefined.toFixed 崩在 match 阶段

## 其他要点

- 直连服务（127.0.0.1:8765 POST /transcribe {audio_path,language}）而非 hypit CLI：CLI 对长音频 fetch 超时断连（796s 实测），直连自控20分钟
- 服务接口仅接受 audio_path（文件路径）+ language，Content-Type application/json
- 句段匹配（align-job matchSegments）用 LLM：原句段 vs 带时间码伪句聚类（静默>0.6s切簇）→ start/end+NG
- Pexels key 来源：`~/.pi/agent/skills/video-asset-hub/config.json`（fallback env PEXELS_API_KEY）

相关：[[hypit-local-whisperx-byok-setup]] [[hypit-caption-demo-film-track-order]]

*Category: bugfix*

---
*Captured: 2026-09-30*

## Related

_Add links to related pages._
