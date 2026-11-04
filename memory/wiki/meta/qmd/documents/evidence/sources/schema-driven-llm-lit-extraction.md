---
type: source
title: Schema 驱动 LLM 文献抽取：分模块 Prompt + 程序侧校验 + 断言回归
status: insight
category: architecture
created: 2026-11-02
updated: 2026-11-02
slug: schema-driven-llm-lit-extraction
---

# Schema 驱动 LLM 文献抽取：分模块 Prompt + 程序侧校验 + 断言回归

Schema 驱动的 LLM 文献信息抽取管线已验证可行（8 篇论文 56 模块全成功、14/14 回归断言通过）：[[schema-driven-llm-lit-extraction]]

关键做法与坑：
1. **按维度分模块 Prompt**，S0（样品表 material_id）先行，其余维度并行并在 Prompt 中携带样品表——解决多组分串台。
2. **程序侧 Schema 校验不可省**：补 null / 删 schema 外字段 / 类型纠正 / 丢残缺记录，全部记入 _meta.issues；不能靠模型自觉。
3. **字段类型要贴合论文给值方式**：烧结温度定义为 number 时，"1400-1600 °C"区间被迫置 null（v1.0.1 改 string 修复）。
4. **Prompt 必须强制扫描 HTML 表格与摘要**：否则 Table 里的 Q×f=4108 等关键指标会被"论文未给出具体数值"漏掉。
5. **单位陷阱**：原文 1423 K 被直接填入 °C 字段——规则改为换算+note 保留原文值。
6. **增量重跑（--only-module）只覆盖所跑维度**，否则未抽维度被"补齐 null"覆盖清空（已修 bug）。
7. 用 verify 脚本固化关键事实为断言，每轮改动后回归，抗 LLM 单次波动。

*Category: architecture*

---
*Captured: 2026-11-02*

## Related

_Add links to related pages._
