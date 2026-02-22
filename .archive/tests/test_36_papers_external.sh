#!/bin/bash
# 在外部终端运行此脚本进行测试
# 使用方法: bash test_36_papers_external.sh

cd /Users/liuyangfan/Documents/code/research-daily-briefing

# 确保没有 CLAUDECODE 环境变量
unset CLAUDECODE

echo "开始测试 36 篇论文..."
echo "开始时间: $(date)"
echo ""

python3 -u test_36_papers_with_skill.py 2>&1 | tee test_36_skill_external.log

echo ""
echo "完成时间: $(date)"
echo "结果已保存到: skill_filter_results_36_*.csv"
