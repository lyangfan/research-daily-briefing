#!/usr/bin/env python3
"""
AI 过滤器
使用 Claude Code CLI 判断论文是否与"科研相关的 AI Agent"相关
"""

import os
import subprocess
from typing import Dict, List

from ..utils.logger import get_logger

logger = get_logger()


class AIFilter:
    """AI 相关性过滤器 (使用 Claude Code CLI + paper-relevance-judge skill)"""

    def __init__(self, config: Dict):
        """
        初始化 AI 过滤器

        Args:
            config: AI 过滤配置
        """
        self.config = config
        self.keywords = config.get('keywords', [])
        self.max_papers = config.get('max_papers', 30)

        # 查找 claude 命令
        self.claude_path = self._find_claude()
        if not self.claude_path:
            logger.warning('未找到 Claude Code CLI，将使用关键词过滤')
            self.use_claude = False
        else:
            self.use_claude = True
            logger.info(f'AI 过滤器初始化完成 (Claude Code: {self.claude_path})')

        # 加载 paper-relevance-judge skill
        self.skill_content = self._load_skill()

    def _find_claude(self) -> str:
        """查找 claude 命令路径"""
        try:
            result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass

        common_paths = [
            os.path.expanduser('~/.local/bin/claude'),
            '/usr/local/bin/claude',
            os.path.expanduser('~/.claude/local/claude'),
        ]

        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path

        return None

    def _load_skill(self) -> str:
        """
        加载 paper-relevance-judge skill 内容

        Returns:
            skill 内容（跳过 YAML frontmatter）
        """
        # 查找 skill 文件
        skill_paths = [
            'skills/paper-relevance-judge/SKILL.md',  # 项目内路径
            os.path.expanduser('~/.claude/skills/paper-relevance-judge/SKILL.md'),  # 用户安装路径
        ]

        for skill_path in skill_paths:
            if os.path.exists(skill_path):
                try:
                    with open(skill_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 跳过 YAML frontmatter
                    lines = content.split('\n')
                    start_idx = 0
                    for i, line in enumerate(lines):
                        if line.strip() == '---' and i > 0:
                            start_idx = i + 1
                            break

                    skill_body = '\n'.join(lines[start_idx:])
                    logger.info(f'已加载 paper-relevance-judge skill: {skill_path}')
                    return skill_body

                except Exception as e:
                    logger.warning(f'读取 skill 文件失败 ({skill_path}): {e}')

        logger.warning('未找到 paper-relevance-judge skill，将使用基础 prompt')
        return None

    def filter_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        过滤论文，返回相关的论文

        Args:
            papers: 论文列表

        Returns:
            相关的论文列表
        """
        if not papers:
            return []

        logger.info(f'开始 AI 过滤，共 {len(papers)} 篇论文')

        # 第一步：关键词初筛
        keyword_filtered = self._filter_by_keywords(papers)
        logger.info(f'关键词初筛后剩余 {len(keyword_filtered)} 篇论文')

        # 限制数量
        if len(keyword_filtered) > self.max_papers:
            logger.info(f'限制数量为 {self.max_papers} 篇')
            keyword_filtered = keyword_filtered[:self.max_papers]

        # 第二步：AI 判断相关性
        if self.use_claude:
            relevant_papers = []
            for i, paper in enumerate(keyword_filtered):
                try:
                    is_relevant = self._check_relevance(paper)
                    if is_relevant:
                        relevant_papers.append(paper)
                        logger.info(f'[{i+1}/{len(keyword_filtered)}] ✓ {paper["title"][:50]}...')
                    else:
                        logger.debug(f'[{i+1}/{len(keyword_filtered)}] ✗ {paper["title"][:50]}...')
                except Exception as e:
                    logger.error(f'判断论文相关性时出错: {e}')
                    # 出错时保守处理，保留论文
                    relevant_papers.append(paper)

            logger.info(f'AI 过滤完成，相关论文 {len(relevant_papers)} 篇')
            return relevant_papers
        else:
            # 没有 Claude Code CLI，直接使用关键词过滤的结果
            logger.info('使用关键词过滤结果')
            return keyword_filtered

    def _filter_by_keywords(self, papers: List[Dict]) -> List[Dict]:
        """
        基于关键词初筛

        Args:
            papers: 论文列表

        Returns:
            包含关键词的论文列表
        """
        if not self.keywords:
            return papers

        filtered = []
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()

            # 检查是否包含任何关键词
            for keyword in self.keywords:
                if keyword.lower() in title or keyword.lower() in abstract:
                    filtered.append(paper)
                    break

        return filtered

    def _check_relevance(self, paper: Dict) -> bool:
        """
        使用 Claude Code CLI + paper-relevance-judge skill 判断论文是否相关

        Args:
            paper: 论文数据

        Returns:
            是否相关
        """
        # 准备论文内容
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')

        # 构建提示词（优先使用 skill）
        if self.skill_content:
            # 使用 paper-relevance-judge skill
            prompt = f"""{self.skill_content}

---

请判断以下论文是否与 AI Agents for Scientific Research 相关：

**论文标题**: {title}

**论文摘要**: {abstract}

请严格按照上述格式要求输出判断结果（Decision、Reasoning、Confidence）。"""
        else:
            # 降级到基础 prompt
            prompt = self.config.get('relevance_prompt', (
                "请判断以下论文是否与'科研相关的 AI Agent'相关。\n\n"
                "判断标准：\n"
                "1. 是否涉及多智能体系统 (multi-agent systems)\n"
                "2. 是否涉及 AI/LLM Agent 的研究\n"
                "3. 是否涉及自动化科研工具或方法论\n"
                "4. 是否涉及强化学习在智能体中的应用\n\n"
                "论文标题：{title}\n"
                "论文摘要：{abstract}\n\n"
                "请只回答 '相关' 或 '不相关'，不要解释。"
            )).format(title=title, abstract=abstract)

        try:
            result = subprocess.run(
                [
                    self.claude_path,
                    '-p', prompt,
                ],
                capture_output=True,
                text=True,
                timeout=120,  # 增加超时到 2 分钟
                env={**os.environ, 'CLAUDECODE': ''}
            )

            if result.returncode == 0:
                content = result.stdout.strip()

                # 记录完整响应用于调试
                logger.debug(f'AI 判断响应:\n{content}')

                # 解析响应（支持多种格式）
                # 格式1: "**Decision**: YES" (Markdown 粗体)
                # 格式2: "Decision: YES" (普通格式)
                # 格式3: "Decision:YES" (无空格)
                # 格式4: "相关" / "不相关" (中文)

                content_lower = content.lower()
                content_stripped = content.strip()

                # 首先检查 **decision** 格式（Markdown 粗体）
                if '**decision**' in content_lower:
                    for line in content.split('\n'):
                        if '**decision**' in line.lower():
                            # 清理并提取
                            line_clean = line.replace('*', '').replace(':', ' ').lower()
                            words = line_clean.split()
                            if 'yes' in words:
                                logger.debug(f"Decision: YES (line: {line[:50]})")
                                return True
                            elif 'no' in words:
                                logger.debug(f"Decision: NO (line: {line[:50]})")
                                return False

                # 检查 decision: 格式（无星号）
                if 'decision:' in content_lower:
                    for line in content.split('\n'):
                        if 'decision:' in line.lower():
                            # 提取 decision 后面的值
                            decision_part = line.split('decision:')[1].strip().lower()
                            if decision_part.startswith('yes') or decision_part.startswith('``yes'):
                                logger.debug(f"Decision: YES (line: {line[:50]})")
                                return True
                            elif decision_part.startswith('no') or decision_part.startswith('``no'):
                                logger.debug(f"Decision: NO (line: {line[:50]})")
                                return False

                # 降级到简单格式检查
                # 检查第一行是否直接是 YES/NO
                first_line = content_stripped.split('\n')[0] if content_stripped else ''
                first_word = first_line.split()[0].lower() if first_line else ''

                if first_word in ['yes', 'yes', 'yes.', 'yes,']:
                    logger.debug(f"Decision: YES (first word)")
                    return True
                elif first_word in ['no', 'no.', 'no,']:
                    logger.debug(f"Decision: NO (first word)")
                    return False

                # 检查中文
                if first_word in ['相关', '是']:
                    logger.debug(f"Decision: YES (Chinese)")
                    return True
                elif first_word in ['不相关', '否', '不是']:
                    logger.debug(f"Decision: NO (Chinese)")
                    return False

                # 最后检查内容中是否包含明确的关键词/判断
                # 特别处理：如果包含 "Scientific application: No" 等分析格式

                # 1. 检查分析格式中的明确判断
                analysis_patterns = [
                    ('scientific application: no', False),
                    ('scientific application: yes', True),
                    ('agent presence: no', False),
                    ('not relevant', False),
                    ('relevant for scientific', True),
                ]

                for pattern, value in analysis_patterns:
                    if pattern in content_lower:
                        logger.debug(f"Decision: {value} (analysis pattern: {pattern})")
                        return value

                # 2. 检查是否有明确的 YES 声明
                yes_patterns = [
                    'decision: yes',
                    'decision:``yes',
                    '"decision": yes',
                    '**decision**: yes',
                    ': yes (agent',
                    ': yes (scientific',
                ]
                for pattern in yes_patterns:
                    if pattern in content_lower:
                        logger.debug(f"Decision: YES (pattern: {pattern})")
                        return True

                # 3. 检查 NO 模式
                no_patterns = [
                    'decision: no',
                    'decision:``no',
                    '"decision": no',
                    '**decision**: no',
                    ': no (not',
                    ': no (focuses',
                    'scientific application: no',
                    'not a scientific',
                    'no (focuses on',
                ]
                for pattern in no_patterns:
                    if pattern in content_lower:
                        logger.debug(f"Decision: NO (pattern: {pattern})")
                        return False

                # 默认降级：根据内容中的关键词判断
                has_yes_indicators = any(w in content_lower for w in ['yes', '相关', 'relevant', 'pass'])
                has_no_indicators = any(w in content_lower for w in ['not relevant', '不相关', 'fail', 'no'])

                if has_yes_indicators and not has_no_indicators:
                    logger.debug(f"Decision: YES (keyword fallback)")
                    return True
                elif has_no_indicators and not has_yes_indicators:
                    logger.debug(f"Decision: NO (keyword fallback)")
                    return False

                # 完全无法判断，记录日志
                logger.warning(f"无法解析 AI 判断结果，内容前 200 字符: {content[:200]}")
                return False
            else:
                logger.debug(f'Claude Code CLI 调用失败: {result.stderr}')
                # 降级到关键词判断
                return self._has_keyword(paper)

        except subprocess.TimeoutExpired:
            logger.debug('Claude Code CLI 超时')
            return self._has_keyword(paper)
        except Exception as e:
            logger.debug(f'AI 判断失败: {e}')
            return self._has_keyword(paper)

    def _has_keyword(self, paper: Dict) -> bool:
        """
        检查论文是否包含关键词（后备方法）

        Args:
            paper: 论文数据

        Returns:
            是否包含关键词
        """
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()

        for keyword in self.keywords:
            if keyword.lower() in title or keyword.lower() in abstract:
                return True
        return False
