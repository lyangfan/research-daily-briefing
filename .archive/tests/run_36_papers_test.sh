#!/bin/bash
# 此脚本需要在新的终端窗口中运行
# 用法: bash run_36_papers_test.sh

set -e

cd "$(dirname "$0")"

# 确保没有 CLAUDECODE 环境变量
unset CLAUDECODE

echo "===================================================================================================="
echo "使用 paper-relevance-judge skill 重新测试 36 篇论文"
echo "===================================================================================================="
echo "开始时间: $(date)"
echo ""

# 检查 claude CLI
if ! command -v claude &> /dev/null; then
    echo "❌ 找不到 claude 命令"
    exit 1
fi

echo "✅ Claude Code: $(which claude)"
echo ""

# 运行 Python 测试脚本
python3 -u << 'PYTHON_SCRIPT'
import sys
import os
import subprocess
import csv
import time
from datetime import datetime
import feedparser

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
print()

# 读取 skill
with open('skills/paper-relevance-judge/SKILL.md', 'r', encoding='utf-8') as f:
    skill_content = f.read()

lines = skill_content.split('\n')
start_idx = 0
for i, line in enumerate(lines):
    if line.strip() == '---' and i > 0:
        start_idx = i + 1
        break
skill_body = '\n'.join(lines[start_idx:])

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

# 函数：判断相关性
def judge_paper(title, abstract):
    prompt = f"""{skill_body}

---

请判断以下论文是否与 AI Agents for Scientific Research 相关：

**论文标题**: {title}

**论文摘要**: {abstract}

请严格按照上述格式要求输出判断结果（Decision、Reasoning、Confidence）。"""

    result = subprocess.run(
        ['claude', '-p', prompt, '--max-turns', '1'],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, 'CLAUDECODE': ''}
    )

    if result.returncode != 0:
        return None, result.stderr or "CLI error"

    content = result.stdout.strip()

    # 解析 Decision
    content_lower = content.lower()
    if 'decision:' in content_lower:
        for line in content_lower.split('\n'):
            if 'decision:' in line:
                decision = line.split('decision:')[1].strip()
                is_yes = decision.startswith('yes')

                # 提取 reasoning
                reasoning = ""
                for l in content.split('\n'):
                    if 'reasoning:' in l.lower():
                        reasoning = l.split('reasoning:')[1].strip()
                        break

                # 提取 confidence
                confidence = ""
                for l in content_lower.split('\n'):
                    if 'confidence:' in l:
                        confidence = l.split('confidence:')[1].strip()
                        break

                return is_yes, f"{reasoning[:100]} | {confidence}"

    # 降级判断
    if 'yes' in content_lower or '相关' in content_lower or '✓' in content:
        return True, "Keyword match"
    return False, "No decision found"

# 处理论文
results = []
start_time = time.time()

for i, paper in enumerate(papers, 1):
    elapsed = time.time() - start_time
    avg = elapsed / i
    remain = avg * (len(papers) - i)

    print(f"[{i}/36] {paper['title'][:55]}... | 预计剩余: {int(remain)}s", end='', flush=True)

    abstract = get_abstract(paper['arxiv_id'])
    if not abstract:
        print(" ⚠️  无摘要")
        results.append({**paper, 'skill_decision': 'ERROR', 'reasoning': '无摘要'})
        continue

    try:
        is_relevant, reasoning = judge_paper(paper['title'], abstract)
        if is_relevant is None:
            print(f" ❌ {reasoning[:50]}")
            results.append({**paper, 'skill_decision': 'ERROR', 'reasoning': reasoning[:100]})
        else:
            decision = "YES" if is_relevant else "NO"
            symbol = "✓" if is_relevant else "✗"
            print(f" {symbol} {decision}")
            results.append({**paper, 'skill_decision': decision, 'reasoning': reasoning})
    except subprocess.TimeoutExpired:
        print(" ⏱️  超时")
        results.append({**paper, 'skill_decision': 'ERROR', 'reasoning': '超时'})
    except Exception as e:
        print(f" ❌ {str(e)[:50]}")
        results.append({**paper, 'skill_decision': 'ERROR', 'reasoning': str(e)[:100]})

    time.sleep(0.3)

# 保存结果
output_file = f"skill_vs_embedding_36_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
for r in yes_emb_no[:5]:
    print(f"  [{r['rank']}] {r['title'][:60]} (sim={r['similarity']})")

print()
print(f"Skill ✗ 但 Embedding ✓ ({len(no_emb_yes)} 篇):")
for r in no_emb_yes[:5]:
    print(f"  [{r['rank']}] {r['title'][:60]} (sim={r['similarity']})")

PYTHON_SCRIPT

echo ""
echo "完成时间: $(date)"
