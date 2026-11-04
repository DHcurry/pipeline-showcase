---
type: source
title: R1推理模型在KGQA上无法提升的根因
status: insight
category: analylsis
created: 2026-09-13
updated: 2026-09-13
slug: r1-kgqa-degradation-root-cause
---

# R1推理模型在KGQA上无法提升的根因

KGQA 中轻量推理模型（DeepSeek-R1-Distill-8B Q3量化，本地 4GB 部署）相对微调版 LLaMA2-7B baseline 反而下降的根因分析：

**实验数据**：WebQSP 20题 Acc 30% vs baseline 85.69%。

**三大根因**：
1. **GNN 检索到的"路径"是关系序列而非实体**：模型输入如 `people.person.name -> people.person.name`，这是 Freebase 关系链，不含具体的实体名（如 "Pat Nixon"）。R1 不知道路径末端的实体是什么，只能复述关系串（"people.person.name"），无法给出可验证的实体答案。
2. **路径质量差（对未微调模型）**：KGQA 的推理路径是 RoG 用 beam search 生成的，本身含噪声。微调后的 LLaMA2 学过"路径→答案"的映射；而 R1-8B Q3 未针对 KGQA 微调，看到噪声路径只能瞎猜或复述。
3. **量化+规模双重劣化**：8B Q3 相比 7B（RoG 微调）在语义理解上反而弱；R1 强调"思考"反而在 600 token 内陷入自我怀疑循环，把 token 耗在思考而非答案上。

**核心结论（研究价值）**：GNN-RAG 的路径检索信息在"未微调的通用推理模型"上无法直接利用——推理模型对路径的"关系-实体解引用"能力不足。这印证了 GNN-RAG 论文中"路径需针对 LLM 预适配/微调"的设计。真正可提升的路径是：用 API 版完整 R1（671B）做对比，或用更大的/微调过的推理模型。[[gtx1650-gguf-reasoning-model]] [[GNN-RAG baseline 实验环境搭建完成]]

*Category: analylsis*

---
*Captured: 2026-09-13*

## Related

_Add links to related pages._
