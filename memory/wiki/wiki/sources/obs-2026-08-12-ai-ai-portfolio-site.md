---
type: source
title: "Observation: AI 作品集网站 ai-portfolio-site 建成"
tags:
  - nextjs
  - threejs
  - portfolio
  - inspiration
  - pi-agent
status: observation
created: 2026-08-12
updated: 2026-08-12
slug: obs-2026-08-12-ai-ai-portfolio-site
relevance: high
observed_at: 2026-08-12T17:19:15.537Z
source_context: 构建 AI 作品集网站（作品展示+灵感引擎），用户用于短视频主题"创造自由AI一切"
---

# ⭐ Observation: AI 作品集网站 ai-portfolio-site 建成

在 C:/Users/16575/ai-portfolio/ai-portfolio-site 建成了 Next.js 15 + TypeScript + Tailwind + Three.js + Framer Motion 的 AI 作品集网站，主题"创造自由·AI 一切"。功能：①作品展示（卡牌式+Three.js 粒子 Hero+详情页+上传）②灵感引擎（双通道：hot 引擎直接调 60s.viki.moe 热搜 API + 启发式创意；pi agent 引擎通过 spawn node dist/cli.js -p 用 stdin 传 prompt 深度生成）。关键踩坑：Windows 下 execFile 传参失败，改用 spawn + stdin 传 prompt 成功；pi CLI 实际路径是 node_modules/@earendil-works/pi-coding-agent/dist/cli.js（不是根 cli.js）；Next 服务端组件不能用 onError 事件。数据存 data/works.json。build 通过，npm run start 本地运行 http://localhost:3000。

*Relevance: high*
*Context: 构建 AI 作品集网站（作品展示+灵感引擎），用户用于短视频主题"创造自由AI一切"*
*Tags: nextjs threejs portfolio inspiration pi-agent*

---
*Observed: 2026-08-12T17:19:15.537Z*
