---
type: source
title: 字幕张冠李戴真根因：老 player/v2 端点按 cid 单键解析（非B站偶发）
status: insight
category: bugfix
created: 2026-09-29
updated: 2026-09-29
slug: bilibili-old-player-endpoint-cid-only-resolution
---

# 字幕张冠李戴真根因：老 player/v2 端点按 cid 单键解析（非B站偶发）

## 修正前结论

此前 [[subtitle-wrong-video-and-force-whisper]] 判定"B站接口偶发返回别视频字幕"——**错误**。用户质疑"B站不可能偶发"是对的。

## 实测铁证（2026-09-29，同一视频同一时刻）

BV19v411M7Rs（何同学，aid=251187473, cid=426711793, dur=468s）：

| 端点 | 返回的 ai-zh 轨道 |
|---|---|
| 老 `x/player/v2?bvid&cid`（代码原用） | id=161023795861，**52行/131.88s，"江南水乡种水稻呀"** ← 别的视频！|
| 新 `x/player/wbi/v2?aid&cid` | id=106272886275，203行/452.68s，"过去的两个月里" ← 正确 |
| TV 签名 `x/player/v2` | **永远 0 轨道**（从未可用，白跑一次） |

**根因**：老端点忽略 aid、按 cid 单键解析——cid 在全站并非唯一（老视频段撞号），撞到谁返回谁的 AI 字幕。"喵钻解说/镜头膜/短剧/水稻"四份错误字幕全是这么撞出来的，**确定性 bug 而非偶发**。WBI 新端点做 aid+cid 成对校验。

## 修复（全部落地验证）

1. **fetchSubtitle 重写为 wbi/v2 单路径**（`fetchPlayerV2Wbi(aid,cid)` + `getVideoAid` 兜底；删 TV 路径与老端点路径）——根治
2. 三层防御保留：入口校验 verifySubtitleBelonging、读缓存校验（拒→throw→fresh 自愈）、force_whisper
3. **缓存门条件死锁修复**：原 "source_text 非空即 cache" 导致字幕空时永不重取 → 新逻辑：字幕缺失+非 whisper+cached_at 超10分钟 → 重取（顺带适配 B站 AI 字幕异步生成）
4. 附带发现并修：主获取路径漏传 validate（上次修复的遗漏）、非空断言、时间轴上限放宽到 2x+60（yt-dlp 报告 AI 字幕时间戳 35x 暴涨案例，防误杀）

## 验证

何同学自愈 fresh → 2532字正确字幕入库；二次 cache ✅；崩老头 4009字无回归 ✅；单测5/5（含时间戳暴涨拒、1.3x 轻微超长过）。

## 方法论

- **用户对"偶发"的直觉质疑推动了真根因定位**——当"偶发"无法复现时，对比不同调用路径的输入输出（本例：老端点 vs 新端点同参数对照）是决定性实验
- 对照实验设计要点：同一时刻、同一资源、只变一个变量（端点），逐层 dump（轨道 id/行数/时间轴/首行内容）
- 修复后仍保留防御层：端点将来再变，污染也进不了库

相关：[[subtitle-wrong-video-and-force-whisper]]

*Category: bugfix*

---
*Captured: 2026-09-29*

## Related

_Add links to related pages._
