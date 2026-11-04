---
name: "update-kaogong-kb"
description: "考公知识库日常更新：用户报错题/新知识点时，同时更新 Obsidian vault 与 wiki 索引"
version: 1
created: "2026-08-10"
updated: "2026-08-10"
---
## When to Use
用户报一道新错题（"我做了一道XX题，选了A，答案是B，错因是Z"）、新增词语辨析、更新知识点体系、或要求把新内容加入考公知识库时。

## Procedure
1. 定位根目录：C:\Users\16575\OneDrive\应用\remotely-save\考公错题本（vault 是活数据，wiki 在 C:\Users\16575\.llm-wiki 个人库）
2. 新错题：按 vault/错题/YYYY-MM-DD-主题关键词-题型.md 命名写入，frontmatter 含 date/category/error_type/sub_category/tags（tags 必须取自 vault/标签注册表.md，不得造词）
3. 新词语辨析：写入 vault/词语辨析/词组A-vs-词组B.md，含 error_type 与复习字段（review_stage/next_review）
4. 更新知识点体系：编辑 vault/知识点/对应解题体系.md，并在 vault/考官手法/对应题型-坑点.md 补充坑点
5. 让 wiki 能检索：用 wiki_capture_source(file_path=新文件) 捕获，再 wiki_ingest 后台合成
6. 更新索引页：重新生成 C:/Users/16575/.llm-wiki/wiki/concepts/考公知识库-目录索引.md 的文件清单（218+ 条，wikilink 需用代码格式反引号包裹避免 unresolved 警告）
7. 验证：wiki_status 检查页面数与孤儿数；vault 文件用 Obsidian 或 read 确认

## Pitfalls
- wiki 工具基于会话 cwd 定位：在 home 目录（C:\Users\16575）启动时捕获进个人 wiki ~/.llm-wiki，不要捕获进 OneDrive 的 .llm-wiki（那个空骨架已删除）
- 索引页里的 [[外部vault文件]] wikilink 会触发 link_unresolved 警告刷屏——一律用代码格式，只对 wiki 内部页面用 [[]]
- raw/ 不可变：捕获后不要编辑 raw/sources/ 下的包，改内容就重新 capture 一个新源
- vault 标签必须从标签注册表选，新增 tag 需先注册

## Verification
1. wiki_status 显示 Health ✅ Good、无孤儿
2. 新文件存在于 vault/ 对应目录且命名规范
3. wiki_recall(新错题主题) 能检索到新捕获的源页面
4. grep 索引页确认新文件在清单中