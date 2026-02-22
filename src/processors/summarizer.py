#!/usr/bin/env python3
"""
论文总结器
使用 Claude Code CLI 生成中文总结
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

from ..utils.logger import get_logger

logger = get_logger()


class PaperSummarizer:
    """论文总结器 (使用 Claude Code CLI)"""

    def __init__(self, config: Dict):
        """
        初始化总结器

        Args:
            config: 总结器配置
        """
        self.config = config
        self.language = config.get('language', 'zh-CN')
        self.max_length = config.get('max_length', 300)

        # 超时配置（支持外部 Skill 调用）
        self.single_paper_timeout = config.get('single_paper_timeout', 600)  # 单篇论文超时（秒）
        self.batch_timeout = config.get('batch_timeout', 900)  # 批量总结超时（秒）

        # 查找 claude 命令
        self.claude_path = self._find_claude()
        if not self.claude_path:
            raise ValueError('未找到 Claude Code CLI，请确保已安装')

        logger.info(f'总结器初始化完成 (Claude Code: {self.claude_path}, 语言: {self.language})')

    def _find_claude(self) -> str:
        """
        查找 claude 命令路径

        Returns:
            claude 命令路径，未找到返回 None
        """
        # 1. 检查 PATH 中的 claude
        try:
            result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass

        # 2. 检查常见安装位置
        common_paths = [
            os.path.expanduser('~/.local/bin/claude'),
            '/usr/local/bin/claude',
            os.path.expanduser('~/.claude/local/claude'),
        ]

        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path

        return None

    def summarize_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        为所有论文生成总结

        Args:
            papers: 论文列表

        Returns:
            添加了总结的论文列表
        """
        logger.info(f'开始生成 {len(papers)} 篇论文的总结 (使用 Claude Code CLI)')

        for i, paper in enumerate(papers):
            try:
                summary = self._summarize_paper(paper)
                paper['summary'] = summary
                paper['summary_language'] = self.language
                logger.info(f'[{i+1}/{len(papers)}] 已总结: {paper["title"][:50]}...')
            except Exception as e:
                logger.error(f'总结论文时出错: {e}')
                # 使用摘要作为后备
                paper['summary'] = paper.get('abstract', '')[:self.max_length]
                paper['summary_language'] = 'original'

        return papers

    def _summarize_paper(self, paper: Dict) -> str:
        """
        为单篇论文生成总结

        Args:
            paper: 论文数据

        Returns:
            中文总结
        """
        # 构建提示词
        prompt = self.config.get('prompt', (
            "请用中文总结以下论文，重点突出：\n"
            "1. 研究问题和动机\n"
            "2. 主要方法和创新点\n"
            "3. 关键结果\n\n"
            "论文标题：{title}\n"
            "作者：{authors}\n"
            "摘要：{abstract}\n\n"
            "请用 200-300 字总结，要简洁清晰。"
        )).format(
            title=paper.get('title', ''),
            authors=', '.join(paper.get('authors', [])[:3]),  # 只取前3个作者
            abstract=paper.get('abstract', '')
        )

        # 使用临时文件存储提示词和结果
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as prompt_file:
            prompt_file.write(prompt)
            prompt_path = prompt_file.name

        try:
            # 调用 claude 命令
            # 使用 -p 传递提示词，--max-turns 1 限制为单次对话
            result = subprocess.run(
                [
                    self.claude_path,
                    '-p', prompt,
                    '--max-turns', '1',
                    '--allowed-tools', ''  # 不需要工具
                ],
                capture_output=True,
                text=True,
                timeout=self.single_paper_timeout,  # 可配置的超时时间
                env={**os.environ, 'CLAUDECODE': ''}  # 清除 CLAUDECODE 环境变量
            )

            if result.returncode == 0:
                summary = result.stdout.strip()

                # 清理可能的 markdown 代码块标记
                if summary.startswith('```'):
                    lines = summary.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines[-1].startswith('```'):
                        lines = lines[:-1]
                    summary = '\n'.join(lines).strip()

                # 限制长度
                if len(summary) > self.max_length:
                    summary = summary[:self.max_length] + '...'

                return summary
            else:
                logger.error(f'Claude Code CLI 执行失败: {result.stderr}')
                # 使用摘要作为后备
                return paper.get('abstract', '')[:self.max_length]

        except subprocess.TimeoutExpired:
            logger.error('Claude Code CLI 执行超时')
            return paper.get('abstract', '')[:self.max_length]
        except Exception as e:
            logger.error(f'调用 Claude Code CLI 失败: {e}')
            return paper.get('abstract', '')[:self.max_length]
        finally:
            # 清理临时文件
            try:
                os.unlink(prompt_path)
            except:
                pass

    def summarize_papers_batch(self, papers: List[Dict]) -> List[Dict]:
        """
        批量总结论文（一次调用处理多篇）

        Args:
            papers: 论文列表

        Returns:
            添加了总结的论文列表
        """
        if not papers:
            return papers

        logger.info(f'开始批量总结 {len(papers)} 篇论文 (使用 Claude Code CLI)')

        # 构建批量提示词
        paper_texts = []
        for i, paper in enumerate(papers, 1):
            paper_text = f"""
论文 {i}:
标题: {paper.get('title', '')}
作者: {', '.join(paper.get('authors', [])[:3])}
摘要: {paper.get('abstract', '')}
"""
            paper_texts.append(paper_text)

        batch_prompt = self.config.get('batch_prompt', (
            "请用中文总结以下每篇论文，每篇 200-300 字，重点突出研究问题、方法创新和关键结果。\n\n"
            "请按以下格式返回，每篇论文用 ===分隔：\n"
            "【论文1】\n"
            "总结内容...\n\n"
            "===\n"
            "【论文2】\n"
            "总结内容...\n\n"
            "...\n\n"
        )) + '\n'.join(paper_texts)

        try:
            result = subprocess.run(
                [
                    self.claude_path,
                    '-p', batch_prompt,
                    '--max-turns', '1',
                ],
                capture_output=True,
                text=True,
                timeout=self.batch_timeout,  # 可配置的批量超时时间
                env={**os.environ, 'CLAUDECODE': ''}
            )

            if result.returncode == 0:
                # 解析批量结果
                summaries = self._parse_batch_summaries(result.stdout, len(papers))

                for i, paper in enumerate(papers):
                    if i < len(summaries):
                        paper['summary'] = summaries[i]
                        paper['summary_language'] = self.language
                    else:
                        # 使用摘要作为后备
                        paper['summary'] = paper.get('abstract', '')[:self.max_length]
                        paper['summary_language'] = 'original'

                logger.info(f'批量总结完成')
            else:
                logger.error(f'批量总结失败: {result.stderr}')
                # 降级为单篇处理
                return self.summarize_papers(papers)

        except subprocess.TimeoutExpired:
            logger.error('批量总结超时，降级为单篇处理')
            return self.summarize_papers(papers)
        except Exception as e:
            logger.error(f'批量总结出错: {e}，降级为单篇处理')
            return self.summarize_papers(papers)

        return papers

    def _parse_batch_summaries(self, output: str, expected_count: int) -> List[str]:
        """
        解析批量总结结果

        Args:
            output: Claude Code 输出
            expected_count: 期望的总结数量

        Returns:
            总结列表
        """
        summaries = []

        # 按分隔符分割
        parts = output.split('===')

        for part in parts:
            # 清理 markdown 代码块
            summary = part.strip()
            if summary.startswith('```'):
                lines = summary.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines[-1].startswith('```'):
                    lines = lines[:-1]
                summary = '\n'.join(lines).strip()

            if summary:
                summaries.append(summary)

        return summaries

    def generate_daily_summary(self, papers: List[Dict]) -> str:
        """
        生成当日论文总览

        Args:
            papers: 论文列表

        Returns:
            总览文本
        """
        if not papers:
            return "今日未发现相关论文。"

        total = len(papers)
        platforms = {}
        for paper in papers:
            platform = paper.get('platform', 'unknown')
            platforms[platform] = platforms.get(platform, 0) + 1

        # 构建总览
        overview_parts = [
            f"今日共发现 {total} 篇与「科研相关 AI Agent」的论文：",
        ]

        for platform, count in sorted(platforms.items()):
            overview_parts.append(f"  - {platform}: {count} 篇")

        return '\n'.join(overview_parts)
