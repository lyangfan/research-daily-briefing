# 科研早报自动化系统

每天自动从 arXiv、bioRxiv、medRxiv 等预印本平台获取最新论文，使用 AI 智能过滤出与「AI Agents for Scientific Research」相关的内容，生成中文结构化总结并保存到本地。

## 功能特点

- **智能过滤**: 使用 Claude CLI + paper-relevance-judge skill 判断论文相关性，支持多种过滤模式
- **PDF 全文处理**: 自动下载并提取 PDF 全文，生成包含具体数据的详细总结
- **中文总结**: 使用 paper-summarizer skill 生成结构化中文摘要
- **自动去重**: SQLite 数据库存储，避免重复处理
- **多平台支持**: arXiv, bioRxiv, medRxiv

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│  Python 脚本执行 (python3 src/main.py run)                  │
│     ↓                                                       │
│     1. 从各平台采集新论文 (arXiv RSS/bioRxiv API)            │
│     2. 关键词初筛                                           │
│     3. Claude CLI + skill 过滤相关性                        │
│     4. 下载 PDF 全文                                         │
│     5. Claude CLI + skill 生成中文总结                      │
│     6. SQLite 存储去重                                       │
│     ↓                                                       │
│  输出早报文件                                                │
│     • data/briefings/output/YYYY-MM-DD.txt                  │
│     • data/briefings/briefings/YYYY-MM-DD.json              │
└─────────────────────────────────────────────────────────────┘
```

## 安装步骤

### 1. 系统要求

- macOS 12+
- Python 3.9+
- **Claude Code CLI** (用于 AI 过滤和总结)

### 2. 快速安装

```bash
# 1. 进入项目目录
cd /Users/liuyangfan/Documents/code/research-daily-briefing

# 2. 运行初始化脚本
bash scripts/setup.sh

# 3. 编辑 .env 文件，填入配置
nano .env
```

### 3. 配置环境变量

编辑 `.env` 文件：

```bash
# 智谱 AI (用于 Embedding 过滤，可选)
ZHIPU_API_KEY=你的智谱API密钥

# OpenAI (用于 Embedding 过滤，可选)
# OPENAI_API_KEY=你的OpenAI密钥
```

**注意**: 本系统使用 **Claude Code CLI** 进行 AI 过滤和总结，不需要配置 ANTHROPIC_API_KEY。

## 使用方法

### 完整流程

```bash
# 完整流程：采集 → 处理 → 生成早报文件
python3 src/main.py run

# 指定日期
python3 src/main.py run --date 2026-02-20
```

**说明**: `run` 命令会生成早报文件到 `data/briefings/output/YYYY-MM-DD.txt`。

### 其他命令

```bash
# 采集和处理论文（保存到数据库，不生成输出文件）
python3 src/main.py fetch

# 测试消息格式（不发送）
python3 src/main.py test

# 查看统计信息
python3 src/main.py stats

# 清理旧数据
python3 src/main.py cleanup
```

### 指定日期

```bash
# 完整流程
python3 src/main.py run --date 2026-02-20

# 仅采集
python3 src/main.py fetch --date 2026-02-20
```

### 查看日志

```bash
# 采集日志
tail -f logs/research_briefing_$(date +%Y-%m-%d).log

# 或查看最新日志
tail -f logs/*.log
```

## 配置说明

### config.yaml

```yaml
# 平台配置
platforms:
  arxiv:
    enabled: true
    categories: [cs.AI, cs.CL, cs.LG, cs.NE, cs.CR, cs.CV]
    batch_size: 100
    max_papers_per_category: 2000
  biorxiv:
    enabled: true
    sections: [bioinformatics]
  medrxiv:
    enabled: true
    sections: [health-informatics]

# AI 过滤配置
ai_filter:
  mode: "claude"              # claude (推荐) | hybrid | keywords | embedding
  model: "claude-3-5-sonnet-20241022"
  max_papers: 0               # 0 表示不限制
  max_workers: 2              # 并行处理线程数（建议不超过 2）
  max_summary_papers: 0       # 输出论文数量上限，0 表示不限制（默认）

  # 过滤模式说明:
  # - claude: 关键词 → Claude CLI 判断 (推荐，准确度最高)
  # - hybrid: 关键词 → Embedding → Claude CLI 判断
  # - keywords: 仅关键词过滤
  # - embedding: 仅 Embedding 相似度

  keywords: [...]             # 初筛关键词 (50+)

  embedding:
    enabled: true
    provider: "zhipu"         # openai | zhipu
    model: "embedding-3"
    similarity_threshold: 0.50

# PDF 下载配置
pdf_download:
  enabled: true
  storage_dir: "data/papers"
  max_text_length: 30000      # 提取的最大文本长度
  timeout: 60                 # 下载超时（秒）
  auto_cleanup: true          # 处理后自动删除 PDF

# 总结生成配置
summarizer:
  language: "zh-CN"
  max_length: 800             # 每篇总结的最大字数
  single_paper_timeout: 600   # 单篇论文总结超时（秒）
  batch_timeout: 900          # 批量总结超时（秒）
  skill_path: "skills/paper-summarizer/SKILL.md"

# 数据存储配置
storage:
  briefings_dir: "data/briefings"
  retain_days: 90
  database_path: "data/briefings.db"
  auto_optimize: true
```

### 关键配置说明

- **`ai_filter.mode`**: 过滤模式，推荐使用 `claude`，准确度最高
- **`ai_filter.max_summary_papers`**: 输出论文数量上限
  - `0`（默认）: 不限制，通过筛选的论文全部输出
  - `10`: 最多输出 10 篇论文
- **`ai_filter.max_workers`**: 并行线程数，建议设为 2，过高会导致 Claude CLI 出错

## 项目结构

```
research-daily-briefing/
├── config.yaml                     # 配置文件
├── .env                            # 环境变量（需自行创建）
├── requirements.txt                # Python 依赖
├── README.md                       # 本文档
├── CLAUDE.md                       # Claude Code 项目指南
├── src/
│   ├── main.py                     # 主程序入口
│   ├── fetchers/                   # 论文采集器
│   │   ├── base.py                 # 抽象基类
│   │   ├── arxiv_fetcher.py        # arXiv RSS/API
│   │   └── biorxiv_fetcher.py      # bioRxiv/medRxiv API
│   ├── processors/                 # AI 处理
│   │   ├── ai_filter.py            # AI 相关性过滤
│   │   ├── embedding_filter.py     # OpenAI Embedding 过滤
│   │   ├── zhipu_embedding_filter.py # 智谱 AI Embedding 过滤
│   │   └── summarizer.py           # 论文总结
│   ├── formatters/                 # 消息格式化
│   │   └── feishu_formatter.py
│   └── utils/                      # 工具
│       ├── logger.py               # 彩色日志
│       ├── storage.py              # SQLite 存储
│       ├── pdf_downloader.py       # PDF 下载和文本提取
│       ├── math_utils.py           # 数学工具（余弦相似度）
│       └── claude_cli.py           # Claude CLI 工具
├── skills/                         # Claude Code Skills
│   ├── paper-relevance-judge/      # 论文相关性判断
│   │   └── SKILL.md
│   └── paper-summarizer/           # 论文总结
│       ├── SKILL.md
│       ├── skill.json
│       └── references/
│           └── EXAMPLES.md
├── scripts/
│   └── setup.sh                    # 初始化脚本
├── data/                           # 运行时数据 (git-ignored)
│   ├── briefings/                  # 早报 JSON 数据
│   ├── papers/                     # PDF 存储
│   │   ├── arxiv/
│   │   ├── biorxiv/
│   │   └── medrxiv/
│   └── briefings.db                # SQLite 数据库
└── logs/                           # 日志文件
```

## AI 过滤模式

系统支持 4 种过滤模式，**推荐使用 Claude 模式**：

### 1. Claude（推荐）
```
关键词初筛 → Claude CLI + paper-relevance-judge skill 判断
```
**最准确**，使用 Claude Code CLI 调用 skill 进行判断，准确率高且一致性好。

### 2. Hybrid
```
关键词初筛 → Embedding 相似度 → Claude CLI 判断
```
最严格，经过三层过滤，但速度较慢。

### 3. Embedding
```
关键词初筛 → Embedding 相似度判断
```
速度快，适合快速筛选，但准确率较低。

### 4. Keywords
```
仅关键词匹配
```
最快，但准确率最低，容易漏选或误选。

## Skills

系统使用两个自定义 Skills：

### paper-relevance-judge
判断论文是否与 "AI Agents for Scientific Research" 相关。

**判断标准**:
- Multi-agent systems 用于科研
- LLM agents 应用于科学计算/数据分析
- Agent 科研工作流自动化
- Agent 训练方法（需在科研任务上评估）

### paper-summarizer
生成结构化的中文论文总结。

**输出格式**:
- 研究问题
- 核心方法
- 关键结果（含具体数据）
- 应用场景

## 故障排查

### 1. Claude CLI 调用失败

```bash
# 检查 Claude Code CLI
which claude

# 测试 CLI
claude --version
```

### 2. PDF 下载失败

检查 `config.yaml` 中的 PDF 配置：
- `pdf_download.enabled: true`
- 确保 `data/papers/` 目录存在且可写

### 3. Embedding 过滤失败

```bash
# 检查智谱 AI API Key
echo $ZHIPU_API_KEY

# 或在 .env 中确认配置
cat .env | grep ZHIPU
```

## 数据存储

### SQLite 数据库

- **位置**: `data/briefings.db`
- **表**: `briefings`, `processed_papers`
- **自动维护**: 90 天数据保留，定期 VACUUM 和 REINDEX

### PDF 存储

- **位置**: `data/papers/{platform}/{paper_id}.pdf`
- **自动清理**: 处理完成后自动删除（可配置）

## 性能优化

- **分页采集**: arXiv 支持批量获取（batch_size=100）
- **并发处理**: ThreadPoolExecutor 并行处理（max_workers=2）
- **SQLite 索引**: 快速查重和查询
- **定期优化**: 自动 VACUUM 和 REINDEX

## 注意事项

1. **并行数限制**: `max_workers` 建议设为 2，过高会导致 Claude CLI 出现 "Execution error"
2. **网络连接**: 采集需要稳定的网络连接
3. **API 速率限制**: 注意平台 API 的调用频率限制

## 更新日志

### v2.1.0 (2026-02-24)
- 重构文档，修正与实际代码不一致的地方
- 更新项目结构和配置说明

### v2.0.0 (2026-02-23)
- 添加 paper-relevance-judge skill
- 支持 PDF 全文下载和处理
- 支持多种 AI 过滤模式 (hybrid/keywords/embedding/claude)
- SQLite 数据库存储
- 改进错误处理和日志记录

### v1.0.0 (2026-02-20)
- 初始版本
- 支持 arXiv、bioRxiv、medRxiv
- 基础的 AI 过滤和总结

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关资源

- [Claude Code CLI](https://claude.ai/code)
- [paper-relevance-judge Skill](skills/paper-relevance-judge/SKILL.md)
- [paper-summarizer Skill](skills/paper-summarizer/SKILL.md)
