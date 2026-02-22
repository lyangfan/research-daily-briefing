#!/usr/bin/env python3
"""
测试 KLong 论文的稳定性
"""

import sys
import subprocess
import feedparser

sys.path.insert(0, '.')
from src.processors.ai_filter import AIFilter

# 读取 skill
config = {'keywords': ['agent'], 'max_papers': 50}
ai_filter = AIFilter(config)

# KLong 论文
arxiv_id = "2602.17547"
title = "KLong: Training LLM Agent for Extremely Long-horizon Tasks"

# 获取摘要
try:
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    feed = feedparser.parse(url)
    abstract = feed.entries[0].get('summary', '') if feed.entries else ''
except:
    abstract = ''

print("=" * 100)
print("测试 KLong 论文稳定性（运行 5 次）")
print("=" * 100)
print()
print(f"标题: {title}")
print(f"摘要: {abstract[:300]}...")
print()

results = []
for i in range(5):
    paper_data = {
        'id': arxiv_id,
        'title': title,
        'abstract': abstract,
        'url': f"https://arxiv.org/abs/{arxiv_id}"
    }

    is_relevant = ai_filter._check_relevance(paper_data)
    decision = "YES" if is_relevant else "NO"
    symbol = "✓" if is_relevant else "✗"

    results.append(decision)
    print(f"[{i+1}/5] {symbol} {decision}")

yes_count = sum(1 for r in results if r == "YES")
no_count = sum(1 for r in results if r == "NO")

print()
print("=" * 100)
if yes_count == 5:
    print("✓ 稳定：总是 YES")
elif no_count == 5:
    print("✓ 稳定：总是 NO")
else:
    print(f"✗ 不稳定：YES {yes_count}/5, NO {no_count}/5")
print("=" * 100)
