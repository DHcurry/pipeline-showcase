---
type: source
title: EMM迭代内refit的三条硬规则（RIM实证）
status: insight
category: architecture
created: 2026-10-09
updated: 2026-10-09
slug: emm-within-loop-refit-rules
---

# EMM迭代内refit的三条硬规则（RIM实证）

在正则化EM（LASSO选支撑集 + 无惩罚refit去偏）的"EMM"变体中，把无惩罚refit放进EM循环内部会引入反馈回路，若不设约束会导致有效惩罚被架空、支撑集爆炸。研究二在RIM模型上用约3100次蒙特卡洛拟合得到三条可复用的规则：

**规则1：第二个M步只能更新被选中的γ。** 进入refit前把非选中γ置0并不够——坐标下降循环内部若不做索引过滤，全部γ仍会获得Newton步（eta_pen=0时软阈值阈值为0），漂移的非选中γ会通过Fisher交叉项污染选中γ与nuisance参数的更新方向。必须显式传入active_gamma并在循环里跳过+锁定为0。

**规则2：第二个M步必须冻结α/ζ等nuisance参数，只动γ。** 若refit同时重估α/ζ，被抬高的这一组参数会连同γ进入下一轮E-step，抬高惩罚步对其他陈述的打分，形成正反馈。实测同eta下TypeI从0.136膨胀到0.336（2.5倍），支撑集出现16/21的"全选"爆炸；冻结α/ζ后回落至0.174，全量验证TypeI 0.516→0.135。

**规则3：η必须随总样本量缩放。** 软阈值 τ=η·w/h 中Fisher信息h∝N，固定η的有效惩罚随N衰减（1/N）。参考网格须锚定在某个总N上（如n_total=2000），令 η_eff = η × n_total / N_ref。实测未缩放时N=3000的TypeI（0.205）约为N=1000（0.065）的三倍；缩放后N=3000降至0.028，且N=1000行为逐位不变（便于对照）。

**共同症状识别**：BIC/调参准则持续顶在惩罚网格上界、同η下refit版本比不refit版本多选一倍以上参数、结果对初始值敏感（非refit版本不敏感）。出现任一症状即应检查上述三条。

**最终指标**：TypeI 0.495→0.046、Power 0.894→0.945、平均选中数11.07→2.44、DSF参数RMSE 0.337→0.045。

相关：[[sources/obs-2026-10-09-8-3100]]

*Category: architecture*

---
*Captured: 2026-10-09*

## Related

_Add links to related pages._
