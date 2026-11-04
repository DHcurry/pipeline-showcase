---
type: source
title: "Observation: GNN-RAG baseline 实验环境搭建完成"
tags:
  - KGQA
  - GNN-RAG
  - baseline
  - experiment
  - research
status: observation
created: 2026-09-01
updated: 2026-09-01
slug: obs-2026-09-01-gnn-rag-baseline
relevance: high
observed_at: 2026-09-01T04:43:56.673Z
source_context: GNN-RAG baseline setup and experiment
---

# ⭐ Observation: GNN-RAG baseline 实验环境搭建完成

成功搭建 GNN-RAG (cmavro/gnn-rag) 实验环境。关键发现：

1. 仓库已包含预计算结果：GNN检索结果 (test.info)、RoG推理路径 (predictions_3_False.jsonl)、LLM预测结果
2. Baseline 性能：WebQSP Acc=85.69%, F1=71.28%; CWQ Acc=66.81%, F1=59.43%
3. 创建了 run_experiment.py 脚本支持 OpenAI API 调用和自定义实验
4. 代码使用旧版 OpenAI API (v0.x)，需要适配新版本
5. GTX 1650 (4GB) 无法运行本地 7B 模型，建议使用 OpenAI API
6. 关键路径: C:/Users/16575/gnn-rag/llm/run_experiment.py

*Relevance: high*
*Context: GNN-RAG baseline setup and experiment*
*Tags: KGQA GNN-RAG baseline experiment research*

---
*Observed: 2026-09-01T04:43:56.673Z*
