---
tags:
  - 错题图谱
  - 索引
  - 行测
  - 言语理解
title: 错题图谱·按错误类型索引
---
# 🗺️ 错题图谱·按错误类型索引
# 🗺️ 错题图谱·按错误类型索引

> 自动从错题库生成，每道错题底部有 `[[知识点/xxx解题体系]]` 即可自动归类。

---

## 按题型 + 错误类型分组

```dataview
TABLE rows.file.link as "错题", rows.error_type as "错误类型", rows.mastery as "掌握"
FROM "错题"
WHERE sub_category != "待定" AND file.name != "README"
SORT file.name DESC
GROUP BY sub_category as "题型"
```

---

## 进阶查询示例

### 未掌握（mastery=0）的错题

```dataview
TABLE error_type, date, sub_category
FROM "错题"
WHERE mastery = 0 AND file.name != "README"
SORT date DESC
```

### 最近7天新增错题

```dataview
TABLE error_type, sub_category
FROM "错题"
WHERE date >= date(today) - dur(7 days) AND file.name != "README"
SORT date DESC
```

---

## 🔗 关联笔记

- [[标签注册表]] — 全部tag注册清单
- [[考官手法/README]] — 考官命题手法索引
