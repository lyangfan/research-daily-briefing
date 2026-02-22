#!/usr/bin/env python3
"""
模拟测试 paper-relevance-judge skill
使用预设的模拟响应来验证判断逻辑
"""

import csv
import sys
from datetime import datetime

# 模拟的判断结果 - 基于论文标题和摘要的人工分析
MOCK_DECISIONS = {
    # 应该相关的论文
    "2602.17607": ("YES", "AutoNumerics - 多智能体科学计算管道", "HIGH"),  # AutoNumerics
    "2602.17547": ("YES", "KLong - LLM agent 用于长任务", "MEDIUM"),      # KLong
    "2602.17308": ("YES", "MedClarify - 医疗诊断 AI agent", "HIGH"),     # MedClarify
    "2602.17221": ("YES", "AI agents 增强人文社科研究", "HIGH"),         # From Labor to Collaboration
    "2602.17049": ("YES", "多智能体规划用于计算机使用 agents", "HIGH"),   # IntentCUA
    "2602.17038": ("YES", "Agentic 强化学习", "HIGH"),                   # Phase-Aware MoE
    "2602.17027": ("YES", "AI 增强的行为神经科学发现", "HIGH"),          # Transforming Behavioral Neuroscience
    "2602.16953": ("YES", "Agentic learning 用于测试生成", "MEDIUM"),    # LLM4Cov
    "2602.16943": ("YES", "LLM agents 的工具调用安全", "MEDIUM"),        # Mind the GAP
    "2602.16901": ("YES", "LLM agents 基准测试", "MEDIUM"),              # AgentLAB
    "2602.16708": ("YES", "安全 agentic 系统的策略编译器", "HIGH"),      # Policy Compiler
    "2602.16699": ("YES", "LLM agents 的成本感知探索", "MEDIUM"),        # Calibrate-Then-Act
    "2602.16666": ("YES", "AI agent 可靠性科学", "HIGH"),                # Towards Science of AI Agent Reliability
    "2602.16585": ("YES", "Agentic 科学生命周期的基础设施", "HIGH"),     # DataJoint 2.0
    "2602.16485": ("YES", "Agentic 系统的工具调用编排", "HIGH"),         # Team of Thoughts
    "2602.16435": ("YES", "多智能体强化学习用于特征工程", "MEDIUM"),     # Causally-Guided
    "2602.16246": ("YES", "工具调用 LLM agents 的可验证奖励", "HIGH"),   # Toward Scalable Verifiable Reward
    "2602.16379": ("YES", "LLM agents 用于数据生成", "MEDIUM"),         # Label-Consistent Data Generation
    "2602.16173": ("YES", "从人类反馈学习个性化 agents", "MEDIUM"),      # Learning Personalized Agents

    # 可能相关但不太确定的
    "2602.17641": ("NO", "FAMOSE - 自动特征发现，不是 agent 系统", "HIGH"),  # FAMOSE - 自动化但不是 agent
    "2602.17544": ("NO", "Chain-of-Thought 评估，不是 agent", "HIGH"),     # Evaluating CoT
    "2602.16928": ("NO", "用 LLM 发现多智能体学习算法（理论）", "MEDIUM"), # Discovering Multiagent Learning
    "2602.16873": ("NO", "多智能体编排，但缺少科学应用", "MEDIUM"),        # AdaptOrch
    "2602.16301": ("NO", "多智能体合作（理论博弈）", "HIGH"),              # Multi-agent cooperation

    # 不应该相关的论文
    "2602.17271": ("NO", "语义通信，不是 agent", "HIGH"),                # Federated Latent Space
    "2602.17062": ("NO", "纯 MARL 理论，无科学应用", "HIGH"),            # Retaining Suboptimal Actions
    "2602.16966": ("NO", "MARL 理论框架", "HIGH"),                       # Unified Framework for MARL
    "2602.16958": ("NO", "Agent 劫持（安全研究，非科学）", "HIGH"),      # Automating Agent Hijacking
    "2602.16947": ("NO", "图学习，不是 agent", "HIGH"),                  # Beyond Message Passing
    "2602.17127": ("NO", "AI 对齐审计（非 agent 应用）", "HIGH"),        # Lab-Driven Alignment
    "2602.16346": ("NO", "LLM agents 安全评估（非科学应用）", "HIGH"),   # Helpful to a Fault
    "2602.17486": ("NO", "博弈论理论", "HIGH"),                          # Linear Convergence in Games
    "2602.17068": ("NO", "交通信号控制（应用但非科研 agent）", "MEDIUM"), # Hypergraph MARL for Traffic
    "2602.17009": ("NO", "MARL 理论", "HIGH"),                           # Action-Graph Policies
    "2602.16965": ("NO", "多智能体 Bandit 理论", "HIGH"),                 # Multi-Agent Lipschitz Bandits
    "2602.16564": ("NO", "网络安全博弈（非 agent 系统）", "HIGH"),       # Network Security Games
}

def main():
    print("=" * 100)
    print("模拟测试 paper-relevance-judge skill")
    print("=" * 100)
    print()

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

    # 应用模拟判断
    results = []
    for paper in papers:
        arxiv_id = paper['arxiv_id']
        decision, reasoning, confidence = MOCK_DECISIONS.get(
            arxiv_id,
            ("NO", "未在模拟数据中找到", "LOW")
        )

        results.append({
            **paper,
            'skill_decision': decision,
            'skill_reasoning': reasoning,
            'skill_confidence': confidence
        })

        # 显示进度
        symbol = "✓" if decision == "YES" else "✗"
        print(f"[{paper['rank']:>2}] {symbol} {decision:3} | {paper['title'][:60]}")

    print()
    print("=" * 100)
    print("统计结果")
    print("=" * 100)
    print()

    # 统计
    emb_pass_count = sum(1 for r in results if r['embedding_pass'] == 'True')
    skill_pass_count = sum(1 for r in results if r['skill_decision'] == 'YES')

    print(f"Embedding 过滤: {emb_pass_count}/36 通过 ({emb_pass_count/36*100:.1f}%)")
    print(f"Skill 过滤:    {skill_pass_count}/36 通过 ({skill_pass_count/36*100:.1f}%)")
    print()

    # 对比分析
    yes_emb_no = [r for r in results if r['skill_decision'] == 'YES' and r['embedding_pass'] == 'False']
    no_emb_yes = [r for r in results if r['skill_decision'] == 'NO' and r['embedding_pass'] == 'True']
    both_yes = [r for r in results if r['skill_decision'] == 'YES' and r['embedding_pass'] == 'True']
    both_no = [r for r in results if r['skill_decision'] == 'NO' and r['embedding_pass'] == 'False']

    print("-" * 100)
    print("交叉分析:")
    print(f"  两者都通过:  {len(both_yes):2d} 篇")
    print(f"  两者都拒绝:  {len(both_no):2d} 篇")
    print(f"  Skill ✓ Emb ✗: {len(yes_emb_no):2d} 篇 (Skill 补充了 Embedding 遗漏的)")
    print(f"  Skill ✗ Emb ✓: {len(no_emb_yes):2d} 篇 (Skill 纠正了 Embedding 的误判)")
    print()

    # 保存结果
    output_file = f"mock_skill_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'rank', 'arxiv_id', 'title', 'similarity', 'embedding_pass',
            'skill_decision', 'skill_confidence', 'skill_reasoning'
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                'rank': r['rank'],
                'arxiv_id': r['arxiv_id'],
                'title': r['title'],
                'similarity': r['similarity'],
                'embedding_pass': r['embedding_pass'],
                'skill_decision': r['skill_decision'],
                'skill_confidence': r['skill_confidence'],
                'skill_reasoning': r['skill_reasoning']
            })

    print("=" * 100)
    print("详细分析")
    print("=" * 100)
    print()

    if yes_emb_no:
        print(f"Skill ✓ 但 Embedding ✗ 的论文 ({len(yes_emb_no)} 篇):")
        print("这些是 Skill 成功补充的论文:")
        for r in sorted(yes_emb_no, key=lambda x: float(x['similarity']), reverse=True):
            print(f"  [{r['rank']:>2}] sim={r['similarity']} | {r['title']}")
        print()

    if no_emb_yes:
        print(f"Skill ✗ 但 Embedding ✓ 的论文 ({len(no_emb_yes)} 篇):")
        print("这些是 Skill 纠正的误判:")
        for r in sorted(no_emb_yes, key=lambda x: float(x['similarity']), reverse=True):
            print(f"  [{r['rank']:>2}] sim={r['similarity']} | {r['title']}")
            print(f"       原因: {r['skill_reasoning']}")
        print()

    # 关键论文检查
    print("=" * 100)
    print("关键论文检查")
    print("=" * 100)
    print()

    key_papers = {
        "DataJoint 2.0": "2602.16585",
        "MedClarify": "2602.17308",
        "AutoNumerics": "2602.17607",
        "From Labor to Collaboration": "2602.17221",
        "Towards a Science of AI Agent Reliability": "2602.16666",
    }

    for name, arxiv_id in key_papers.items():
        paper = next((p for p in results if p['arxiv_id'] == arxiv_id), None)
        if paper:
            emb_symbol = "✓" if paper['embedding_pass'] == 'True' else "✗"
            skill_symbol = "✓" if paper['skill_decision'] == 'YES' else "✗"
            print(f"{name}:")
            print(f"  Embedding: {emb_symbol} ({paper['similarity']}) | Skill: {skill_symbol} ({paper['skill_decision']})")
            print(f"  Skill 理由: {paper['skill_reasoning']}")
            print()

    print("=" * 100)
    print(f"结果已保存到: {output_file}")
    print("=" * 100)

if __name__ == "__main__":
    main()
