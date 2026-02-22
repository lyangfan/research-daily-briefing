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
    """AI 相关性过滤器 (使用 Claude Code CLI)"""

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
        使用 Claude Code CLI 判断论文是否相关

        Args:
            paper: 论文数据

        Returns:
            是否相关
        """
        # 构建提示词
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
        )).format(
            title=paper.get('title', ''),
            abstract=paper.get('abstract', '')
        )

        try:
            result = subprocess.run(
                [
                    self.claude_path,
                    '-p', prompt,
                    '--max-turns', '1',
                ],
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, 'CLAUDECODE': ''}
            )

            if result.returncode == 0:
                content = result.stdout.strip().lower()

                # 判断响应
                return '相关' in content or 'relevant' in content or 'yes' in content
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
