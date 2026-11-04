---
name: "content-creator-workspace-architecture"
description: "content-creator-workspace 的目标架构、页面结构与 AI 创作流程硬要求"
version: 1
created: "2026-09-27"
updated: "2026-09-28"
---
## When to Use
在 content-creator-workspace 中新增/修改板块、页面或 AI 功能时。

## Procedure
1. 以 Pi Agent 为骨架的口播文案创作系统：session=项目（AgentSession 目录一项目一对应）；内容发现=项目内素材收集，素材（视频元数据+转写）进项目知识库；素材库=拆解原视频创作思路/节奏/背景知识；创作=以素材为上下文 AI 协助产出新文案；所有新板块必须预留通用可扩展的 AI 接入能力（AI 功能可精简但接入能力必须保留）。
2. 交互硬要求：流程驱动（按钮触发步骤+可编辑），非对话/聊天窗口；中文、编辑器为主角（taste skill：min-h-360px 保底、辅助内容可折叠）；不要功能重复的多入口界面，须整合进项目页。
3. AI 创作流程：①素材集中分析（勾选→批量分析→逐条 AI 拆解存库→生成真实可视化思维导图，非文本大纲）；②唯一交互框=中央编辑器，所有 AI 操作（模仿生成/节奏优化/AI分析当前稿/局部改写/AI优化）作用于编辑器内容，不允许独立“主题”输入框与编辑器并存的双输入源；思维导图用 AI 返回 JSON 喂 jsMind 0.9.1（engine:"canvas"）渲染，不手搓 SVG。
4. 内容发现搜索：WBI 签名接口，排序（oralrank/综合/click/pubdate/dm/stow/scores）+时长档(0-4)全部上页面；找相似走 archive/related 接口；口播分 oral_score=本地规则打分（基准55：时长45-240s+14、点赞率≥2%+5、收藏率≥1%+5、弹幕率≥0.3%或评论≥30+4、简介完整+3、内容关键词+4、结构词+3；时长异常/无关键词-8；85+/75+/65+ 分档标签），非 AI。
5. 前端结构：主页=项目列表（projects 表，session_dir 一项目一目录）；/projects/[id] 三页签=素材库（MaterialsTab+MaterialPreviewModal）/内容发现（DiscoverTab 内嵌）/创作（CreateTab 两步式）；导航仅“项目”+“模型”（settings 页 Pi SDK 配置）。analysis/studio 页已删除并重定向。创作页 workflow 调用 6 处全部直连 127.0.0.1:8001。
6. 技术栈/数据：前端 Next.js 16+React19+Tailwind(:3000)，后端 backend/unified 纯 TS Hono 单进程(:8001，tsx 直跑，npm start 需先 build)；零 Python 依赖（whisper_transcribe.py 除外）。SQLite better-sqlite3(runtime/data.db)：projects/project_materials/transcriptions/bilibili_cookies/video_cache/settings。AI 唯一入口 AIService(services/ai.ts)→ModelRuntime.completeSimple（settings 同步 auth.json+models.json，isConfigured 要求 enabled=true），未暴露 response_format，JSON 靠 extractJSON+repairTruncatedJson；只留非流式 analyze/generate/imitate/optimize/feedback/partial_edit 端点。
7. 调试约定：长耗时 LLM 测试用 Monitor 后台跑+逐例落盘 JSONL（缓冲无法回读）；临时脚本 e2e-*.mjs 放 backend/unified/ 且测完清理；改代码必须重启对应 dev 进程；tsc --noEmit + 端到端实测才算修完。
8. 反AI味自检清单：删空洞套话（“在当今时代”“随着…的发展”）；禁机械排比三连；长短句交错；口语化、有具体数字与生活化比喻。

## Pitfalls
- 不允许对话驱动界面或双输入源编辑器。
- 思维导图不手搓 SVG，必须走成熟库渲染。

## Verification
1. 新板块保留通用 AI 接入口；编辑器仍是唯一输入源；页面结构与导航一致。