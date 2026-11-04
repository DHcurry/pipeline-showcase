---
type: source
title: "Observation: 671B 全量 DeepSeek 本地部署最低成本方案调研"
tags:
  - deepseek
  - 671B
  - 部署
  - 硬件选型
  - llama.cpp
  - ktransformers
  - mac-studio
status: observation
created: 2026-10-11
updated: 2026-10-11
slug: obs-2026-10-11-671b-deepseek
relevance: medium
observed_at: 2026-10-11T05:40:28.089Z
source_context: 回答全量 DeepSeek 最低成本部署方案
---

# 🔍 Observation: 671B 全量 DeepSeek 本地部署最低成本方案调研

调研"最低成本跑全量 DeepSeek(671B)"结论：(1) 纯CPU方案约¥3.8万：MZ73-LM1/MZ33-AR1 主板 + EPYC 9135/9115 + ≥512GB DDR5 + llama.cpp，Q8 实测 7.17 tok/s（腾讯玄武实验室）；(2) Mac Studio M3 Ultra 512GB 约¥6-7.4万，MLX Q4 约 15-19 tok/s，单机性价比最高；(3) ktransformers：24GB 显存 + 382GB 内存跑 Q4_K_M(377GB)，decode 9-14 tok/s；(4) GPU 满血 FP8 需 8×H100/H200，¥50万+，非最低成本。本网络 HuggingFace 不通，几百GB 权重须走 hf-mirror.com 或 ModelScope。用户现有 GTX1650 4GB+24GB RAM 无法跑 671B。

*Relevance: medium*
*Context: 回答全量 DeepSeek 最低成本部署方案*
*Tags: deepseek 671B 部署 硬件选型 llama.cpp ktransformers mac-studio*

---
*Observed: 2026-10-11T05:40:28.089Z*
