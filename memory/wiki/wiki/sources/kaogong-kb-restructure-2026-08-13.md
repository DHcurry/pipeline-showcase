---
type: source
title: 考公知识库目录结构重构
status: insight
category: 考公
created: 2026-08-13
updated: 2026-08-13
slug: kaogong-kb-restructure-2026-08-13
---

# 考公知识库目录结构重构


考公知识库完成目录结构重构（2026-08-13）：

## 重构内容

1. **错题按题型分组**：从平铺108个文件改为按主旨题/逻辑填空/下文推断等7个题型分组
2. **词语辨析按类型分组**：从平铺76个文件改为按成语辨析/实词辨析分组
3. **知识点+坑点合并**：从分开的"知识点/"和"考官手法/"合并为"知识体系/"下的两个子目录
4. **模板优化**：更新错题模板，确保 Obsidian 兼容（tags用数组，中文值加引号）

## 新目录结构

```
vault/
├── 错题/（108个，按题型分组）
├── 词语辨析/（76个，按类型分组）
├── 知识体系/（19个，知识点+坑点）
├── 教材/（7个）
├── 复习/（3个）
└── 模板/（2个模板）
```

## 入库规范

- 必填：date, mastery, review_stage, next_review（成长性标志）
- 分类：category, sub_category, error_type
- tags 用 YAML 数组格式
- 中文属性值用双引号包裹

## 相关页面

- [[entities/考公知识库]] — 知识库实体
- [[concepts/考公知识库-目录索引]] — 文件清单


*Category: 考公*

---
*Captured: 2026-08-13*

## Related

_Add links to related pages._
