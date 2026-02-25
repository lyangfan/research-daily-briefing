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
mkdir -p data/briefings/briefings data/briefings/output data/papers logs
echo "✅ 目录结构创建完成"
echo

# 4. 设置脚本执行权限
echo "🔐 设置脚本执行权限..."
chmod +x scripts/*.sh
echo "✅ 权限设置完成"
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 初始化完成！"
echo
echo "📝 下一步:"
echo "  1. 编辑 .env 文件，填入 ZHIPU_API_KEY（可选）"
echo "  2. 测试消息格式: python3 src/main.py test"
echo "  3. 运行完整流程: python3 src/main.py run"
echo
