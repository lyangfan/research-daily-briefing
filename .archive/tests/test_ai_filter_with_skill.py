#!/usr/bin/env python3
"""
测试 AI 过滤器使用 paper-relevance-judge skill
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.processors.ai_filter import AIFilter

def test_ai_filter():
    """测试 AI 过滤器"""

    # 测试配置
    config = {
        'keywords': [
            'multi-agent', 'AI agent', 'LLM agent', 'autonomous agent',
            'scientific workflow', 'research automation'
        ],
        'max_papers': 30,
        'relevance_prompt': '请判断以下论文是否与"科研相关的 AI Agent"相关。'
    }

    # 初始化过滤器
    print("=" * 80)
    print("测试 AI 过滤器 + paper-relevance-judge skill")
    print("=" * 80)
    print()

    ai_filter = AIFilter(config)

    # 检查 skill 是否加载
    if ai_filter.skill_content:
        print("✅ paper-relevance-judge skill 已加载")
        print(f"   Skill 内容长度: {len(ai_filter.skill_content)} 字符")
    else:
        print("⚠️  paper-relevance-judge skill 未加载，将使用基础 prompt")

    print()

    # 测试用例
    test_papers = [
        {
            'id': 'test1',
            'title': 'DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows',
            'abstract': 'DataJoint 2.0 是一个为智能体科学生命周期设计的计算基础设施，支持 LLM agents 自动化科学生命周期中的工作流程。',
            'url': 'https://arxiv.org/abs/2602.16585'
        },
        {
            'id': 'test2',
            'title': 'MedClarify: An information-seeking AI agent for medical diagnosis with case-specific follow-up questions',
            'abstract': '我们提出了 MedClarify，一个用于医学诊断的信息寻求 AI agent，能够根据具体病例提出后续问题。',
            'url': 'https://arxiv.org/abs/2602.17308'
        },
        {
            'id': 'test3',
            'title': 'Retaining Suboptimal Actions to Follow Shifting Optima in Multi-Agent Reinforcement Learning',
            'abstract': '本文研究了在多智能体强化学习中保留次优动作以跟随移动最优解的理论问题。',
            'url': 'https://arxiv.org/abs/2602.17062'
        }
    ]

    print(f"共有 {len(test_papers)} 篇测试论文")
    print()

    if not ai_filter.use_claude:
        print("❌ Claude Code CLI 不可用，无法测试 AI 判断功能")
        print("   请确保已安装 Claude Code CLI 并在 PATH 中")
        return

    print("开始测试 AI 判断...")
    print("-" * 80)
    print()

    results = []
    for i, paper in enumerate(test_papers, 1):
        print(f"[{i}/{len(test_papers)}] 测试论文: {paper['title'][:60]}...")

        try:
            is_relevant = ai_filter._check_relevance(paper)
            status = "✅ 相关" if is_relevant else "❌ 不相关"
            print(f"    结果: {status}")
            results.append({
                'paper': paper,
                'relevant': is_relevant
            })
        except Exception as e:
            print(f"    ❌ 错误: {e}")
            results.append({
                'paper': paper,
                'relevant': None,
                'error': str(e)
            })
        print()

    # 汇总结果
    print("=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print()

    for i, result in enumerate(results, 1):
        paper = result['paper']
        relevant = result.get('relevant')
        expected = i <= 2  # 前两篇应该相关

        status_symbol = "✓" if relevant == expected else "✗"
        status_text = "相关" if relevant else "不相关" if relevant is not None else "错误"

        print(f"{status_symbol} 论文 {i}: {status_text}")
        print(f"   标题: {paper['title']}")
        print(f"   预期: {'相关' if expected else '不相关'}")
        print()

    # 统计
    correct = sum(1 for r in results if r.get('relevant') == (i <= 2))
    print(f"准确率: {correct}/{len(results)} = {correct/len(results)*100:.1f}%")

if __name__ == "__main__":
    test_ai_filter()
