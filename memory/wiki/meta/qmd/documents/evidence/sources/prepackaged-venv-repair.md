---
type: source
title: 预打包venv异机修复：pyvenv.cfg+fp16复制+路径改写
status: insight
category: devops
created: 2026-10-25
updated: 2026-10-25
slug: prepackaged-venv-repair
---

# 预打包venv异机修复：pyvenv.cfg+fp16复制+路径改写

【预打包 Python 环境（rar/zip 里的 venv）在异机修复三件套】适用于 fastsdcpu-1.0.0-beta.64 这类"已装好"的实验环境：① env\Scripts\python.exe 报 "No Python at '原机器路径'" → 重写 env\pyvenv.cfg 的 home/executable 指向本机同版本 Python；② diffusers 报 "no file named diffusion_pytorch_model.bin" → 说明 .bin/.safetensors 权重在打包时损坏被丢弃，若只有 fp16 safetensors，把 diffusion_pytorch_model.fp16.safetensors 复制为 diffusion_pytorch_model.safetensors 即可（fp16→fp32 加载数值无损）；③ settings.yaml 里写死的原机器路径（如 results 目录）要同步改。另外：Windows 上让服务脱离 TTY 常驻要用 Python subprocess.Popen(["cmd","/c",bat])，MonitorCreate/cmd /c 在无 TTY 下只会打印提示符就退出（ES 8.15.3 与 fastSD API 均验证）。相关 [[sources/obs-2026-10-25-genai-4-e-genai-lab]]。

*Category: devops*

---
*Captured: 2026-10-25*

## Related

_Add links to related pages._
