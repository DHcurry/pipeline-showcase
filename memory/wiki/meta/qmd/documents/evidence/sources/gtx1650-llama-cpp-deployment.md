---
type: source
title: GTX 1650 4GB llama.cpp 本地部署路径
status: insight
category: devops
created: 2026-08-11
updated: 2026-08-11
slug: gtx1650-llama-cpp-deployment
---

# GTX 1650 4GB llama.cpp 本地部署路径

在 GTX 1650 4GB（无 Tensor Core）上成功部署本地推理：llama-cpp-python 0.2.90 + CUDA 12.4 预编译轮子，Qwen2.5-3B Q4_K_M 全 GPU 24-26 tok/s、7B Q3_K_M 18.3 tok/s，均过 10 tok/s 红线。核心链路：ExLlamaV2 无 Windows 轮子→回退 llama.cpp；轮子在 GitHub Releases（被墙）→ghfast.top 代理；CUDA DLL 靠 pip 的 nvidia-cuda-runtime-cu12/nvidia-cublas-cu12（PyPI 慢→清华 TUNA 镜像）；模型走 hf-mirror.com。[[esp32-桌面机器人项目]] 相关网络环境结论：该机器 github/huggingface 直连不通，hf-mirror + ghfast.top + TUNA 三通道可用。参数坑：--n_ctx 而非 ctx_size、--flash_attn 需显式 True、KV 量化 --type_k/v 8。

*Category: devops*

---
*Captured: 2026-08-11*

## Related

_Add links to related pages._
