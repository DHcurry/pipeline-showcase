---
type: source
title: "Observation: 风格档案三通道（蒸馏/导入/upvideos拉取）+12字段统一schema落地"
tags:
  - 风格蒸馏
  - 导入通道
  - style_profiles
  - WBI
status: observation
created: 2026-09-29
updated: 2026-09-29
slug: obs-2026-09-29-upvideos-12-schema
relevance: high
observed_at: 2026-09-29T14:30:53.418Z
source_context: content-creator 风格蒸馏管线 P0+P1 实施
---

# ⭐ Observation: 风格档案三通道（蒸馏/导入/upvideos拉取）+12字段统一schema落地

风格档案三通道落地（2026-09-29晚）：①蒸馏 POST /workflow/distill（多样本→12字段档案）②导入 POST /workflow/import_profile（现成 SKILL.md/yaml→LLM归一→同一schema，sample_count=0标记导入）③统一schema12字段（stormzhang式扩展：persona/capabilities/structure_patterns/openings/closings/checklist + 原有dna/七维/口癖/禁忌）。生成侧零改动（JSON.stringify整体注入自动携带新字段）。端到端：刘润SKILL.md导入→structure_patterns 5/openings 6/checklist 10全保留→纯档案生成（无素材）开头即用其signature_move"你可能正在…"且全程用"你"遵守taboo。upvideos端点（spi指纹+minimal参数+WBI）+前端UI（下拉✓档✓蒸后缀、蒸馏/拉取视频/导入按钮组、importOpen面板）。潜伏bug：getMixinKey的join()逗号分隔——搜索端点不校验w_rid掩盖，space端点暴露，已修join("")。

*Relevance: high*
*Context: content-creator 风格蒸馏管线 P0+P1 实施*
*Tags: 风格蒸馏 导入通道 style_profiles WBI*

---
*Observed: 2026-09-29T14:30:53.418Z*
