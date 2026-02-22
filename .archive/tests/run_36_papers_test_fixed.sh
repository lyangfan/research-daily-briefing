#!/bin/bash
# 修复后的测试脚本
# 在外部终端运行: bash run_36_papers_test_fixed.sh

set -e

cd "$(dirname "$0")"
unset CLAUDECODE

echo "===================================================================================================="
echo "使用修复后的 paper-relevance-judge skill 重新测试 36 篇论文"
echo "===================================================================================================="
echo "开始时间: $(date)"
echo ""

python3 -u << 'PYTHON_SCRIPT'
import sys
import os
import subprocess
import csv
import time
from datetime import datetime
import feedparser

# 导入修复后的 ai_filter
sys.path.insert(0, '.')
from src.processors.ai_filter import AIFilter

# 读取之前的 CSV
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

print(f"✅ 加载了 {len(papers)} 篇论文")

# 初始化 AI Filter
config = {
    'keywords': ['multi-agent', 'AI agent', 'LLM agent', 'autonomous agent'],
    'max_papers': 50
}

ai_filter = AIFilter(config)
print(f"✅ Skill 已加载: {len(ai_filter.skill_content)} 字符")
print(f"✅ Claude Code: {ai_filter.claude_path}")
print()

# 函数：获取摘要
def get_abstract(arxiv_id):
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        feed = feedparser.parse(url)
        if feed.entries:
            return feed.entries[0].get('summary', '').replace('\n', ' ')
    except:
        pass
    return ""

# 处理论文
results = []
start_time = time.time()

for i, paper in enumerate(papers, 1):
    elapsed = time.time() - start_time
    avg = elapsed / i if i > 0 else 0
    remain = avg * (len(papers) - i)

    print(f"[{i}/36] {paper['title'][:55]}... | 预计剩余: {int(remain)}s", end='', flush=True)

    abstract = get_abstract(paper['arxiv_id'])
    if not abstract:
        print(" ⚠️  无摘要")
        results.append({**paper, 'skill_decision': 'ERROR', 'reasoning': '无摘要'})
        continue

    try:
        paper_data = {
            'id': paper['arxiv_id'],
            'title': paper['title'],
            'abstract': abstract,
            'url': paper['url']
        }

        is_relevant = ai_filter._check_relevance(paper_data)

        if is_relevant:
            print(" ✓ YES")
            results.append({**paper, 'skill_decision': 'YES', 'reasoning': 'Pass'})
        else:
            print(" ✗ NO")
            results.append({**paper, 'skill_decision': 'NO', 'reasoning': 'Fail'})

    except subprocess.TimeoutExpired:
        print(" ⏱️  超时")
        results.append({**paper, 'skill_decision': 'ERROR', 'reasoning': '超时'})
    except Exception as e:
        print(f" ❌ {str(e)[:50]}")
        results.append({**paper, 'skill_decision': 'ERROR', 'reasoning': str(e)[:100]})

    time.sleep(0.3)

# 保存结果
output_file = f"skill_vs_embedding_36_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Rank', 'arXiv ID', 'Title', 'Emb_Sim', 'Emb_Pass', 'Skill_Decision', 'Reasoning'])
    for r in results:
        writer.writerow([
            r['rank'], r['arxiv_id'], r['title'],
            r['similarity'], r['embedding_pass'],
            r['skill_decision'], r.get('reasoning', '')
        ])

print()
print("=" * 100)
print("测试完成")
print("=" * 100)
print(f"结果: {output_file}")
print()

# 统计
emb_pass = sum(1 for r in results if r['embedding_pass'] == 'True')
skill_pass = sum(1 for r in results if r['skill_decision'] == 'YES')

print("对比:")
print(f"  Embedding: {emb_pass}/36 通过 ({emb_pass/36*100:.1f}%)")
print(f"  Skill:     {skill_pass}/36 通过 ({skill_pass/36*100:.1f}%)")

# 对比分析
yes_emb_no = [r for r in results if r['skill_decision'] == 'YES' and r['embedding_pass'] == 'False']
no_emb_yes = [r for r in results if r['skill_decision'] == 'NO' and r['embedding_pass'] == 'True']

print()
print(f"Skill ✓ 但 Embedding ✗ ({len(yes_emb_no)} 篇):")
for r in yes_emb_no[:10]:
    print(f"  [{r['rank']}] {r['title'][:70]} (sim={r['similarity']})")

print()
print(f"Skill ✗ 但 Embedding ✓ ({len(no_emb_yes)} 篇):")
for r in no_emb_yes[:10]:
    print(f"  [{r['rank']}] {r['title'][:70]} (sim={r['similarity']})")

PYTHON_SCRIPT

echo ""
echo "完成时间: $(date)"
