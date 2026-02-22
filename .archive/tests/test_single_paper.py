#!/usr/bin/env python3
"""
测试单篇论文的判断
"""

import sys
import os
import subprocess

sys.path.insert(0, '.')

# 读取 skill
with open('skills/paper-relevance-judge/SKILL.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = 0
for i, line in enumerate(lines):
    if line.strip() == '---' and i > 0:
        start_idx = i + 1
        break

skill_body = ''.join(lines[start_idx:])

# 测试论文
title = "DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows"
abstract = "DataJoint 2.0 introduces a computational infrastructure designed for agentic scientific workflows, enabling LLM agents to automate research pipelines including data processing, experiment design, and result analysis."

prompt = f"""{skill_body}

---

请判断以下论文是否与 AI Agents for Scientific Research 相关：

**论文标题**: {title}

**论文摘要**: {abstract}

请严格按照上述格式要求输出判断结果（Decision、Reasoning、Confidence）。"""

print("=" * 100)
print("测试单篇论文判断")
print("=" * 100)
print()

# 运行 Claude CLI
result = subprocess.run(
    ['claude', '-p', prompt],
    capture_output=True,
    text=True,
    timeout=180,
    env={**os.environ, 'CLAUDECODE': ''}
)

print("Claude 输出:")
print(result.stdout)
print()

# 测试解析逻辑
content = result.stdout.strip()
content_lower = content.lower()

print("=" * 100)
print("解析测试")
print("=" * 100)
print()

# 检查 **decision**
if '**decision**' in content_lower:
    print("✓ 找到 '**decision**'")

    # 找到 Decision 行
    for line in content.split('\n'):
        if '**decision**' in line.lower():
            print(f"  Decision 行: '{line}'")

            # 清理并提取
            line_clean = line.replace('*', '').replace(':', ' ').lower()
            print(f"  清理后: '{line_clean}'")

            words = line_clean.split()
            print(f"  单词列表: {words}")

            if 'yes' in words:
                print("  ✓ 解析为 YES")
            elif 'no' in words:
                print("  ✗ 解析为 NO")
            break
else:
    print("✗ 没有找到 '**decision**'")
    print(f"  内容前 200 字符: {content[:200]}")
