---
type: source
title: "Observation: HTML动效管线闭环：LLM动态HTML→hypit录制→分镜卡展示"
tags:
  - 动效
  - motion
  - hypit
  - capture
  - HTML渲染
  - 分镜卡
status: observation
created: 2026-09-30
updated: 2026-09-30
slug: obs-2026-09-30-html-llm-html-hypit
relevance: high
observed_at: 2026-09-30T09:28:36.389Z
source_context: 方案一：hypit 动态动效管线实施
---

# ⭐ Observation: HTML动效管线闭环：LLM动态HTML→hypit录制→分镜卡展示

HTML动效管线闭环（2026-09-30晚）：分镜段(text_card/chart/motion且无真实素材) → services/motion.ts LLM生成4秒竖屏HTML动画(数字滚动/金句卡/关键词弹出,内容取自段落文案,非固定模板) → hypit capture run 录制 → 03_motion/xx.mp4 挂进seg.files → 前端mp4首帧缩略(琥珀边框+▶)+点击全屏播放弹层。E2E: 4文件、6/7段有素材、分镜表就位；抽帧实证"87%观众在前三秒就划走"数字卡来自段落文案。四个坑固化：①Puppeteer新版无waitForTimeout→setTimeout；②Chrome153 install-browser解压丢exe→python zipfile直解修复(npmmirror镜像秒下)；③--browser指向用户Edge→单例跨进程转发录到用户正在看的标签页(screenshot与page.url矛盾的灵异现象)→专用Chrome+每渲染前清userDataDir(ccw-motion-profile防会话恢复)；④capture的screenshot({path})截错目标→只信record产物,验证用ffmpeg抽帧。备料motion phase上限4段,files回写storyboard_json供前端展示。

*Relevance: high*
*Context: 方案一：hypit 动态动效管线实施*
*Tags: 动效 motion hypit capture HTML渲染 分镜卡*

---
*Observed: 2026-09-30T09:28:36.389Z*
