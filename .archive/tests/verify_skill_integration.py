#!/usr/bin/env python3
"""
验证 paper-relevance-judge skill 集成
"""

import sys
import os
sys.path.insert(0, '.')

def main():
    print("=" * 80)
    print("验证 paper-relevance-judge skill 集成")
    print("=" * 80)
    print()

    # 1. 检查 skill 文件
    skill_path = "skills/paper-relevance-judge/SKILL.md"
    if os.path.exists(skill_path):
        print(f"✅ Skill 文件存在: {skill_path}")
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"   文件大小: {len(content)} 字符")
    else:
        print(f"❌ Skill 文件不存在: {skill_path}")
        return

    print()

    # 2. 检查 ai_filter.py 是否修改
    ai_filter_path = "src/processors/ai_filter.py"
    with open(ai_filter_path, 'r', encoding='utf-8') as f:
        ai_filter_content = f.read()

    checks = [
        ("_load_skill 方法", "_load_skill" in ai_filter_content),
        ("skill_content 属性", "self.skill_content" in ai_filter_content),
        ("skill 路径检查", "skills/paper-relevance-judge/SKILL.md" in ai_filter_content),
        ("Decision 格式解析", "'decision:'" in ai_filter_content),
        ("Reasoning 记录", "'reasoning:'" in ai_filter_content),
    ]

    print("代码修改检查:")
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"  {status} {check_name}")

    print()

    # 3. 测试 AIFilter 初始化
    print("测试 AIFilter 初始化:")
    try:
        from src.processors.ai_filter import AIFilter
        config = {'keywords': ['agent'], 'max_papers': 30}
        ai_filter = AIFilter(config)

        if ai_filter.skill_content:
            print(f"  ✅ Skill 已加载 ({len(ai_filter.skill_content)} 字符)")
        else:
            print(f"  ⚠️  Skill 未加载")

        if ai_filter.use_claude:
            print(f"  ✅ Claude Code CLI 可用: {ai_filter.claude_path}")
        else:
            print(f"  ⚠️  Claude Code CLI 不可用")
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")

    print()
    print("=" * 80)
    print("集成验证完成")
    print("=" * 80)
    print()
    print("下一步：")
    print("1. 运行完整测试: python3 src/main.py fetch --date 2026-02-21")
    print("2. 查看日志确认 skill 被使用")
    print("3. 对比 embedding_results_36_new_query.csv 中的结果")

if __name__ == "__main__":
    main()
