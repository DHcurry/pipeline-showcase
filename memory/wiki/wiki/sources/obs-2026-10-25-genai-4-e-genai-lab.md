---
type: source
title: "Observation: GenAI实验课4实验完成，交付物在E:\\GenAI_lab\\实验报告"
tags:
  - GenAI实验课
  - 交付
  - elasticsearch
  - fastsdcpu
  - haystack
status: observation
created: 2026-10-25
updated: 2026-10-25
slug: obs-2026-10-25-genai-4-e-genai-lab
relevance: high
observed_at: 2026-10-25T06:15:55.772Z
---

# ⭐ Observation: GenAI实验课4实验完成，交付物在E:\GenAI_lab\实验报告

GenAI实验课4个实验全部完成并出具报告。交付物在 E:\GenAI_lab\实验报告\（4份docx + 实验结果附件，9.8MB）。D:\mCloudDownload\GenAI实验课 已100%满（0字节剩余），无法在D盘放交付物，报告改放E盘。关键环境事实：①lab venv=E:\GenAI_lab\venv（transformers 4.46.3 + haystack-ai 2.26.1 + elasticsearch-haystack 5.5.0，导入路径为 haystack_integrations.document_stores.elasticsearch）；②fastSD CPU env 的 pyvenv.cfg home 指向原机器路径，已改为本机 Python311；③sd-turbo 的 unet fp32 权重在压缩包中损坏，用 fp16 权重复制为 diffusion_pytorch_model.safetensors 解决；④settings.yaml 的 results 路径已改 E 盘；⑤ES 8.15.3 用 Popen+cmd 启动可脱离 TTY 存活（MonitorCreate 跑 bat 只打印提示符即退出）。

*Relevance: high*
*Tags: GenAI实验课 交付 elasticsearch fastsdcpu haystack*

---
*Observed: 2026-10-25T06:15:55.772Z*
