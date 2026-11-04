---
type: source
title: PTA SQL考试70题全部AC满分700
status: insight
category: automation
created: 2026-11-02
updated: 2026-11-02
slug: pta-exam-70-ac-full-score
---

# PTA SQL考试70题全部AC满分700

2026-11-01 PTA "26-9-数据库" 考试最终结果：**70/70 题全部 AC，700/700 分**。

## 关键时间线
- 首轮考试：读了 70 题题面 + 131 张图片、写好 69 题答案，但全部准备完才提交 → 考试到期，仅 10-1 通过（10 分）。**教训：考试必须边解边交。**
- 开放作答后：用 `submit_tpl2.js` 每 2.2 秒一题批量提交 69 题，约 3 分钟全部提交完毕，67 题直接 AC。
- 剩余 3 题修复：
  - 10-2 主键冲突 → 用 rapidocr-onnxruntime OCR 出样例数据，正确行是 `(2,3,'钢笔','001','练字必不可少',15.00,300,3.90,500)`。
  - 10-37/10-38 混淆 → **题目 id 与题号不对应**，我的探测语句全打在 10-37 上，把已 AC 的题打成了失败。核对 label→id 映射后重提，两题均 AC。
  - 10-38 排序要求藏在题面正文（"按登记日期降序"），不是 `ORDER BY product_id`。

## 可复用结论
- PTA API：`POST /api/exams/{examId}/exam-submissions`、`GET /api/exams/{examId}/submissions/{sid}`（protobuf，status 5=AC）、`last-submissions?problem_set_problem_id=`。
- 期望输出列名可从题目详情 `f1.f4.f9.f5`（结果表结构 DDL）拿到，比猜列名可靠。
- 排序/范围等约束常只在题面文字里，样例图只体现数据。
- 已沉淀为 skill：`pta-exam-sql-automation`（global）。

相关：[[sources/obs-2026-11-01-pta-69-1]]

*Category: automation*

---
*Captured: 2026-11-02*

## Related

_Add links to related pages._
