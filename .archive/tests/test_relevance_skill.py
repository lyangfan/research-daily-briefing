#!/usr/bin/env python3
"""
测试 paper-relevance-judge skill
验证 skill 能否正确判断论文相关性
"""

import subprocess
import sys

def test_skill(title: str, abstract: str) -> dict:
    """使用 skill 判断论文相关性"""

    # 读取 skill 内容
    skill_file = "skills/paper-relevance-judge/SKILL.md"
    with open(skill_file, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    # 跳过 YAML frontmatter
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

    # 调用 claude（需要外部运行，不能嵌套）
    # 返回格式化的 prompt 供用户手动测试
    return {
        "prompt": prompt,
        "title": title,
        "abstract": abstract[:200] + "..." if len(abstract) > 200 else abstract
    }

def main():
    print("=" * 80)
    print("测试 paper-relevance-judge skill")
    print("=" * 80)
    print()

    # 测试用例
    test_cases = [
        {
            "name": "应该相关 - DataJoint 2.0",
            "title": "DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows",
            "abstract": "DataJoint 2.0 是一个为智能体科学生命周期设计的计算基础设施，支持 LLM agents 自动化科学生命周期中的工作流程，包括数据处理、实验设计和结果分析。"
        },
        {
            "name": "应该相关 - MedClarify",
            "title": "MedClarify: An information-seeking AI agent for medical diagnosis with case-specific follow-up questions",
            "abstract": "我们提出了 MedClarify，一个用于医学诊断的信息寻求 AI agent，能够根据具体病例提出后续问题，辅助医生进行诊断决策。"
        },
        {
            "name": "应该相关 - AutoNumerics",
            "title": "AutoNumerics: An Autonomous, PDE-Agnostic Multi-Agent Pipeline for Scientific Computing",
            "abstract": "我们提出了 AutoNumerics，一个自主的、与偏微分方程无关的多智能体管道，用于科学计算。该系统使用多个 LLM agents 协同工作，自动化数值求解过程。"
        },
        {
            "name": "不应该相关 - 纯理论 MARL",
            "title": "Retaining Suboptimal Actions to Follow Shifting Optima in Multi-Agent Reinforcement Learning",
            "abstract": "本文研究了在多智能体强化学习中保留次优动作以跟随移动最优解的理论问题，提出了新的算法框架。"
        },
        {
            "name": "不应该相关 - 博弈论",
            "title": "Linear Convergence in Games with Delayed Feedback via Extra Prediction",
            "abstract": "本文研究了带有延迟反馈的博弈中的线性收敛性问题，通过额外预测方法改进了理论保证。"
        }
    ]

    print(f"共有 {len(test_cases)} 个测试用例\n")
    print("⚠️  注意：由于 Claude Code 不能嵌套调用，请手动运行以下命令进行测试：\n")

    for i, case in enumerate(test_cases, 1):
        result = test_skill(case["title"], case["abstract"])

        print(f"测试 {i}: {case['name']}")
        print(f"标题: {case['title']}")
        print(f"\n手动测试命令:")
        print(f"claude --prompt '{result['prompt'][:500]}...' --max-turns 1")
        print()
        print("-" * 80)
        print()

    print("\n或者，可以在项目根目录下运行：")
    print("python3 src/main.py fetch --date 2026-02-21")
    print("查看 embedding_results_36_new_query.csv 中标记为 False 但应该相关的论文")
    print("然后用 skill 重新判断")

if __name__ == "__main__":
    main()
