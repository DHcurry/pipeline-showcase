---
type: source
title: "Observation: DeepSeek-R1-8B 本地部署成功"
tags:
  - llama-cpp
  - GGUF
  - R1
  - KGQA
  - GPU部署
status: observation
created: 2026-09-11
updated: 2026-09-11
slug: obs-2026-09-11-deepseek-r1-8b
relevance: high
observed_at: 2026-09-11T09:17:40.703Z
source_context: 部署 DeepSeek-R1-Distill-Llama-8B 本地推理用于 KGQA 实验
---

# ⭐ Observation: DeepSeek-R1-8B 本地部署成功

GNN-RAG 本地 reasoning 模型部署关键进展（GTX 1650 4GB + 24GB RAM）：

1. 模型选择：DeepSeek-R1-Distill-Llama-8B Q3_K_M GGUF（4.01GB），与 baseline LLaMA2-7B 同架构家族、带完整推理链
2. 关键踩坑记录：
   - llama-cpp-python 0.3.35 CUDA wheel 报 0xc000001d（CPU 无 AVX512），回退 0.2.90 cu124 版成功（wiki 验证过的版本）
   - type_k/type_v 参数必须是整数（8=Q8_0），字符串报错
   - CUDA_PATH 环境变量必须移除，否则 0.2.90 去错误路径找 DLL
   - nvidia DLL（cudart64_12.dll, cublas64_12.dll, cublasLt64_12.dll）手动复制到 llama_cpp/lib
   - 25层GPU+3层RAM 配置成功，加载3.7s，生成13.6s（R1先思考再回答）
3. 输出格式适配：R1-Distill 输出 '思考\n...\n</think>\n\n最终答案: xxx'，已写 extract_r1_answer 正则提取
4. 模型位置：C:/Users/16575/models/DeepSeek-R1-Distill-Llama-8B-Q3_K_M.gguf
5. 脚本：run_reasoning_experiment.py --local_gguf 模式已就绪

*Relevance: high*
*Context: 部署 DeepSeek-R1-Distill-Llama-8B 本地推理用于 KGQA 实验*
*Tags: llama-cpp GGUF R1 KGQA GPU部署*

---
*Observed: 2026-09-11T09:17:40.703Z*
