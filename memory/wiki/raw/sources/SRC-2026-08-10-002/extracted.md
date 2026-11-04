---
tags: [首页]
cssclass: dashboard
---

# 📚 考公错题本

> 每道错题都是一次进步的机会。记录、分析、攻克。

---

## 📊 数据总览

```dataview
TABLE length(rows) AS 数量
FROM "vault/错题"
GROUP BY "错题总数"
```

```dataview
TABLE length(rows) AS 数量
FROM "vault/词语辨析"
GROUP BY "词语辨析"
```

```dataview
TABLE length(rows) AS 数量
FROM "vault/知识点"
GROUP BY "知识点"
```

---

## 🔥 最近错题

```dataview
TABLE date AS 日期, category AS 模块, error_type AS 错误类型
FROM "vault/错题"
SORT date DESC
LIMIT 10
```

---

## 🎯 高频错误类型

```dataview
TABLE length(rows) AS 错题数
FROM "vault/错题"
WHERE error_type
GROUP BY error_type
SORT length(rows) DESC
```

---

## 📁 按模块分类

```dataview
TABLE length(rows) AS 错题数
FROM "vault/错题"
WHERE category
GROUP BY category
SORT length(rows) DESC
```

---

## 📅 本周错题

```dataview
LIST
FROM "vault/错题"
WHERE date >= date(today) - dur(7 days)
SORT date DESC
```

---

## 🗺️ 知识图谱

```dataview
TABLE tags AS 标签
FROM "vault/知识点"
SORT file.name ASC
```

---

## 🏷️ 标签云

```dataview
TABLE length(rows) AS 数量
FROM "vault/错题"
FLATTEN tags AS tag
GROUP BY tag
SORT length(rows) DESC
LIMIT 15
```

---

## 🎯 自适应复习系统

> 根据你的表现动态调整推送频率！答对→减少推送，答错→加强推送+讲解

| 等级 | 推送频率 | 说明 |
|------|----------|------|
| 🆕 新学 | 每天 | 刚加入的内容 |
| 📖 初识 | 每2天 | 答对1次 |
| 📝 熟悉 | 每4天 | 答对2次 |
| ✅ 掌握 | 每8天 | 答对3次 |
| ⭐ 熟练 | 每16天 | 答对4次 |
| 🏆 精通 | 每30天 | 答对5次 |

**使用方法：**
1. 每天早上9点收到闪卡推送
2. 回忆答案后回复「对」或「错了+你的理解」
3. MiMo 判断并更新掌握等级
4. 系统自动调整后续推送频率

---

## 📝 快速操作

- [[今日复习|📅 今日复习]]
- [[复习看板|📊 复习看板]]
- [[vault/模板/错题模板|📝 新建行测错题]]
- [[vault/模板/申论错题模板|📝 新建申论错题]]
- [[vault/词语辨析/README|📖 逻辑填空·词语辨析库]]
- [[vault/模板/周复习模板|📋 周复习]]

---

## 🔗 导航

| 分类 | 入口 |
|------|------|
| 判断推理 | `#判断推理` |
| 言语理解 | `#言语理解` |
| 数量关系 | `#数量关系` |
| 资料分析 | `#资料分析` |
| 常识判断 | `#常识判断` |
| 申论 | `#申论` |

---

> 💡 **使用提示**：做题后直接告诉我"我做了一道XX题，选了X，答案是Y，错因是Z"，我会自动帮你整理到这个系统里。
