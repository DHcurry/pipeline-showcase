---
type: source
title: "Observation: TGM2蛋白组分析：M1失败run剔除后C组略高(ns)，选题依据改走PPI/富集"
tags:
  - proteomics
  - TGM2
  - GJ-rat
  - STRING
  - M1-outlier
  - QC
status: observation
created: 2026-10-22
updated: 2026-10-22
slug: obs-2026-10-22-tgm2-m1-run-c-ns-ppi
relevance: high
observed_at: 2026-10-22T06:49:43.972Z
source_context: GJ-rat蛋白组TGM2目标蛋白分析与绘图
---

# ⭐ Observation: TGM2蛋白组分析：M1失败run剔除后C组略高(ns)，选题依据改走PPI/富集

GJ-rat蛋白组TGM2分析完成（源CSV：WeChat接收目录GJ-rat_Report.csv）。关键发现：①M1是整条失败run（894蛋白、信号~1000×、r≈0.4），其TGM2值4.19e9是假象来源，按三条QC标准剔除（其重跑M1X正常）；②清洗+中位数归一化+log2后，TGM2在C组(n=8)略高于HY+M组(n=7)：log2FC=+0.22，Welch p=0.105，Mann-Whitney p=0.152，ns——用户预期的"C组更低"不成立，且任何合规分析（含X重跑并入：log2FC=+0.20, p=0.196）方向一致；③全蛋白3554个可检验，仅10个DEP；④TGM2选题支撑：STRING互作hub（ITGB1 0.783、RELA 0.616、LOX 0.556），LOX是本队列唯一ECM相关DEP(C低)，模块富集NF-κB调控/TLR4/血管组织/TGM2文献簇。产物：E:\TGM2_analysis\（脚本+5图+报告）。

*Relevance: high*
*Context: GJ-rat蛋白组TGM2目标蛋白分析与绘图*
*Tags: proteomics TGM2 GJ-rat STRING M1-outlier QC*

---
*Observed: 2026-10-22T06:49:43.972Z*
