#!/usr/bin/env python3
"""
调试 Claude CLI 输出格式
在终端运行: python3 debug_claude_output.py
"""

import subprocess
import os

# 读取 skill 并跳过 YAML frontmatter
with open('skills/paper-relevance-judge/SKILL.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 跳过第一个 --- 之前的内容，找到第二个 ---
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
print("调试 Claude CLI 输出格式")
print("=" * 100)
print()
print(f"Skill 长度: {len(skill_body)} 字符")
print(f"Prompt 长度: {len(prompt)} 字符")
print()
print("=" * 100)
print("Claude 输出:")
print("=" * 100)
print()

# 运行 Claude CLI（不使用 --max-turns）
result = subprocess.run(
    ['claude', '-p', prompt],
    capture_output=True,
    text=True,
    timeout=180,
    env={**os.environ, 'CLAUDECODE': ''}
)

print("STDOUT:")
print(result.stdout)
print()

if result.stderr:
    print("STDERR:")
    print(result.stderr)
    print()

print("=" * 100)
print("解析测试:")
print("=" * 100)
print()

# 测试解析逻辑
content = result.stdout.strip()
content_lower = content.lower()

print(f"输出长度: {len(content)} 字符")
print()

# 检查是否包含 Decision
if 'decision:' in content_lower:
    print("✅ 找到 'decision:' 关键字")
    for line in content_lower.split('\n'):
        if 'decision:' in line:
            decision_value = line.split('decision:')[1].strip()
            print(f"   Decision 值: '{decision_value}'")
            print(f"   是 YES? {decision_value.startswith('yes')}")
            break
else:
    print("❌ 没有找到 'decision:' 关键字")

# 检查其他可能的关键字
checks = [
    ('yes', 'yes 关键字'),
    ('no', 'no 关键字'),
    ('相关', '中文"相关"'),
    ('不相关', '中文"不相关"'),
    ('decision', 'decision 关键字（大小写敏感）'),
]

for keyword, desc in checks:
    if keyword in content_lower or keyword in content:
        print(f"✓ 找到: {desc}")

print()
print("=" * 100)
print(f"完整输出（原始）:")
print("=" * 100)
print(repr(content[:500]))
