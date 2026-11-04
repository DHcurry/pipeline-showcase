---
type: source
title: ONNX 模型本地导出给固定 notebook 用的 4 个坑
status: insight
category: bugfix
created: 2026-10-28
updated: 2026-10-28
slug: onnx-notebook-model-export-pitfalls
---

# ONNX 模型本地导出给固定 notebook 用的 4 个坑

帮用户在江南大学 WebVPN 希冀平台的 Jupyter 实验一里补全 ONNX 推理代码时，本地训练导出模型踩了 4 个坑，全部实证修复：

1. **CrossEntropyLoss 不能吃 softmax 输出**：把 `torch.softmax` 写进 `forward()` 后 loss 卡在 2.05 几乎不降（等价于对概率再取 log）。修复：forward 返回 logits，只在导出包装 `NetForExport` 里加 softmax（notebook 端 `prob*100` 要求输出是概率）。
2. **notebook 预处理输出是 NHWC**：`ImageClassifier.preprocess_image` 返回 `(1,224,224,3)`，若导出成 NCHW 会在 `session.run` 报 `Got invalid dimensions for input: index1 Got:224 Expected:3`。修复：导出 wrapper 里 `x.permute(0,3,1,2)`，dummy 用 `(1,224,224,3)`。**给定 notebook 代码反推模型规格时，以 notebook 的张量形状为准。**
3. **GTX1650 4GB + 224×224 + batch128 = 显存 thrash**：实测单迭代 2088ms、峰值 4.49GB（超过 4GB 卡），训练慢 30 倍。修复：首层 `stride=2`（224→112）+ batch64 → **93ms/迭代、峰值 0.74GB**，4 epoch 120s/epoch。
4. **Windows DataLoader `num_workers>0` 必须有 `if __name__ == "__main__"` 保护**，否则 spawn 子进程重跑整个训练脚本，报 `DataLoader worker exited unexpectedly` / Safe importing of main module。

验证方法：把用户原样贴回的类定义 + 待交付单元格代码内嵌进 `verify_notebook_code.py`，在与平台一致的工作目录下跑通，得到 50 张测试集 90% 识别率、反色对照 10%（后者是报告“极性不一致”论点的直接证据）。

相关：[[sources/obs-2026-10-28-model-onnx-90]]

*Category: bugfix*

---
*Captured: 2026-10-28*

## Related

_Add links to related pages._
