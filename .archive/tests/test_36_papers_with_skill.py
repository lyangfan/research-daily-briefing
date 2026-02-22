#!/usr/bin/env python3
"""
使用 paper-relevance-judge skill 重新测试 36 篇论文
"""

import sys
import os
import subprocess
import csv
import time
from datetime import datetime

sys.path.insert(0, '.')

# 36 篇论文 - 读取之前的 CSV 并获取完整摘要
import feedparser

CSV_FILE = "embedding_results_36_new_query.csv"

def load_papers_from_csv():
    """从 CSV 加载论文信息"""
    papers = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 提取 arXiv ID
            url = row.get('URL', '')
            arxiv_id = url.replace('https://arxiv.org/abs/', '').replace('v1', '').replace('v2', '')

            papers.append({
                'rank': row.get('排名'),
                'similarity': row.get('相似度'),
                'embedding_pass': row.get('是否通过'),
                'title': row.get('标题'),
                'authors': row.get('作者'),
                'platform': row.get('平台'),
                'url': url,
                'arxiv_id': arxiv_id
            })
    return papers

def fetch_abstract(arxiv_id: str) -> str:
    """从 arXiv 获取论文摘要"""
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        feed = feedparser.parse(url)

        if feed.entries:
            return feed.entries[0].get('summary', '').replace('\n', ' ')
    except Exception as e:
        print(f"        ⚠️  获取摘要失败: {e}")
    return ""

def judge_with_claude(title: str, abstract: str, claude_path: str) -> tuple:
    """使用 Claude CLI 判断相关性"""
    # 读取 skill
    skill_path = "skills/paper-relevance-judge/SKILL.md"
    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    # 跳过 YAML
    lines = skill_content.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            start_idx = i + 1
            break
    skill_body = '\n'.join(lines[start_idx:])

    # 构建 prompt
    prompt = f"""{skill_body}

---

请判断以下论文是否与 AI Agents for Scientific Research 相关：

**论文标题**: {title}

**论文摘要**: {abstract}

请严格按照上述格式要求输出判断结果（Decision、Reasoning、Confidence）。"""

    # 调用 Claude
    result = subprocess.run(
        [claude_path, '-p', prompt, '--max-turns', '1'],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, 'CLAUDECODE': ''}
    )

    if result.returncode == 0:
        content = result.stdout.strip()

        # 解析 Decision
        content_lower = content.lower()
        if 'decision:' in content_lower:
            decision_line = [line for line in content_lower.split('\n') if 'decision:' in line]
            if decision_line:
                decision_value = decision_line[0].split('decision:')[1].strip()
                is_yes = decision_value.startswith('yes')

                # 提取 reasoning
                reasoning_lines = [line for line in content.split('\n') if 'reasoning:' in line.lower()]
                reasoning = reasoning_lines[0].split('reasoning:')[1].strip() if reasoning_lines else ''

                # 提取 confidence
                confidence_lines = [line for line in content_lower.split('\n') if 'confidence:' in line]
                confidence = confidence_lines[0].split('confidence:')[1].strip() if confidence_lines else ''

                return is_yes, reasoning, confidence

        # 降级判断
        return 'yes' in content_lower or '相关' in content_lower, '', ''
    else:
        return None, result.stderr, ''

def main():
    print("=" * 100)
    print("使用 paper-relevance-judge skill 重新测试 36 篇论文")
    print("=" * 100)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 查找 claude
    claude_path = "/usr/local/bin/claude"
    if not os.path.exists(claude_path):
        claude_path = os.path.expanduser("~/.local/bin/claude")

    if not os.path.exists(claude_path):
        print("❌ 找不到 Claude Code CLI")
        return

    print(f"✅ Claude Code: {claude_path}")
    print()

    # 加载论文
    papers = load_papers_from_csv()
    print(f"✅ 加载了 {len(papers)} 篇论文")
    print()

    # 结果存储
    results = []
    start_time = time.time()

    for i, paper in enumerate(papers, 1):
        elapsed = time.time() - start_time
        avg_time = elapsed / i if i > 0 else 0
        remaining = avg_time * (len(papers) - i)

        print(f"[{i}/36] {paper['title'][:50]}... | 预计剩余: {int(remaining)}s", end='', flush=True)

        # 获取摘要
        abstract = fetch_abstract(paper['arxiv_id'])
        if not abstract:
            print(" ⚠️  无摘要")
            results.append({**paper, 'skill_decision': 'ERROR', 'skill_reasoning': '无摘要', 'skill_confidence': ''})
            continue

        # 判断
        try:
            is_relevant, reasoning, confidence = judge_with_claude(paper['title'], abstract, claude_path)

            if is_relevant is None:
                print(f" ❌ CLI错误")
                results.append({**paper, 'skill_decision': 'ERROR', 'skill_reasoning': reasoning[:100], 'skill_confidence': ''})
            else:
                decision = "YES" if is_relevant else "NO"
                symbol = "✓" if is_relevant else "✗"
                print(f" {symbol} {decision}" + (f" ({confidence})" if confidence else ""))
                results.append({**paper, 'skill_decision': decision, 'skill_reasoning': reasoning[:100], 'skill_confidence': confidence})

        except subprocess.TimeoutExpired:
            print(" ⏱️  超时")
            results.append({**paper, 'skill_decision': 'ERROR', 'skill_reasoning': '超时', 'skill_confidence': ''})
        except Exception as e:
            print(f" ❌ {str(e)[:50]}")
            results.append({**paper, 'skill_decision': 'ERROR', 'skill_reasoning': str(e)[:100], 'skill_confidence': ''})

    # 保存结果
    output_file = f"skill_filter_results_36_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['rank', 'arxiv_id', 'title', 'embedding_sim', 'embedding_pass', 'skill_decision', 'skill_confidence', 'skill_reasoning']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            writer.writerow({
                'rank': r['rank'],
                'arxiv_id': r['arxiv_id'],
                'title': r['title'],
                'embedding_sim': r['similarity'],
                'embedding_pass': r['embedding_pass'],
                'skill_decision': r['skill_decision'],
                'skill_confidence': r.get('skill_confidence', ''),
                'skill_reasoning': r.get('skill_reasoning', '')
            })

    print()
    print("=" * 100)
    print("测试完成")
    print("=" * 100)
    print(f"结果保存到: {output_file}")
    print()

    # 对比统计
    emb_pass = sum(1 for r in results if r['embedding_pass'] == 'True')
    skill_pass = sum(1 for r in results if r['skill_decision'] == 'YES')

    print("对比统计:")
    print(f"  Embedding 通过: {emb_pass}/36 ({emb_pass/36*100:.1f}%)")
    print(f"  Skill 通过:     {skill_pass}/36 ({skill_pass/36*100:.1f}%)")

    # 详细对比 - 应该通过但 embedding 没通过的
    should_pass_emb_no = [r for r in results if r['skill_decision'] == 'YES' and r['embedding_pass'] == 'False']
    print()
    print(f"Skill 通过但 Embedding 未通过 ({len(should_pass_emb_no)} 篇):")
    for r in should_pass_emb_no:
        print(f"  [{r['rank']}] {r['title'][:60]} (sim={r['embedding_sim']})")

    # 应该不通过但 embedding 通过的
    should_not_pass_emb_yes = [r for r in results if r['skill_decision'] == 'NO' and r['embedding_pass'] == 'True']
    print()
    print(f"Skill 不通过但 Embedding 通过 ({len(should_not_pass_emb_yes)} 篇):")
    for r in should_not_pass_emb_yes:
        print(f"  [{r['rank']}] {r['title'][:60]} (sim={r['embedding_sim']})")

if __name__ == "__main__":
    main()
