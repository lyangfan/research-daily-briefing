#!/usr/bin/env bash
#
# 采集和处理脚本
# 每天 6:00 执行
#

set -euo pipefail

# 项目目录
PROJECT_DIR="/Users/liuyangfan/Documents/code/research-daily-briefing"
cd "$PROJECT_DIR"

# 日志
LOG_FILE="$PROJECT_DIR/logs/fetch.log"
ERROR_LOG="$PROJECT_DIR/logs/fetch-error.log"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始采集和处理论文" | tee -a "$LOG_FILE"

# 激活虚拟环境（如果使用）
# source venv/bin/activate

# 执行采集和处理
python3 src/main.py fetch 2>&1 | tee -a "$LOG_FILE"

# 检查执行结果
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 采集和处理完成" | tee -a "$LOG_FILE"
    exit 0
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 采集和处理失败" | tee -a "$ERROR_LOG"
    exit 1
fi
