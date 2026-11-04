---
type: source
title: 4GB 显卡内存借用方案跑 7B agent
status: insight
category: devops
created: 2026-08-11
updated: 2026-08-11
slug: gtx1650-7b-ram-offload-agent
---

# 4GB 显卡内存借用方案跑 7B agent

GTX 1650 4GB 上用「25 层 GPU + 3 层 RAM」混合卸载成功跑起 Qwen2.5-7B-Q3_K_M 作为 pi agent：ctx 16384（能装下 pi 的 10k+ agent 上下文），生成 13.5 tok/s（纯 GPU 是 21.6 但只能 2048 ctx），prefill 74 tok/s（10k 输入约 2-3 分钟首轮延迟）。关键调参：llama.cpp 路由 models-preset.ini 里 n-gpu-layers=25 + parallel=1 + batch-size=512 + ctx-size=16384 + KV q8；并行 slot 必须减到 1 否则显存不够导致 prefill 掉到 CPU（1.18 tok/s 灾难）。教训：显存紧张时 prefill 计算缓冲优先于多余 KV slot。pi 端 models.json 需同步 contextWindow/maxTokens 才能用。[[gtx1650-llama-cpp-deployment]] 用户主动放弃"禁止 offload"红线换取 7B 质量。

*Category: devops*

---
*Captured: 2026-08-11*

## Related

_Add links to related pages._
