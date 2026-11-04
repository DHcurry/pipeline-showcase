---
name: "schema-driven-llm-lit-extraction"
description: "Schema 驱动的 LLM 文献信息抽取管线（分模块 Prompt + 程序侧校验 + 断言回归）搭建流程"
version: 1
created: "2026-11-02"
updated: "2026-11-02"
---
## When to Use
当需要为一类科研文献设计数据库字段体系(Schema)并用 LLM 自动抽取结构化信息、或改造已有抽取管线时使用。

## Procedure
1. 读文献确定研究领域与论文叙述套路，先划 5-8 个信息维度（S0 基础/样品表、S1 领域关键量、S2 制备、S3 结构成像、S4 性能测量、S5 谱学、S6 理论），再细化叶子字段；每条性能记录=material_id+数值+条件+图号。
2. 写 schema.json（含 version/changelog/null_policy/material_id 规则）与 schema_doc.md（字段表可由 schema 程序生成，避免漏字段），JSON 用 python -m json.tool 校验。
3. 实现抽取程序：读 Markdown→S0 先抽得样品表→其余维度并行、每维度一个 Prompt（字段结构+填写规则+样品表+全文）→程序侧 Schema 校验（补 null/删多余字段/类型纠正/丢残缺记录，记入 _meta.issues）→合并输出；单模块重试3次、单篇失败不中断批量。
4. Prompt 硬规则：无依据填 null 禁编造；表格(<table>)与摘要数值必须扫描；温度三分类(制备/退火/测量)不混用；_C 字段一律摄氏度、原文 K 要换算并保留原值；区间值填字符串字段。
5. 选 2-3 篇对照原文写 verify 脚本，把关键事实固化为断言（含'原文未给→必须 null'的反编造断言），每轮改动后回归。
6. 实际运行全组文献，用 extraction_report.json 看填充率与 issues，对照总结发现的问题并回改 Schema/Prompt/代码。

## Pitfalls
- 烧结/退火温度字段若定义为 number，论文给'1400-1600 °C'区间时会被迫置 null——区间型字段用 string。
- 模型常漏扫 HTML 表格和摘要中的关键指标，必须在 Prompt 显式强制。
- 原文以 K 给出的温度直接填入 _C 字段造成 273 度偏差——要求换算并在 note 保留原文值。
- 调试开关 --only-module 若把未抽维度'补齐 null'再整体写回，会清空已有结果——增量模式必须只覆盖所跑维度。
- LLM 会输出 schema 外的自造字段，且单次抽取有随机波动——必须程序侧校验+断言回归，不能靠 Prompt 自觉。
- zip 内中文文件名常是 cp437→gbk 编码（flag_bits 0x800 区分），直接 decode 会报错。

## Verification
1. python -m json.tool schema.json 通过
2. python extract.py 全量运行，报告 8/8（或全部）成功、无 fatal_error
3. python verify_results.py 全部断言 PASS（含反编造 null 断言）
4. 输出 JSON 顶层维度键与 schema 完全一致、无多余键