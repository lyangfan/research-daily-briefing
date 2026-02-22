#!/usr/bin/env python3
"""
带详细调试的测试脚本
在终端运行: python3 test_with_debug.py
"""

import sys
import os
import subprocess
import csv
import feedparser
from datetime import datetime

sys.path.insert(0, '.')

# 导入 ai_filter
from src.processors.ai_filter import AIFilter

# 读取论文
papers = []
with open('embedding_results_36_new_query.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        url = row.get('URL', '')
        arxiv_id = url.replace('https://arxiv.org/abs/', '').replace('v1', '').replace('v2', '')
        papers.append({
            'rank': row.get('排名'),
            'similarity': row.get('相似度'),
            'embedding_pass': row.get('是否通过'),
            'title': row.get('标题'),
            'arxiv_id': arxiv_id,
            'url': url
        })

print(f"加载了 {len(papers)} 篇论文")

# 初始化
config = {'keywords': ['agent'], 'max_papers': 50}
ai_filter = AIFilter(config)
print(f"Skill 已加载: {len(ai_filter.skill_content)} 字符")
print()

# 测试前 3 篇论文
for i, paper in enumerate(papers[:3], 1):
    print("=" * 100)
    print(f"测试 [{i}] {paper['title']}")
    print("=" * 100)

    # 获取摘要
    try:
        url = f"http://export.arxiv.org/api/query?id_list={paper['arxiv_id']}"
        feed = feedparser.parse(url)
        abstract = feed.entries[0].get('summary', '') if feed.entries else ''
        print(f"摘要: {abstract[:200]}...")
    except Exception as e:
        print(f"获取摘要失败: {e}")
        continue

    # 直接调用 Claude CLI（不通过 ai_filter）
    skill_body = ai_filter.skill_content
    prompt = f"""{skill_body}

---

请判断以下论文是否与 AI Agents for Scientific Research 相关：

**论文标题**: {paper['title']}

**论文摘要**: {abstract}

请严格按照上述格式要求输出判断结果（Decision、Reasoning、Confidence）。"""

    result = subprocess.run(
        ['claude', '-p', prompt],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, 'CLAUDECODE': ''}
    )

    print()
    print("Claude 输出:")
    print("-" * 100)
    print(result.stdout)
    print("-" * 100)
    print()

    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        print()

    # 解析
    content = result.stdout.strip()
    content_lower = content.lower()

    print("解析结果:")
    if '**decision**' in content_lower:
        print("  ✓ 找到 '**decision**'")
        for line in content.split('\n'):
            if '**decision**' in line.lower():
                print(f"    行: '{line}'")
                line_clean = line.replace('*', '').replace(':', ' ').lower()
                words = line_clean.split()
                if 'yes' in words:
                    print(f"    ✓ 解析为 YES")
                elif 'no' in words:
                    print(f"    ✗ 解析为 NO")
                break
    else:
        print("  ✗ 没有找到 '**decision**'")
        # 检查其他格式
        if 'decision:' in content_lower:
            print("    但找到 'decision:'")
        if 'yes' in content_lower[:100]:
            print(f"    前 100 字符包含 'yes': {content_lower[:100]}")

    print()

print("=" * 100)
print("测试完成")
print("=" * 100)
