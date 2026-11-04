---
type: source
title: "Observation: WebQSP原始数据与项目数据一致性验证完成"
tags:
  - WebQSP
  - dataset
  - KGQA
  - data-comparison
  - huggingface
status: observation
created: 2026-09-09
updated: 2026-09-09
slug: obs-2026-09-09-webqsp
relevance: high
observed_at: 2026-09-09T03:39:25.430Z
source_context: WebQSP dataset download and comparison with GNN-RAG project data
---

# ⭐ Observation: WebQSP原始数据与项目数据一致性验证完成

WebQSP原始数据与GNN-RAG项目数据对比完成，结论：完全一致。

关键发现：
1. 通过 hf-mirror.com 镜像成功从 HuggingFace 下载 ml1996/webqsp 数据集（国内网络直连HF超时，镜像可用）
2. 数据规模：train 2848, test 1639, validation 250
3. 项目 predictions.jsonl 有1628条 = 原始1639 - 11条无答案问题
4. 问题文本一致性 100%（1628/1628）
5. 答案一致性 100%（1628/1628）
6. 本地副本保存在 C:/Users/16575/gnn-rag/llm/data_original_webqsp/
7. test.info 用 Freebase mid (m.xxx)，predictions.jsonl 用可读名，可借助 entities_names.json 双向映射
8. 答案分布：49.7%问题只有1个答案，10%问题有10+答案

*Relevance: high*
*Context: WebQSP dataset download and comparison with GNN-RAG project data*
*Tags: WebQSP dataset KGQA data-comparison huggingface*

---
*Observed: 2026-09-09T03:39:25.430Z*
