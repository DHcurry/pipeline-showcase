---
type: source
title: 模仿生成内容/风格分离：事实隔离墙与裸key prompt根因
status: insight
category: backend
created: 2026-09-29
updated: 2026-09-29
slug: imitate-style-content-separation
---

# 模仿生成内容/风格分离：事实隔离墙与裸key prompt根因

## 功能：模仿生成的素材二分（2026-09-27 实现）

- **内容素材** = 左侧勾选素材（references，观点与事实的唯一来源）
- **风格素材** = 前端下拉选博主（`style_author`）→ 后端 `listMaterialsByAuthor(projectId, author)` 取该博主最多3篇作品（JSON `json_extract(meta,'$.author')`）→ 仅作风格样本
- 前端：CreateTab 的 `styleAuthors` useMemo（materials.meta.author 去重）+ select；响应回显 `style_author`

## 方法论（来自搜索到的 style-clone SKILL.md）

1. **八维文风画像**：句式节奏/段落结构/词汇偏好(含禁忌清单)/叙事视角/情感温度/论证逻辑/修辞手法/整体基因
2. **事实隔离墙**：风格样本只提炼风格——禁止把样本的观点/事实/案例/数据/专属名词/原句带进成稿（正是"不参考其具体作品"的精确表达）
3. **多篇共同特征优先**：跨篇稳定风格为核心，单篇偶发特征降权——对应"博主平时的文风"

验证成功样例：style_profile 提炼出"哎呀、诶、先说/先给"口头禅+设问过渡+禁忌清单；成稿内容来自 reference（"手机就够了先把第一条发出去"原样来自内容素材），风格（哎呀/一句段/设问）来自博主。

## 关键教训：mimo 裸 key 输出的根因是 prompt 模板自身

`DEFAULT_GENERATE_PROMPT` 的输出示例写的是 `{generated_text: 正文, ...}`（**无引号 key**）——mimo 照抄模板格式输出伪 JSON！修复=模板示例改合法 JSON `{"generated_text": "正文",...}`（根治）+ `quoteBareKeys` 修复器（兜底，字符串感知：只在 `{`/`,` 后且紧跟冒号时补引号，null/true/数字/字符串内容不受影响）。

模板改动会显著影响输出行为——**LLM 输出格式问题先查 prompt 示例本身**，再怀疑模型。

rawFallback 降级路径也要 dump raw 到 last_session_raw.txt（否则诊断时看到的是旧文件残留，误导排查）。

相关：[[session-json-bracket-repair]] [[next16-turbopack-bracket-api-route-bug]]

*Category: backend*

---
*Captured: 2026-09-29*

## Related

_Add links to related pages._
