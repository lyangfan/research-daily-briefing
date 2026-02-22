# 科研早报自动化系统

每天自动从 arXiv、bioRxiv、medRxiv 等预印本平台获取最新论文，使用 AI 智能过滤出与「AI Agents for Scientific Research」相关的内容，生成中文总结并通过 OpenClaw 发送到飞书。

## 功能特点

- 🤖 **智能过滤**: 使用 paper-relevance-judge skill 判断论文相关性，支持多种过滤模式
- 📄 **PDF 全文处理**: 自动下载并提取 PDF 全文，生成包含具体数据的详细总结
- 📝 **中文总结**: 使用 paper-summarizer skill 生成结构化中文摘要
- 🔁 **自动去重**: SQLite 数据库存储，避免重复处理
- ⏰ **定时执行**: macOS launchd 定时任务，支持休眠唤醒
- 📊 **多平台支持**: arXiv, bioRxiv, medRxiv

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│ 你的 Mac (保持开盖，允许定时唤醒)                              │
│                                                             │
│  ⏰ launchd 定时任务 (每天 6:00 & 7:00)                      │
│     ↓                                                       │
│  📜 Python 脚本执行:                                         │
│     1. 从各平台采集新论文 (arXiv RSS/bioRxiv API)            │
│     2. 关键词初筛                                           │
│     3. Embedding/Skill 过滤相关性                           │
│     4. 下载 PDF 全文                                         │
│     5. Claude CLI 生成中文总结                              │
│     6. SQLite 存储去重                                       │
│     ↓                                                       │
│  🌐 OpenClaw Gateway (本地 127.0.0.1:18789)                 │
│     ↓                                                       │
│  📤 发送到飞书                                               │
└─────────────────────────────────────────────────────────────┘
```

## 安装步骤

### 1. 系统要求

- macOS 12+
- Python 3.9+
- OpenClaw Gateway (已安装并运行)
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
# OpenClaw 配置
OPENCLAW_GATEWAY_TOKEN=你的网关token
OPENCLAW_FEISHI_TARGET=你的飞书群ID或用户ID

# Zhipu AI (用于 Embedding，可选)
ZHIPU_API_KEY=你的智谱API密钥
```

**注意**: 本系统使用 **Claude Code CLI** 进行 AI 处理，不需要配置 ANTHROPIC_API_KEY。

### 4. 配置系统定时唤醒

```bash
# 允许定时事件唤醒系统
sudo pmset -b schedpowerevents 1

# 设置每天早上 5:55 自动唤醒
sudo pmset repeat wake MTWRFSU 05:55:00
```

### 5. 安装 launchd 定时任务

```bash
# 复制配置文件
cp launchd/com.research.briefing.fetch.plist ~/Library/LaunchAgents/
cp launchd/com.research.briefing.send.plist ~/Library/LaunchAgents/

# 加载任务
launchctl load ~/Library/LaunchAgents/com.research.briefing.fetch.plist
launchctl load ~/Library/LaunchAgents/com.research.briefing.send.plist
```

## 使用方法

### 完整流程（推荐，用于 OpenClaw）

```bash
# 完整流程：采集 → 处理 → 输出早报内容到 stdout
python3 src/main.py run

# 指定日期
python3 src/main.py run --date 2026-02-20
```

**说明**: `run` 命令会直接输出早报内容到标准输出，适合 OpenClaw 捕获并发送。

### 手动执行（调试用）

```bash
# 采集和处理论文（保存到数据库）
python3 src/main.py fetch

# 发送早报到飞书（需要配置 OpenClaw）
python3 src/main.py send

# 测试消息格式（不实际发送）
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

# 仅发送
python3 src/main.py send --date 2026-02-20
```

### 查看日志

```bash
# 采集日志
tail -f logs/fetch.log

# 发送日志
tail -f logs/send.log

# 错误日志
tail -f logs/fetch-error.log
tail -f logs/send-error.log
```

## 配置说明

### config.yaml

```yaml
# 平台配置
platforms:
  arxiv:
    enabled: true
    categories: [cs.AI, cs.CL, cs.LG, ...]
    batch_size: 100
  biorxiv:
    enabled: true

# AI 过滤配置
ai_filter:
  mode: "hybrid"              # hybrid | keywords | embedding | skill
  model: "claude-3-5-sonnet-20241022"
  max_papers: 30              # 每天最多处理多少篇
  max_summary_papers: 10       # 早报中最多包含多少篇

  # 过滤模式说明:
  # - hybrid: 关键词 → Embedding → Claude CLI 判断
  # - keywords: 仅关键词过滤
  # - embedding: 仅 Embedding 相似度
  # - skill: 使用 paper-relevance-judge skill

  keywords: [...]             # 初筛关键词

  embedding:
    enabled: true
    provider: "zhipu"        # openai | zhipu
    similarity_threshold: 0.50

# PDF 下载配置
pdf_download:
  enabled: true
  storage_dir: "data/papers"
  max_text_length: 30000     # 提取的最大文本长度

# 总结生成配置
summarizer:
  language: "zh-CN"
  single_paper_timeout: 600   # 单篇论文总结超时（秒）
  skill_path: "skills/paper-summarizer/SKILL.md"
```

## 项目结构

```
research-daily-briefing/
├── config.yaml                     # 配置文件
├── .env                            # 环境变量（需自行创建）
├── requirements.txt                # Python 依赖
├── README.md                       # 本文档
├── CLAUDE.md                       # Claude Code 项目指南
├── SKILL_TEST_SUMMARY.md           # Skill 测试总结
├── src/
│   ├── fetchers/                   # 论文采集器
│   │   ├── base.py
│   │   ├── arxiv_fetcher.py        # arXiv RSS (支持分页)
│   │   └── biorxiv_fetcher.py      # bioRxiv/medRxiv API
│   ├── processors/                 # AI 处理
│   │   ├── ai_filter.py            # AI 相关性过滤
│   │   ├── embedding_filter.py     # Embedding 相似度过滤
│   │   └── summarizer.py           # 论文总结
│   ├── formatters/                 # 消息格式化
│   │   └── feishu_formatter.py
│   ├── utils/                      # 工具
│   │   ├── logger.py
│   │   ├── storage.py              # SQLite 存储
│   │   └── pdf_downloader.py      # PDF 下载和文本提取
│   └── main.py                     # 主程序
├── skills/
│   ├── paper-relevance-judge/      # 论文相关性判断 Skill
│   │   └── SKILL.md
│   └── paper-summarizer/           # 论文总结 Skill
│       └── SKILL.md
├── scripts/
│   ├── setup.sh                    # 初始化脚本
│   ├── fetch_and_process.sh        # 采集脚本
│   └── send_briefing.sh            # 发送脚本
├── data/
│   ├── briefings/                  # 早报数据
│   ├── papers/                     # PDF 存储
│   └── briefings.db                # SQLite 数据库
├── logs/                           # 日志文件
└── launchd/                        # launchd 配置
```

## AI 过滤模式

系统支持 4 种过滤模式：

### 1. Hybrid（推荐）
```
关键词初筛 → Embedding 相似度 → Claude CLI 判断
```
最严格，准确率最高，适合生产环境。

### 2. Skill
```
关键词初筛 → paper-relevance-judge skill 判断
```
使用专门的 skill 进行判断，准确率高且一致性好。

### 3. Embedding
```
关键词初筛 → Embedding 相似度判断
```
速度快，适合快速筛选。

### 4. Keywords
```
仅关键词匹配
```
最快，但准确率较低。

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

### 1. 定时任务未执行

```bash
# 检查任务状态
launchctl list | grep research.briefing

# 查看任务日志
log show --predicate 'process == "research.briefing"' --last 1h
```

### 2. OpenClaw 发送失败

```bash
# 检查 OpenClaw Gateway 状态
openclaw gateway status

# 测试手动发送
openclaw message send --channel feishu --target "你的ID" --message "测试"
```

### 3. Claude CLI 调用失败

```bash
# 检查 Claude Code CLI
which claude

# 测试 CLI
claude --version
```

### 4. PDF 下载失败

检查 `config.yaml` 中的 PDF 配置：
- `pdf_download.enabled: true`
- 确保 `data/papers/` 目录存在且可写

## 数据存储

### SQLite 数据库

- **位置**: `data/briefings.db`
- **表**: `briefings`, `processed_papers`
- **自动维护**: 90 天数据保留，定期 VACUUM

### PDF 存储

- **位置**: `data/papers/{platform}/{paper_id}.pdf`
- **自动去重**: 避免重复下载

## 性能优化

- **分页采集**: arXiv 支持批量获取，减少 API 调用
- **并发处理**: PDF 下载可并发（需自行配置）
- **SQLite 索引**: 快速查重和查询
- **定期优化**: 自动 VACUUM 和 REINDEX

## 注意事项

1. **Mac 需保持开盖**: 合盖会导致系统休眠，定时任务无法执行
2. **允许定时唤醒**: 确保 `pmset` 配置正确
3. **OpenClaw Gateway 运行**: 网关需要在后台运行
4. **网络连接**: 采集需要稳定的网络连接
5. **API 速率限制**: 注意平台 API 的调用频率限制

## 更新日志

### v2.0.0 (2026-02-23)
- ✅ 添加 paper-relevance-judge skill
- ✅ 支持 PDF 全文下载和处理
- ✅ 支持多种 AI 过滤模式
- ✅ SQLite 数据库存储
- ✅ 改进错误处理和日志记录

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
- [OpenClaw Gateway](https://github.com/pandolia/openclaw)
- [paper-relevance-judge Skill](skills/paper-relevance-judge/SKILL.md)
- [SKILL_TEST_SUMMARY.md](SKILL_TEST_SUMMARY.md)
