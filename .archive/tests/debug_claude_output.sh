#!/bin/bash
# 调试 Claude CLI 输出格式

unset CLAUDECODE

# 读取 skill 并跳过 YAML frontmatter
SKILL_BODY=$(awk 'BEGIN{skip=1} /^---$/{if(skip==0)exit; skip=0;next} skip==0{print}' "skills/paper-relevance-judge/SKILL.md")

# 测试单篇论文
TITLE="DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows"
ABSTRACT="DataJoint 2.0 introduces a computational infrastructure designed for agentic scientific workflows, enabling LLM agents to automate research pipelines including data processing, experiment design, and result analysis."

PROMPT="$SKILL_BODY

---

请判断以下论文是否与 AI Agents for Scientific Research 相关：

**论文标题**: $TITLE

**论文摘要**: $ABSTRACT

请严格按照上述格式要求输出判断结果（Decision、Reasoning、Confidence）。"

echo "===================================================================================================="
echo "调试 Claude CLI 输出格式"
echo "===================================================================================================="
echo ""
echo "Skill 长度: $(echo "$SKILL_BODY" | wc -c | tr -d ' ') 字符"
echo "Prompt 长度: $(echo "$PROMPT" | wc -c | tr -d ' ') 字符"
echo ""
echo "===================================================================================================="
echo "Claude 输出:"
echo "===================================================================================================="
echo ""

# 不使用 --max-turns，让 Claude 自然完成
echo "$PROMPT" | claude -p -

echo ""
echo "===================================================================================================="
