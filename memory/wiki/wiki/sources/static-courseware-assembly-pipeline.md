---
type: source
title: 静态课件组装流水线：切分旧幻灯+三道校验
status: insight
category: 教学课件工程
created: 2026-10-10
updated: 2026-10-10
slug: static-courseware-assembly-pipeline
---

# 静态课件组装流水线：切分旧幻灯+三道校验

在现有课堂游戏静态课件体系上新增课程时，最稳的组装方式：用 python 按行号切分旧幻灯文件（head=到 `const SLIDES=[` 前一行、tail=从 `const deck=document.getElementById` 起），插入新 SLIDES 数组后替换 title/chap 文案，避免手写整套 CSS/引擎。产出后固定三道校验：① 抽取全部 `<script>` 用 `node --check`（本次抓到 act9-buzzer 题库字符串内嵌 ASCII 双引号的 SyntaxError，改中文引号修复）；② 正则核对 JS 里 `$('id')` 与 HTML id 一一对应；③ 起 SimpleServer 对所有新页面 curl 200。注意：Windows 控制台 python 需 PYTHONIOENCODING=utf-8，否则打印 emoji 即 GBK 崩溃；edit 工具对 emoji+全角空格 oldText 易失配，含 emoji 的 HTML 批量改动用 python replace 更稳。相关交付见 [[obs-2026-10-10-windows-3]]。

*Category: 教学课件工程*

---
*Captured: 2026-10-10*

## Related

_Add links to related pages._
