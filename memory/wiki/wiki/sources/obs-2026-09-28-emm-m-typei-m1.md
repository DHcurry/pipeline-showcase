---
type: source
title: "Observation: EMM第二M步修复验证：机制修复成功但TypeI根因在M1阈值"
tags:
  - EMM
  - LASSO
  - RIM
  - TypeI
  - eta-grid
  - coordinate-descent
status: observation
created: 2026-09-28
updated: 2026-09-28
slug: obs-2026-09-28-emm-m-typei-m1
relevance: high
observed_at: 2026-09-28T14:38:05.807Z
source_context: EMM第二M步修复与eta网格扩展实验
---

# ⭐ Observation: EMM第二M步修复验证：机制修复成功但TypeI根因在M1阈值

EMM第二M步修复完成并验证：修改RIM_lasso_engine.R三处（coordinate_descent_mstep加active_gamma参数、gamma循环冻结非选中陈述、EMM refit块传active_gamma+verbose输出M1/M2追踪）。单条件诊断：M1→M2 gamma差异0.49→0.078，假阳性支撑集[1,10]→[1]，EMM LL从比EM差32变为略优。但48单元×10重复全量实验Type I无改善（0.495→0.515），根因是M1软阈值强度：81%的BIC重复选在eta网格上界25、最大惩罚下仍选出10/21个陈述、tau=eta·w/h随N增大而有效惩罚变弱。下一步已启动eta网格扩到100的实验（emm_etaext_experiment.R）。

*Relevance: high*
*Context: EMM第二M步修复与eta网格扩展实验*
*Tags: EMM LASSO RIM TypeI eta-grid coordinate-descent*

---
*Observed: 2026-09-28T14:38:05.807Z*
