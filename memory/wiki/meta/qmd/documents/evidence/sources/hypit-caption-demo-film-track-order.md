---
type: source
title: Hypit 词锚字幕 demo 成功：film Track 先声明在顶层（层叠方向坑）
status: insight
category: bugfix
created: 2026-09-30
updated: 2026-09-30
slug: hypit-caption-demo-film-track-order
---

# Hypit 词锚字幕 demo 成功：film Track 先声明在顶层（层叠方向坑）

## 成果（2026-09-30，全本地零费用）

`Desktop/hypit-caption-demo.mp4`（15s 720×1280 带语音+中文字幕）：
- 本地 WhisperX 词对齐（plan 明确 `whisperx.local bound in the Profile · local, no Provider charge`——HypiHub 彻底绕开）
- caption-fine karaoke 逐词高亮实时跟读（第6秒"是"字 active 黄色 #FFD54A）
- 9 请求全部本地，build 2分54秒

## 关键坑：film Track 层叠方向

**先声明的 Track 在顶层**。初版按"后声明在上"假设把 captions 放最后 → 字幕被 bg 完全盖住（抽帧只见画面）。调整 `<film:Track>` 把 captions 放**第一位**后正常。plan/类型检查抓不到这种纯视觉层叠问题——**必须抽帧目检**。

## 接线模板（caption.svml 核心段，实测可用）

```svml
<asset:Audio id="voice" src="./voice.wav"/> + pipeline:Normalize video="none" audio="default" span-authority="audio"
<script id="story"><passage><HOST>中文口播文本</HOST></passage></script>  ← HOST 不闭合！闭合会 SCRIPT_SEGMENT_CLOSE
<whisperx:SemanticTake narrative={story} segment={story.segment.passage} media={voice-media.media} language="zh"/>
<time:Timeline><time:Take source={speech-take.take}/></time:Timeline>
<caption-fine:Style id="primary" recipe={look.caption.primary} font={caption-font}/>   ← recipe 放 look.svs: caption.primary {...}
<caption-fine:Track id="captions" document={story.caption} timeline={program.timeline}><caption-fine:Use style={primary}/></caption-fine:Track>
<fonts:Stack family="inter"><fonts:Fallback family="noto-sans-sc"/></fonts:Stack>   ← 中文需装 @fontsource-variable/noto-sans-sc
film Track 顺序: captions → bg → sound（先=顶）
```

- svrun `<target output="X.video">` 必须等于 render:Video 的 `{id}.video`
- `hypit get --to` 带扩展名才是文件；无扩展名建不出目录（当成文件名）
- 字幕 recipe（caption.primary）在 look.svs，stack-order 70 / karaoke current / active-fill 黄

相关：[[hypit-local-whisperx-byok-setup]] [[hypit-integration-first-light]]

*Category: bugfix*

---
*Captured: 2026-09-30*

## Related

_Add links to related pages._
