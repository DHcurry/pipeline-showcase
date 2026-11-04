---
type: source
title: 行尾检测假阳性与字符串替换引入不可见字符的教训
status: insight
category: backend
created: 2026-09-27
updated: 2026-09-27
slug: crlf-detection-and-invisible-chars
---

# 行尾检测假阳性与字符串替换引入不可见字符的教训

## 教训1：grep 检测 CRLF 会假阳性

用 `grep -c $'\r' "$f"` 检测文件行尾，四个文件全报"CRLF 100%"，据此写的 CRLF 转换替换全部 count=0 失败。实际原因：`$'\r'` 在该 shell 上下文中展开为空 → 空模式匹配所有行 → count = 总行数。

**正确做法**：python 逐文件统计 `c.count('\r\n')` 与 `c.count('\n') - crlf`。同一仓库可能混合行尾（content-creator 的 ai.ts 是 CRLF，bilibili.ts/database.ts/projects.ts/MaterialsTab.tsx 全是 LF）——**必须逐文件检测，不能假设**。

## 教训2：多行字符串替换必须在真实行尾下匹配

替换脚本应：读文件时 `newline=''`（保留原始行尾），old/new 用同一行尾生成，且 count==1 断言失败即退出不写盘（保证原子性）。

## 教障3：edit/JSON 传输可引入不可见字符

用 edit 工具写含 `\uFFFD` 的字符串数组后，文件里出现 `"\ue6c3"`（私有区 PUA 字符）和疑似空串 `""`——grep 输出中不可见，python repr 才暴露。若数组里真混入空串，`text.includes("")` 永远为真 → 质量检测恒判低分 → **所有字幕视频都会被自动转写**。

**防御**：
1. 修改后用 `repr()` 打印实际内容确认（打印前 `sys.stdout.reconfigure(encoding='utf-8')`，否则 GBK 控制台打印 PUA 字符直接 UnicodeEncodeError）
2. 对"模式匹配数组"类代码，写单测覆盖**正常样本**（防止恒真条件）
3. 整行正则重写（`re.sub(r'const x = \[[^\n]*\]', ...)`）比字段级 patch 更能清除整行垃圾

content-creator-workspace 字幕质量检测：单测5例全过后才上线（normal 85留字幕 / sparse 55转写 / overflow 30转写 / mojibake 55转写 / empty 0）。

相关：[[session-json-bracket-repair]]

*Category: backend*

---
*Captured: 2026-09-27*

## Related

_Add links to related pages._
