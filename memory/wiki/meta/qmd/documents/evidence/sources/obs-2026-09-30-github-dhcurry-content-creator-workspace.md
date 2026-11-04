---
type: source
title: "Observation: GitHub迁移完成：DHcurry/content-creator-workspace（密钥零泄漏）"
tags:
  - GitHub
  - 迁移
  - memory
  - 私有仓
  - MIGRATION.md
status: observation
created: 2026-09-30
updated: 2026-09-30
slug: obs-2026-09-30-github-dhcurry-content-creator-workspace
relevance: critical
observed_at: 2026-09-30T15:20:31.077Z
source_context: 项目+记忆+模型链路迁移GitHub
---

# 🔴 Observation: GitHub迁移完成：DHcurry/content-creator-workspace（密钥零泄漏）

GitHub迁移完成（2026-09-30）：私有仓 DHcurry/content-creator-workspace（main=85bb190，375文件）。入库：全源码+memory/wiki(255文件)+memory/pi-hermes-memory(MEMORY/USER/failures+skills+sessions.db用sqlite backup干净拷贝)+清洗后data.db(7项目/13转写/4风格档案,已DELETE bilibili_cookies)+MIGRATION.md。排除（.gitignore)：auth.json/llm_settings/models.json(B站cookie与mimo key等密钥)、backend/models 211M Whisper权重、deliverables 270M/footage_cache/uploads/logs、node_modules/.next。凭证链路：Windows凭证管理器存有DHcurry的github token(credential fill可用,不落盘)、git项目级代理127.0.0.1:7897(直连被墙,CONNECT 200验证)、REST API创建私有仓201→push成功。新机器恢复=克隆后照MIGRATION.md：npm i→手动放密钥文件→HF镜像(HF_ENDPOINT=hf-mirror.com)拉whisper+hypit programs→capture用npmmirror(base-url)→记忆两目录拷回~/.llm-wiki与~/.pi/agent。注意git ls-tree的grep ^path计数在Windows会假少(用git ls-files权威)。

*Relevance: critical*
*Context: 项目+记忆+模型链路迁移GitHub*
*Tags: GitHub 迁移 memory 私有仓 MIGRATION.md*

---
*Observed: 2026-09-30T15:20:31.077Z*
