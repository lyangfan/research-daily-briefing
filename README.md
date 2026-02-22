# 科研早报自动化系统

每天自动从 arXiv、bioRxiv、medRxiv 等预印本平台获取最新论文，使用 Claude AI 智能过滤出与「科研相关的 AI Agent」相关的内容，生成中文总结并通过 OpenClaw 发送到飞书。

## 功能特点

- 🤖 **智能过滤**: 使用 Claude Code CLI 判断论文相关性
- 📝 **中文总结**: 使用 Claude Code CLI 生成中文摘要，突出研究问题、方法创新和关键结果
- 🔁 **自动去重**: 避免重复处理已读论文
- ⏰ **定时执行**: 每天早上 6:00 采集，7:00 发送
- 🚨 **错误通知**: 失败时自动发送通知到飞书
- 📊 **多平台支持**: arXiv, bioRxiv, medRxiv, SSRN

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│ 你的 Mac (保持开盖，允许定时唤醒)                              │
│                                                             │
│  ⏰ launchd 定时任务 (每天 6:00 & 7:00)                      │
│     ↓                                                       │
│  📜 Python 脚本执行:                                         │
│     - 从各平台采集新论文                                     │
│     - Claude AI 过滤 & 总结                                  │
│     - 调用 OpenClaw CLI 发送                                 │
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

### 手动执行

```bash
# 采集和处理论文
python3 src/main.py fetch

# 发送早报到飞书
python3 src/main.py send

# 测试（不实际发送）
python3 src/main.py test

# 查看统计信息
python3 src/main.py stats

# 清理旧数据
python3 src/main.py cleanup
```

### 指定日期

```bash
# 获取指定日期的论文
python3 src/main.py fetch --date 2026-02-20

# 发送指定日期的早报
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
  biorxiv:
    enabled: true

# AI 过滤配置
ai_filter:
  max_papers: 30          # 每天最多处理多少篇
  max_summary_papers: 10  # 早报中最多包含多少篇
  keywords: [...]         # 初筛关键词

# OpenClaw 配置
openclaw:
  feishi_target: ""       # 飞书目标ID
  send_time: "07:00"
```

## 项目结构

```
research-daily-briefing/
├── config.yaml                     # 配置文件
├── .env                            # 环境变量（需自行创建）
├── requirements.txt                # Python 依赖
├── README.md                       # 本文档
├── src/
│   ├── fetchers/                   # 论文采集器
│   │   ├── arxiv_fetcher.py
│   │   └── biorxiv_fetcher.py
│   ├── processors/                 # AI 处理
│   │   ├── ai_filter.py
│   │   └── summarizer.py
│   ├── formatters/                 # 消息格式化
│   │   └── feishu_formatter.py
│   ├── utils/                      # 工具
│   │   ├── logger.py
│   │   └── storage.py
│   └── main.py                     # 主程序
├── scripts/
│   ├── setup.sh                    # 初始化脚本
│   ├── fetch_and_process.sh        # 采集脚本
│   └── send_briefing.sh            # 发送脚本
├── data/
│   └── briefings/                  # 早报数据
├── logs/                           # 日志文件
└── launchd/                        # launchd 配置
```

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

### 3. API 调用失败

检查 `.env` 文件中的 API Key 是否正确，以及网络连接是否正常。

## 注意事项

1. **Mac 需保持开盖**: 合盖会导致系统休眠，定时任务无法执行
2. **允许定时唤醒**: 确保 `pmset` 配置正确
3. **OpenClaw Gateway 运行**: 网关需要在后台运行（已安装自愈服务）
4. **API 配额**: 注意 Claude API 的调用配额

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
