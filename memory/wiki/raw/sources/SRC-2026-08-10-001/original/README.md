# 考公错题本 - 使用说明

## 架构

```
Memory MCP (知识图谱层)  ←→  Obsidian Vault (笔记层)
         ↓                          ↓
   实体/关系/查询              详细内容/图谱视图
         ↓
   Python 脚本 ─→ 快速录入 / 周复习 / 可视化
```

## 快速开始

### 1. 打开 Obsidian
1. 打开 Obsidian → "Open folder as vault"
2. 选择 `C:\Users\16575\Desktop\考公错题本\vault`
3. 左下角 Graph view 查看知识图谱

### 2. 推荐安装的社区插件

打开 Obsidian → 设置 → 第三方插件 → 关闭安全模式 → 浏览：

| 插件 | 用途 |
|------|------|
| **Dataview** | Dashboard 数据查询（必装） |
| **Calendar** | 日历视图快速创建每日记录 |
| **Minimal Theme** | 好看的主题（可选） |
| **Kanban** | 看板式复习进度管理（可选） |

### 3. 使用方式

#### 方式 A：告诉 Agent（推荐）

在对话中说：
> "我做了一道假言命题的题，题目是...我选了C但答案是B，
>  错误原因是混淆了充分条件和必要条件"

Agent 会自动帮你整理到 vault 和图谱中。

#### 方式 B：命令行脚本

```bash
# 交互式录入
python scripts/add_error.py

# 非交互式录入
python scripts/add_error.py --non-interactive \
  --title "假言命题" --category "判断推理" \
  --error-type "概念混淆" --question "题目..." \
  --my-answer "C" --correct-answer "B" \
  --reason "混淆了充分条件和必要条件" \
  --knowledge-points "充分条件,假言命题"
```

#### 方式 C：手动添加
1. 复制 `vault/模板/错题模板.md`
2. 重命名为 `YYYY-MM-DD-题目关键词.md` 放入 `vault/错题/`
3. 填写内容，用 `[[知识点]]` 格式关联

### 4. 艾宾浩斯间隔复习

```bash
python scripts/ebbinghaus.py                  # 查看今日复习计划
python scripts/ebbinghaus.py --stats          # 查看整体进度
python scripts/ebbinghaus.py --upcoming 7     # 未来7天安排
python scripts/ebbinghaus.py --mark-reviewed "题目"  # 标记已复习
python scripts/ebbinghaus.py --mark-forgot "题目"    # 标记忘了（重置）
python scripts/ebbinghaus.py --init           # 初始化所有笔记
```

间隔: 1天 → 2天 → 4天 → 7天 → 15天 → 30天

### 5. 生成周复习报告

```bash
python scripts/weekly_review.py        # 本周报告
python scripts/weekly_review.py --weeks 1  # 上周报告
python scripts/weekly_review.py --no-save  # 只看终端不保存笔记
```

### 6. 生成知识图谱

```bash
python scripts/visualize_graph.py          # 生成图片
python scripts/visualize_graph.py --stats  # 只看统计
```

## 目录结构

```
考公错题本/
├── vault/                          ← Obsidian vault 目录
│   ├── 首页.md                     ← Dashboard（装 Dataview 插件后生效）
│   ├── 错题/                       ← 每道错题一条笔记
│   ├── 知识点/                     ← 知识点卡片
│   ├── 错误类型/                   ← 错误类型说明 + 改进策略
│   ├── 复习/                       ← 自动生成的周复习笔记
│   └── 模板/                       ← 笔记模板
│       ├── 错题模板.md             ← 行测错题
│       ├── 申论错题模板.md         ← 申论错题
│       ├── 周复习模板.md           ← 周复习
│       └── 每日记录模板.md         ← 每日学习记录
├── scripts/
│   ├── add_error.py                ← 快速录入脚本
│   ├── ebbinghaus.py               ← 艾宾浩斯间隔复习
│   ├── weekly_review.py            ← 周复习生成器
│   └── visualize_graph.py          ← 知识图谱可视化
├── knowledge_graph.png             ← 生成的图谱图片
└── README.md                       ← 本文件
```

## 错误类型

| 错误类型 | 说明 | 改进方向 |
|----------|------|----------|
| 概念混淆 | 相似概念搞混 | 对比记忆，具体例子验证 |
| 审题不仔细 | 没看清题目要求 | 圈画关键词，读两遍题目 |
| 计算失误 | 思路对但算错 | 草稿整洁，关键步骤验算 |
| 公式记错 | 公式记忆不准 | 理解推导，定期默写 |
| 粗心 | 马虎大意 | 放慢速度，检查机制 |
| 时间分配不当 | 某题花太久 | 严格计时，先易后难 |

## 复习建议

1. **每天**：做题后立即录入错题（方式 A/B/C）
2. **每天**：运行 `python scripts/ebbinghaus.py` 查看今日复习任务
3. **每周**：运行 `weekly_review.py`，查看报告并生成复习笔记
4. **打开 Dashboard**：在 Obsidian 中查看 `首页.md` 的实时统计
5. **关注图谱**：连线最多的知识点节点 = 最薄弱的地方
6. **定期回顾错误类型**：打开 `vault/错误类型/` 查看改进策略

## Memory MCP 说明

重启 Hermes 后可用的工具（可选，主要用于跨会话查询）：

| 工具 | 用途 |
|------|------|
| `mcp_memory_create_entities` | 创建实体 |
| `mcp_memory_create_relations` | 建立关系 |
| `mcp_memory_search_nodes` | 搜索节点 |
| `mcp_memory_open_nodes` | 查看节点详情 |
