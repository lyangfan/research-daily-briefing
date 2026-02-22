#!/bin/bash
# 稳定性测试 - 运行两次并对比结果

set -e

cd "$(dirname "$0")"
unset CLAUDECODE

echo "===================================================================================================="
echo "稳定性测试 - 运行两次对比"
echo "===================================================================================================="
echo ""

# 第一次运行
echo "第一次运行..."
python3 -u << 'PYTHON_SCRIPT' > test_run1.txt 2>&1 &
PID1=$!
PYTHON_SCRIPT

# 等待第一次完成
wait $PID1

# 第二次运行
echo "第二次运行..."
python3 -u << 'PYTHON_SCRIPT' > test_run2.txt 2>&1 &
PID2=$!
PYTHON_SCRIPT

# 等待第二次完成
wait $PID2

# 对比结果
echo ""
echo "===================================================================================================="
echo "对比结果"
echo "===================================================================================================="
echo ""

# 提取 YES 的论文
grep "✓ YES" test_run1.txt | wc -l
grep "✓ YES" test_run2.txt | wc -l

echo "差异:"
diff test_run1.txt test_run2.txt || true

echo ""
echo "完成"
