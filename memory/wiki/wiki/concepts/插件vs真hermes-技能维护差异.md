---
type: concept
title: 插件vs真Hermes-技能维护差异
created: 2026-08-12
updated: 2026-08-12
---

# 插件 vs 真 Hermes：技能维护差异

> 对比 pi-hermes-memory 插件 (v0.9.3) 与真 Hermes agent 的源码后确认：一处刻意裁剪——技能自动维护能力。

## 对比表

| 维度 | pi-hermes-memory 插件 (v0.9.3) | 真 Hermes agent |
|---|---|---|
| 后台复习是否碰技能 | **否**。后台复习 prompt 明令 `Do NOT create or modify skills in this background review`（src/constants.ts） | **是**。`_SKILL_REVIEW_PROMPT`（agent/background_review.py L182）：`Be ACTIVE — most sessions produce at least one skill update` |
| 技能由谁写入 | 主代理自觉调用 `skill_manage` | fork 子代理直写 skill store（run_agent.py `_spawn_background_review`，review_skills=True） |
| 技能目录 | 包内无 skills 目录（`/learn-memory-tool` 只是教学菜单） | hermes_constants.py：optional-skills + bundled + `<HERMES_HOME>/skills` 多级 |
| 学习频率主张 | 保守：宁缺毋滥 | 激进：什么都不做 = 错过学习机会 |

## 为什么插件砍掉自动技能更新

1. **权限边界**：Hermes 是独立 agent，子代理 fork 直写自己的 skill store；插件寄生在宿主 agent 里，后台子进程没资格替主代理决定固化成技能。
2. **质量闸门**：插件照搬 "Be ACTIVE" 会导致低质量技能批量涌入宿主知识库且无法追溯。
3. **职责分离**：记忆可自动写（事实风险低），技能是程序性知识必须过主代理闸门。

## 思维迁移

自动化边界不是"能不能做"，而是"搞砸了要赔多少"：低风险可逆操作可自动化，高风险影响面操作保留人工闸门。

## 出处

- 书《记忆的工程学》第十二章附：`C:/Users/16575/pi-hermes-memory-思维之书.md`
- 真 Hermes 源码：`/tmp/h2/`（agent/background_review.py L182、hermes_constants.py）
- 插件源码：`C:/Users/16575/.pi/agent/npm/node_modules/pi-hermes-memory/src/constants.ts`
