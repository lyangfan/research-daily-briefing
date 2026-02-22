#!/usr/bin/env bash
#
# 发送早报脚本
# 每天 7:00 执行
#

set -euo pipefail

# 项目目录
PROJECT_DIR="/Users/liuyangfan/Documents/code/research-daily-briefing"
cd "$PROJECT_DIR"

# 日志
LOG_FILE="$PROJECT_DIR/logs/send.log"
ERROR_LOG="$PROJECT_DIR/logs/send-error.log"

# 飞书目标（从环境变量读取）
FEISHI_TARGET="${OPENCLAW_FEISHI_TARGET:-}"

if [ -z "$FEISHI_TARGET" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: 未设置 OPENCLAW_FEISHI_TARGET 环境变量" | tee -a "$ERROR_LOG"
    exit 1
fi

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始发送早报" | tee -a "$LOG_FILE"

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 执行发送
python3 src/main.py send 2>&1 | tee -a "$LOG_FILE"

# 检查执行结果
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 早报发送成功" | tee -a "$LOG_FILE"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 早报发送失败" | tee -a "$ERROR_LOG"

    # 发送错误通知到飞书
    ERROR_MSG="⚠️ 早报发送失败\n\n时间: $(date '+%Y-%m-%d %H:%M:%S')\n请检查日志获取详细信息"
    openclaw message send --channel feishu --target "$FEISHI_TARGET" --message "$ERROR_MSG" 2>/dev/null || true

    exit 1
fi
