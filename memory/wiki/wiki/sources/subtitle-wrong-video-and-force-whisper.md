---
type: source
title: 字幕张冠李戴事故：归属校验+强制转写双修复
status: insight
category: bugfix
created: 2026-09-29
updated: 2026-09-29
slug: subtitle-wrong-video-and-force-whisper
---

# 字幕张冠李戴事故：归属校验+强制转写双修复

## 事故（2026-09-29 用户发现）

何同学视频（BV19v411M7Rs）的字幕是游戏解说（"喵钻罐头"2577字），崩老头视频（BV1d87L6UEws）的字幕是苹果镜头膜（1327字）；点"转写"后换成短剧台词 2.6 万字（"爹娘/顾南晟/我的好夫人"）。

## 根因（三层）

1. **B站接口偶发返回别视频字幕**（TV 签名路径当时返回了错误数据；实测后来又恢复正常——同 bvid 两次 fetch 结果不同的实锤：崩老头 video_cache 字幕1327字错、转写时重新 fetch 4009 字对）
2. **零归属校验**：错误字幕直接入库长期沿用
3. **转写 Step 0 "有字幕秒回"**：用户点转写想用真实语音纠错，它却再返回一份字幕（且这份错误字幕被 markTranscriptionDone 当转写存表——2.6万短剧就是这么来的），**根本没跑 Whisper**

## 修复（四项全闭环，E2E 验证）

1. **force_whisper**：POST /bilibili/transcribe 加参数 → 跳过 Step 0 字幕秒回；缓存 source=subtitle 时强制重跑。前端两按钮（发现页"语音转写"、素材页"用语音转写覆盖"）都传 true。stt.ts 用 `if (!opts.forceWhisper) try {...} catch` 单行包裹避免缩进 churn
2. **verifySubtitleBelonging(text, lastTo, {duration,title})**：时间轴校验（超出视频或覆盖<40%拒）+ 标题特征子串命中（【】系列名+英文词+标点切片的3-6字子串，剔除"评论/关注/点赞"等高频口播词，零命中拒）。**原则：宁可错杀字幕（Whisper兜底），绝不放过污染**。单测6/6：两个真实污染样本全拦、正确字幕全过
3. **transcriptions 加 source 列**（whisper|subtitle，ALTER in getDb try/catch）；字幕秒回结果**不再 backfill 素材**；markTranscriptionDone 标 source
4. **数据清理**：删假转写、清错误字幕、对题但属字幕秒回的标 source=subtitle

## E2E 证据

force → pre:none → enqueue → [STT] Converted to WAV 14.9MB → done:2379字 source=whisper 内容"我做了一张桌子/苹果发布会" looks_hexue=true looks_shortdrama=false。Whisper 识别错字（"球析发布会"）反而是真实语音的指纹。

## 教训

- **"秒回"优化改变了用户意图语义**："转写"按钮的承诺是真实语音，任何路径偷换（返回字幕）都是 bug
- 外部 API 的返回内容要**假设可能张冠李戴**——归属校验比信任更便宜（错杀代价=一次转写，放过代价=长期污染）
- 内容级校验（标题子串+时间轴）在无元数据时够用，关键是**宁严勿宽**的方向选择

相关：[[imitate-style-content-separation]] [[next16-turbopack-bracket-api-route-bug]]

*Category: bugfix*

---
*Captured: 2026-09-29*

## Related

_Add links to related pages._
