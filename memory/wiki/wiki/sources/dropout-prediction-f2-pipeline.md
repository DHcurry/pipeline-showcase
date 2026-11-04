---
type: source
title: 辍学预测 F-beta(2) 管线的已验证做法
status: insight
category: datascience
created: 2026-10-25
updated: 2026-10-25
slug: dropout-prediction-f2-pipeline
---

# 辍学预测 F-beta(2) 管线的已验证做法

在 HUDK4050 辍学预测挑战（[[E:/dropout_challenge]]）中验证的要点：

1. **时间快照型进度数据的聚合**：进度 CSV 是每学期快照，同一学生多行，按 (StudentID, Term) 去重后聚合出 n_terms、gpa_mean/std/last、cum_gpa_drop、termspan 等轨迹特征，是主要预测信号。
2. **标签截断效应**：最新 cohort (2016-17) 标签全为 0，因为入读时间太短无法观测辍学。GroupKFold 按 cohort 分折时该折 F-beta=0；用 StratifiedKFold 评估更贴近测试分布。
3. **F-beta(beta=2) 阈值寻优**：在 OPF 上枚举阈值得到 th=0.15 即可最大化 F2（偏召回），比默认 0.5 提升巨大（0.86 vs 更低）。
4. **LightGBM 处理 pandas 类别特征**：object 列（地址、城市）必须剔除或编码，否则报 "pandas dtypes must be int, float or bool"；空 CSV（Spring 2013 静态文件 0 字节）读取前要检查文件大小。

*Category: datascience*

---
*Captured: 2026-10-25*

## Related

_Add links to related pages._
