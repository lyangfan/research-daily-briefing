#!/usr/bin/env python3
"""
稳定性测试 - 测试前 10 篇论文两次
在终端运行: python3 test_stability_10.py
"""

import sys
import os
import subprocess
import csv
import feedparser
from datetime import datetime

sys.path.insert(0, '.')
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

print("=" * 100)
print("稳定性测试 - 前 10 篇论文，运行两次")
print("=" * 100)
print()

# 初始化
config = {'keywords': ['agent'], 'max_papers': 50}
ai_filter = AIFilter(config)

# 测试前 10 篇
test_papers = papers[:10]

# 获取摘要
for paper in test_papers:
    try:
        url = f"http://export.arxiv.org/api/query?id_list={paper['arxiv_id']}"
        feed = feedparser.parse(url)
        paper['abstract'] = feed.entries[0].get('summary', '') if feed.entries else ''
    except:
        paper['abstract'] = ''

# 运行两次
results_run1 = []
results_run2 = []

for run_num, results_list in enumerate([results_run1, results_run2], 1):
    print(f"第 {run_num} 次运行...")
    print("-" * 100)

    for i, paper in enumerate(test_papers, 1):
        try:
            paper_data = {
                'id': paper['arxiv_id'],
                'title': paper['title'],
                'abstract': paper['abstract'],
                'url': paper['url']
            }

            is_relevant = ai_filter._check_relevance(paper_data)
            decision = "YES" if is_relevant else "NO"
            symbol = "✓" if is_relevant else "✗"

            rank_val = paper.get('rank') or str(i)
            print(f"[{rank_val:>2}] {symbol} {decision:3} | {paper['title'][:55]}")
            results_list.append({
                'rank': rank_val,
                'title': paper['title'],
                'decision': decision
            })
        except Exception as e:
            rank_val = paper.get('rank') or str(i)
            print(f"[{rank_val:>2}] ? ERR | {paper['title'][:55]} ({str(e)[:30]})")
            results_list.append({
                'rank': rank_val,
                'title': paper['title'],
                'decision': 'ERROR'
            })
    print()

# 对比结果
print("=" * 100)
print("稳定性对比")
print("=" * 100)
print()

stable_count = 0
unstable_count = 0

for i in range(len(test_papers)):
    r1 = results_run1[i]
    r2 = results_run2[i]

    if r1['decision'] == r2['decision']:
        stable_count += 1
        symbol = "✓"
    else:
        unstable_count += 1
        symbol = "✗"

    r1_rank = r1.get('rank') or str(i+1)
    print(f"{symbol} [{r1_rank}] Run1: {r1['decision']:3} | Run2: {r2['decision']:3} | {r1['title'][:50]}")

print()
print("=" * 100)
print(f"稳定性: {stable_count}/10 = {stable_count*10}% 一致")
print(f"不稳定: {unstable_count}/10 = {unstable_count*10}% 不一致")
print("=" * 100)
