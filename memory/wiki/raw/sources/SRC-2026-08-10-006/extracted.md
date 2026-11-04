---
tags: [首页, 词语辨析]
---

# 📖 逻辑填空·词语辨析库

> 逻辑填空的核心是词语辨析。积累词组差异，做题时一眼锁定正确选项。

---

## 📊 总览

```dataview
TABLE error_type AS 类别, review_stage AS 复习阶段, next_review AS 下次复习
FROM "vault/词语辨析"
SORT file.name ASC
```

---

## 🏷️ 按类别浏览

```dataview
TABLE length(rows) AS 词组数
FROM "vault/词语辨析"
WHERE error_type
GROUP BY error_type
SORT length(rows) DESC
```

---

## 📅 今日待复习

```dataview
LIST
FROM "vault/词语辨析"
WHERE next_review <= date(today) AND review_stage < 6
SORT next_review ASC
```

---

## 📝 快速操作

- 运行 `python scripts/ebbinghaus.py` 查看今日复习计划
- 新词组通过 `python scripts/add_vocab.py` 录入
