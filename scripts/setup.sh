#!/usr/bin/env bash
#
# 初始化和设置脚本
#

set -euo pipefail

PROJECT_DIR="/Users/liuyangfan/Documents/code/research-daily-briefing"
cd "$PROJECT_DIR"

echo "🚀 科研早报系统 - 初始化设置"
echo

# 1. 创建 .env 文件
if [ ! -f .env ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo "✅ .env 文件已创建"
    echo "⚠️  请编辑 .env 文件，填入你的 API Keys 和配置"
    echo
else
    echo "✅ .env 文件已存在"
fi

# 2. 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip3 install -r requirements.txt || {
    echo "❌ 依赖安装失败"
    exit 1
}
echo "✅ 依赖安装完成"
echo

# 3. 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p data/briefings logs launchd
echo "✅ 目录结构创建完成"
echo

# 4. 设置脚本执行权限
echo "🔐 设置脚本执行权限..."
chmod +x scripts/*.sh
echo "✅ 权限设置完成"
echo

# 5. 配置 pmset 定时唤醒
echo "⏰ 配置系统定时唤醒..."
echo "当前 pmset 设置:"
pmset -g
echo
echo "建议执行以下命令启用定时唤醒:"
echo "  sudo pmset -b schedpowerevents 1"
echo "  sudo pmset repeat wake MTWRFSU 05:55:00"
echo

# 6. 安装 launchd 服务
echo "📋 安装 launchd 定时任务..."
read -p "是否安装 launchd 定时任务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 创建 launchd 配置文件
    cat > launchd/com.research.briefing.fetch.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.research.briefing.fetch</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$PROJECT_DIR/scripts/fetch_and_process.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/fetch.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/fetch-error.log</string>
</dict>
</plist>
EOF

    cat > launchd/com.research.briefing.send.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.research.briefing.send</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$PROJECT_DIR/scripts/send_briefing.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/send.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/send-error.log</string>
</dict>
</plist>
EOF

    # 复制到 LaunchAgents 目录
    cp launchd/com.research.briefing.fetch.plist ~/Library/LaunchAgents/
    cp launchd/com.research.briefing.send.plist ~/Library/LaunchAgents/

    # 加载服务
    launchctl load ~/Library/LaunchAgents/com.research.briefing.fetch.plist
    launchctl load ~/Library/LaunchAgents/com.research.briefing.send.plist

    echo "✅ launchd 任务已安装并加载"
    echo
    echo "已安装的任务:"
    echo "  - com.research.briefing.fetch (每天 6:00)"
    echo "  - com.research.briefing.send (每天 7:00)"
    echo
    echo "查看任务状态:"
    echo "  launchctl list | grep research.briefing"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 初始化完成！"
echo
echo "📝 下一步:"
echo "  1. 编辑 .env 文件，填入必要的配置"
echo "  2. 运行测试: python3 src/main.py test"
echo "  3. 测试采集: python3 src/main.py fetch --days-back 3"
echo "  4. 手动发送: python3 src/main.py send"
echo
