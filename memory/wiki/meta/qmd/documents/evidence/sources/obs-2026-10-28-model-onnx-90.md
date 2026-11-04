---
type: source
title: "Observation: 实验一 model.onnx 本地训练导出并验证通过（识别率90%）"
tags:
  - onnx
  - mnist
  - 希冀
  - 实验一
  - 导出
  - 验证
status: observation
created: 2026-10-28
updated: 2026-10-28
slug: obs-2026-10-28-model-onnx-90
relevance: high
observed_at: 2026-10-28T16:52:00.553Z
source_context: 本地训练 ONNX 手写数字模型供希冀平台实验一使用
---

# ⭐ Observation: 实验一 model.onnx 本地训练导出并验证通过（识别率90%）

实验一(ONNX图像分类)的 model.onnx + metadata.json 已在本地训练导出并全链路验证通过。产物目录 C:\Users\16575\exp_jupyter\upload\：model.onnx (971KB, opset13, 输入 NHWC [batch,224,224,3] float32, 输出 10 类 softmax 概率)、metadata.json (labels ['0'..'9'], polarity 白底黑字)、test_data\0~9 各 5 张手写风 PNG、exp_upload.zip (三者打包，平台端解压即用)。源码 train_and_export.py（4 epoch, 测试集 97.51%, 峰值显存 0.74GB）、gen_test_images.py（Ink Free/Segoe Print/楷体随机字号旋转偏移生成）、verify_notebook_code.py（内嵌用户原版 ImageClassifier 类跑通：50 张总体识别率 90%，3/4/5/6 各有错分，反色对照仅 10%）。用户将自行上传到江南大学 WebVPN 希冀平台 Jupyter 实验环境。

*Relevance: high*
*Context: 本地训练 ONNX 手写数字模型供希冀平台实验一使用*
*Tags: onnx mnist 希冀 实验一 导出 验证*

---
*Observed: 2026-10-28T16:52:00.553Z*
