---
name: paper-relevance-judge
description: Judge whether academic papers are relevant to AI Agents for Scientific Research. Use when filtering research papers from arXiv, bioRxiv, or other academic platforms to identify papers involving AI/LLM agents for scientific workflows, multi-agent systems for research automation, intelligent agents for data analysis or scientific computing, or agent-based tools for knowledge discovery. Output is YES/NO judgment with reasoning.
---

# Paper Relevance Judge

## Overview

This skill evaluates whether academic papers are relevant to the domain of "AI Agents for Scientific Research." It provides structured criteria and a decision framework to consistently identify papers that involve AI agents, multi-agent systems, or autonomous agents applied to scientific research workflows.

## Relevance Criteria

A paper is **RELEVANT** if it involves:

### 1. Agent Systems for Research
- **Multi-agent systems** used for scientific computing, data analysis, or research automation
- **LLM-powered agents** (AI agents, autonomous agents, intelligent agents) applied to scientific domains
- **Agent-based workflows** for literature review, data processing, experiment design, or knowledge discovery
- **Agentic AI systems** that augment or automate scientific research tasks

### 2. Scientific Application Domains
- Agents for **data analysis** (bioinformatics, genomics, statistical modeling, computational biology)
- Agents for **scientific computing** (numerical simulation, PDE solving, optimization)
- Agents for **knowledge management** (literature search, hypothesis generation, experiment planning)
- Agents for **decision support** (medical diagnosis, experimental design, research planning)
- Agents for **research infrastructure** (SciOps, data pipelines, workflow orchestration)

### 3. Agent Capabilities
- **Autonomous reasoning** and decision-making in scientific contexts
- **Tool use** (APIs, databases, lab equipment) for scientific tasks
- **Human-AI collaboration** in research workflows
- **Multi-agent coordination** for complex scientific problems

### 4. Agent Research for Science (INCLUDE training/methods papers if applied to science)
- **Training methods** for LLM agents **evaluated on scientific tasks** (PaperBench, research workflows, scientific reasoning)
- **Agent architectures** designed for scientific applications
- **Agent capabilities research** (long-horizon planning, reasoning) **with scientific evaluation**
- Key indicators: Mentions of "paper processing", "research automation", "PaperBench", "scientific benchmarks"

⚠️ **Important**: Training/method papers are RELEVANT if they are evaluated on scientific tasks, even if they also evaluate on general tasks.

A paper is **NOT RELEVANT** if it:
- Focuses on **general chatbots** or conversational AI without scientific application
- Studies **agents in non-scientific domains** (gaming, general customer service, social media)
- Describes **traditional machine learning** without agent-based architecture
- Focuses on **single-model predictions** without agentic behavior (autonomy, tool use, reasoning)
- Is about **pure theory** (e.g., game theory, optimization) without agent implementation
- Is **pure bioinformatics/genomics research** (GWAS, pQTL, genome-wide association, proteomics, sequencing analysis) without any AI agent system
- Uses **statistical methods only** (regression, PCA, correlation analysis) for biological/medical data without agent architecture
- Is about **biological data analysis** using traditional computational methods (NOT AI agents)
- Focuses on **biomarker discovery**, **genetic association studies**, or **proteomic profiling** without an AI agent component

⚠️ **CRITICAL DISTINCTION**: A paper about "bioinformatics" or "genomics" is ONLY relevant if it uses AI **AGENTS**. Traditional bioinformatics pipelines, GWAS studies, and statistical genomics are NOT relevant, even if they use machine learning for prediction.

## Evaluation Framework

### Input Format

You will receive:
- **Paper title**
- **Abstract** (summary of the paper)
- **Full text** (optional, if PDF is available)

### Decision Process

⚠️ **CRITICAL OUTPUT FORMAT** ⚠️

**You MUST output ONLY these 3 lines, nothing else:**

```
**Decision**: YES or NO
**Reasoning**: [one sentence explanation]
**Confidence**: HIGH or MEDIUM or LOW
```

**DO NOT**:
- ❌ Do NOT output "Analysis details" or "Evaluation" before the Decision
- ❌ Do NOT output bullet points or step-by-step reasoning
- ❌ Do NOT output anything other than the 3 required lines

**EXAMPLE CORRECT OUTPUT:**
```
**Decision**: YES
**Reasoning**: The paper describes an AI agent for medical diagnosis applied to healthcare.
**Confidence**: HIGH
```

Start your response immediately with `**Decision**:` - do not add any intro text.

1. **Identify Agent Presence**: Does the paper involve agents, multi-agent systems, or agentic AI?
   - Look for keywords: agent, multi-agent, LLM agent, autonomous agent, agentic, AI assistant
   - Check for agent capabilities: autonomy, tool use, reasoning, coordination

2. **Check Scientific Application**: Is the agent applied to scientific research or a scientific domain?
   - Look for domains: bioinformatics, genomics, scientific computing, data analysis, knowledge discovery
   - Check for tasks: literature review, experiment design, data processing, workflow automation

3. **Assess Agent Capabilities**: Does the system demonstrate agentic behavior?
   - **Autonomy**: Can it make decisions or take actions independently?
   - **Tool Use**: Does it interact with external systems (APIs, databases, equipment)?
   - **Reasoning**: Does it use chain-of-thought, planning, or multi-step decision-making?
   - **Coordination**: Are multiple agents working together?

4. **Apply Exclusion Criteria**:
   - **Pure ML/DL**: Papers about neural networks, transformers, or deep learning WITHOUT agent architecture
   - **General AI**: Chatbots, recommendation systems, or prediction systems WITHOUT agentic behavior
   - **Non-scientific**: Agents applied to gaming, entertainment, or general business tasks
   - **Theoretical**: Papers about game theory, optimization, or control theory WITHOUT agent implementation

### Output Format

**Decision**: YES or NO

**Reasoning**: Brief explanation (1-2 sentences) of why the paper is relevant or not

**Confidence**: HIGH, MEDIUM, or LOW

Example:
```
Decision: YES
Reasoning: The paper describes DataJoint 2.0, an agentic workflow system for scientific data pipelines that uses LLM agents to automate research workflows.
Confidence: HIGH
```

## Examples

### Relevant Papers (Decision: YES)

**Example 1**: "DataJoint 2.0: A Computational Substrate for Agentic Scientific Workflows"
- **Why**: Describes an agentic system for automating scientific workflows
- **Key indicators**: "agentic", "scientific workflows", "computational substrate"

**Example 2**: "MedClarify: An information-seeking AI agent for medical diagnosis with case-specific follow-up questions"
- **Why**: AI agent for medical diagnosis (scientific/medical domain)
- **Key indicators**: "AI agent", "medical diagnosis", "information-seeking"

**Example 3**: "AutoNumerics: An Autonomous, PDE-Agnostic Multi-Agent Pipeline for Scientific Computing"
- **Why**: Multi-agent system for scientific computing (PDE solving)
- **Key indicators**: "multi-agent", "scientific computing", "autonomous"

### Not Relevant Papers (Decision: NO)

**Example 1**: "Retaining Suboptimal Actions to Follow Shifting Optima in Multi-Agent Reinforcement Learning"
- **Why**: Pure MARL theory without scientific application or agentic behavior
- **Key issue**: Focuses on RL algorithm, not agent system for science

**Example 2**: "Linear Convergence in Games with Delayed Feedback via Extra Prediction"
- **Why**: Theoretical game theory paper
- **Key issue**: No agent implementation, no scientific application

**Example 3**: "Helpful to a Fault: Measuring Illicit Assistance in Multi-Turn, Multilingual LLM Agents"
- **Why**: Studies general LLM agents for safety, not scientific research
- **Key issue**: Focus is on safety evaluation, not scientific application

**Example 4**: "Human CSF proteogenomics links genetic variation to neurodegenerative disease proteins"
- **Why**: Pure proteogenomics study using GWAS and statistical analysis, no AI agent involved
- **Key issue**: Traditional bioinformatics/statistical genomics, NOT an agent system
- **Note**: Despite keywords like "analysis", "framework", and medical domain, there is NO agent architecture

**Example 5**: "Machine learning analysis of genomic data for cancer prediction"
- **Why**: Uses ML for prediction, but no agent system (autonomy, tool use, reasoning)
- **Key issue**: Single ML model for prediction, NOT an agent system

## Edge Cases and Special Considerations

### Borderline Cases - Lean Towards YES
- Papers about **agents for data analysis** even if the domain isn't explicitly "scientific" (e.g., business analytics with clear agent architecture)
- Papers about **research automation tools** that use LLMs, even if not explicitly called "agents"
- Papers about **human-AI collaboration** for knowledge work or data processing

### Borderline Cases - Lean Towards NO
- Papers about **single-model predictions** (e.g., "An LLM for X") without agentic capabilities
- Papers about **passive tools** (e.g., search engines, databases) without autonomous reasoning
- Papers about **general-purpose AI** (e.g., "A better chatbot") without scientific application
- Papers about **agent training/evaluation** ONLY on non-scientific tasks (coding, gaming, general benchmarks)

### When Full Text is Available
- Prioritize full-text information over abstract for ambiguous cases
- Look for sections on "experiments," "evaluation," or "case studies" to verify scientific application
- Check if the system actually uses agents or if it's just using "agent" as a buzzword

### Confidence Levels
- **HIGH**: Paper clearly involves agents in a scientific context
- **MEDIUM**: Paper likely involves agents but application domain is ambiguous
- **LOW**: Paper uses agent-related terminology but relevance is unclear

## Quick Reference

| Pattern | Decision | Reason |
|---------|----------|--------|
| "agentic [scientific task]" | YES | Agent for scientific workflow |
| "AI agent for [medical/bio/science]" | YES | Agent in scientific domain |
| "multi-agent [scientific computing]" | YES | Multi-agent for science |
| "chatbot for [general task]" | NO | General chatbot, not scientific |
| "LLM for [single prediction]" | NO | Single model, not agent |
| "game theory in MARL" | NO | Theory, not agent system |
| "agent for gaming" | NO | Non-scientific domain |
| "data analysis with agents" | YES | Agent for data analysis |
| "workflow automation with LLM" | YES | Agentic workflow (likely science) |
| "safety of LLM agents" | NO | Safety research, not scientific agent |
| "GWAS / pQTL / proteomics study" | NO | Statistical genomics, not agent |
| "ML for [biomarker/prediction]" | NO | Single ML model, not agent system |
| "genomic analysis with ML" | NO | Traditional bioinformatics, no agent |
| "statistical analysis of [biological data]" | NO | Statistics, not AI agent |
| "proteogenomics / transcriptomics" | NO | Omics study, not agent system |

---

## Final Decision Checklist

Before outputting your decision, verify:

**If answering YES, the paper MUST have at least:**
1. ✓ Clear mention of "agent", "multi-agent", "LLM agent", or "agentic" (in the context of an AI system, not biological agents) AND
2. ✓ Scientific/research application (data analysis, scientific computing, research automation, bio/medical, knowledge discovery) OR clear agentic capabilities (autonomy + tool use + reasoning)

**If answering NO, the paper typically:**
1. ✗ Lacks agent architecture (single model, traditional ML/DL, statistical methods)
2. ✗ Applies agents to non-scientific domains (gaming, general chatbots, social media)
3. ✗ Is pure theory (game theory, optimization) without implementation
4. ✗ Focuses on safety/evaluation of agents rather than using agents for science
5. ✗ Is pure bioinformatics/genomics (GWAS, pQTL, proteomics, sequencing) without AI agent system
6. ✗ Uses ML/statistics for biological data but has NO agent component (no autonomy, no tool use, no reasoning)

**⚠️ CRITICAL CHECK for Bio/Medical Papers:**
Before answering YES for any bio/medical paper, ask:
- Does this paper describe an **AI AGENT SYSTEM** (with autonomy, tool use, multi-step reasoning)?
- OR is it just **traditional bioinformatics/statistical analysis** (GWAS, ML prediction, correlation analysis)?

If it's the latter → Answer **NO**

**When uncertain between YES and NO:**
- If the paper explicitly mentions "agent system", "agentic workflow", "multi-agent", "LLM agent" with scientific application → lean **YES**
- If the paper only mentions "analysis", "model", "prediction", "framework" WITHOUT agent terminology → lean **NO**
- If the paper is about "bioinformatics", "genomics", "proteomics" WITHOUT explicit agent architecture → lean **NO**
