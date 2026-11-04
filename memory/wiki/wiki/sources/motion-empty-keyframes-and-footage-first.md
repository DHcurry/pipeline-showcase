---
type: source
title: 动效空帧根因（LLM引用animation不写@keyframes）与参考视频切片优先
status: insight
category: bugfix
created: 2026-09-30
updated: 2026-09-30
slug: motion-empty-keyframes-and-footage-first
---

# 动效空帧根因（LLM引用animation不写@keyframes）与参考视频切片优先

## 问题1：动效 mp4 空帧（用户实测 1.4KB）

**根因铁证**：生成的 HTML 引用了 8-16 个动画名（r1/r2/roll/ruleIn…）但 **@keyframes 定义 0 个**——LLM 写 `animation:` 却整个忘定义 → 元素初始 `opacity:0` 永远透明 → 纯色空帧（定义齐全的那条正常，证明非渲染问题）。

**三层修复（motion.ts）**：
1. prompt 下发**8名动画库**（fadeIn/rise/scaleIn/pulse/roll/drawX/slideL/slideL+slideR）+白名单"只准用库内名字"+自检清单
2. `validateMotionHTML`：animation 引用 ⊆ @keyframes 定义
3. `repairMotionHTML`：库内名缺定义→按行提取注入；自造名→正则替换为 fadeIn——保证有内容

**验证**：修复后 mp4 从 1.4KB → 231/243KB，抽帧"87%观众在前三秒就划走"完整渲染。

## 问题2：Pexels 关联性差 → 参考视频切片优先

新 footage.ts：`LLM 匹配分镜段×素材库 → 关键词在转写文本的位置比例×时长估算时间点 → ffmpeg -c copy 切15s（runtime/footage_cache/ 下载缓存）`。pack-job Phase2a/2b：素材库切片主源（预算8）→ Pexels 兜底（预算8）。实测 `05_mat6.mp4` 12.3MB 切片出现。

## 顺手根除：pack/align 的 rewrite 瞬态

用户点备料撞到 `/api/pack/:id` 走 rewrite + 后端重启窗口 → 纯文本 Internal Server Error（**client-log 全局钩子首次实战捕获**——日志系统起作用了）。动态 ID 无法建静态 route → CreateTab 所有 pack/align 调用**直连 API_BASE**（与 MaterialsTab 同模式），0 残留。

## 教训

- LLM 长输出的"引用与定义不一致"必须**机器校验**（prompt 约束只是概率防线）；修复策略=库内注入+未知替换降级（保内容优先于完美）
- 抽帧验证用**新文件名**（read 工具对同路径图有缓存——曾连续三轮读到旧图误判）
- capture 的 screenshot 不可信、record+ffmpeg 抽帧才可信（前轮已证）

相关：[[obs-2026-09-30-html-llm-html-hypit]] [[v1-pack-v2-align-four-blockers]]

*Category: bugfix*

---
*Captured: 2026-09-30*

## Related

_Add links to related pages._
