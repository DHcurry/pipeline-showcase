---
type: source
title: "Observation: 二手卡混合跑671B：价格与ktransformers实测"
tags:
  - 二手显卡
  - "3090"
  - 价格
  - ktransformers
  - 671B
  - 混合推理
status: observation
created: 2026-10-11
updated: 2026-10-11
slug: obs-2026-10-11-671b-ktransformers
relevance: medium
observed_at: 2026-10-11T06:05:45.969Z
source_context: 用户问个人主机+二手显卡的中和方案
---

# 🔍 Observation: 二手卡混合跑671B：价格与ktransformers实测

2026年"个人主机+二手卡"跑671B的行情与数据：二手 RTX 3090 24G 因AI需求+显存涨价从2025年中¥2000-2300涨到正常成交¥5500-8000（闲鱼挂牌中位¥7444）；4090 二手¥18500-23000（比新5080还贵）；魔改3080 20G ¥2500-2750。ktransformers 官方：单卡24GB+382GB RAM 跑 671B Q4_K_M(377GB)，prefill 286 tok/s(V0.3 AMX)，decode 13.7 tok/s（专家选择top-6）。unsloth 1.58bit 量化仅需~131GB，可用6-8张3090纯显存跑，但质量明显打折。结论：混合方案加卡主要加速prefill和上下文（agent输入长输出短正吃这个），decode瓶颈在RAM内存带宽，加卡边际收益小。

*Relevance: medium*
*Context: 用户问个人主机+二手显卡的中和方案*
*Tags: 二手显卡 3090 价格 ktransformers 671B 混合推理*

---
*Observed: 2026-10-11T06:05:45.969Z*
