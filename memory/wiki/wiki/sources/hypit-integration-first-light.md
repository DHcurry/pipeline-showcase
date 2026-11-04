---
type: source
title: Hypit 集成首战：零凭证全链路出片 + 词锚语法与接入路径
status: insight
category: bugfix
created: 2026-09-30
updated: 2026-09-30
slug: hypit-integration-first-light
---

# Hypit 集成首战：零凭证全链路出片 + 词锚语法与接入路径

## 结果（2026-09-30）

本机原本**未装 hypit**（全面搜索无果），本次从零装好并**零凭证跑通全链路出片**：
`Desktop/hypit-demo-output.mp4`（10s 竖屏 720×1280 30fps，1分44秒渲染，5请求全 local no Provider charge）。

## 装备与命令链

- Skill: `npx skills add hypit-ai/hypit -g` → `~\.agents\skills\hypit`（symlink 到 Pi/Claude）；CLI: `npx @hypit/hypit`（v0.2.16）
- 工作流：`runtime init` → `runtime up`（自动装 hyperframes 引擎+Chrome Headless Shell）→ `doctor` → **`plan <x>.svrun`（免费语法验证器，错误信息指路）** → `build --follow` → `get --output final.video --to <dir>`（注意 --to 是**目录**）
- 依赖包按需 `hypit packages install`（inter 字体、emoji 字体各一次）

## 关键语法（可复用模板在 /c/Users/16575/AppData/Local/Temp/hypit-demo/）

- 三文件：`.svml`描述工作 / `.svs` recipes / `.svrun` 执行入口（author+target）
- **词锚点**：`<script>` 内 `@{proof}...@{/proof}` 语义范围、`@{claim!}` 语义点、`||`字幕 Cue 交接、`<API|A P I>` 显示/发音双文本——**这正是"口播哪句配特效"的锚定系统**
- 本地素材：`<asset:Video src>` → `pipeline:Normalize(span-authority="video")` → `media-track:Track+Item(during="program")` → **导出路径是 `{main.visual}`**（非 .track）
- `time:Timeline clock end="10s"` 纯时间容器；typo:Track 标题；film:Track→render:Video
- plan 输出即依赖清单：本地5步 vs HypiHub 2步

## 缺口（下一步）

1. **HypiHub 凭证**（`hypit auth login hypihub.default`）：词对齐 whisperx 与 seedance 生成都挂它——词锚字幕 demo 必须注册
2. **标题层未渲染**（渲染日志无报错、字体就绪，疑 film Track 层序或 during窗口）——待精修
3. 素材 deepseek_1.mp4 实为口播工作台屏幕录制（8月存的 video-assets）

## 集成结论（回答"能不能集成到 content-creator-workspace"）

能且互补：分镜卡(阶段1)→Pexels素材(阶段2)→**hypit 渲染(阶段3)**；词锚点是"哪句配特效"的正确抽象。形态=项目后端 spawn hypit CLI（plan/build/get 已验证可脚本化）。本机未装过 hypit 一事也已澄清（用户印象有误）。

相关：[[generate-plain-text-and-system-prompt-json-trap]]

*Category: bugfix*

---
*Captured: 2026-09-30*

## Related

_Add links to related pages._
