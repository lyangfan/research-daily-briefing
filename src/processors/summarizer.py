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
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.logger import get_logger
from ..utils.pdf_downloader import PDFDownloader
from ..utils.claude_cli import find_claude

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

        # 并行处理配置
        self.max_workers = config.get('max_workers', 4)  # 并行线程数

        # PDF 下载配置
        pdf_config = config.get('pdf_download', {})
        self.pdf_enabled = pdf_config.get('enabled', False)
        self.pdf_downloader = None
        if self.pdf_enabled:
            self.pdf_downloader = PDFDownloader(pdf_config)

        # 查找 claude 命令
        self.claude_path = find_claude()
        if not self.claude_path:
            raise ValueError('未找到 Claude Code CLI，请确保已安装')

        # Skill 路径
        skill_path_config = config.get('skill_path', '')
        if skill_path_config:
            self.skill_path = Path(skill_path_config)
            logger.info(f'使用自定义 Skill: {self.skill_path}')
        else:
            # 默认使用项目内的 skill
            project_root = Path(__file__).parent.parent.parent
            self.skill_path = project_root / 'skills/paper-summarizer/SKILL.md'
            logger.info(f'使用项目 Skill: {self.skill_path}')

        # 检查是否使用 .skill 文件或 SKILL.md
        self.skill_file = None
        if self.skill_path.exists():
            # 优先查找 .skill 文件（ZIP 格式）
            skill_zip = self.skill_path.parent / (self.skill_path.stem + '.skill')
            if skill_zip.exists():
                self.skill_file = str(skill_zip)
                logger.info(f'使用 Skill ZIP: {self.skill_file}')
            else:
                self.skill_file = str(self.skill_path)
                logger.info(f'使用 Skill MD: {self.skill_file}')

        self.use_skill = self.skill_file is not None

        logger.info(f'总结器初始化完成 (Claude Code: {self.claude_path}, 语言: {self.language}, 使用 Skill: {self.use_skill}, PDF支持: {self.pdf_enabled})')

    def summarize_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        为所有论文生成总结（并行处理）

        Args:
            papers: 论文列表

        Returns:
            添加了总结的论文列表
        """
        if not papers:
            return papers

        logger.info(f'开始生成 {len(papers)} 篇论文的总结 (并行线程: {self.max_workers})')

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_paper = {
                executor.submit(self._summarize_and_update, paper): paper
                for paper in papers
            }

            # 收集结果
            completed = 0
            total = len(papers)
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                completed += 1
                try:
                    future.result()
                    title = paper.get('title', 'Unknown')
                    logger.info(f'[{completed}/{total}] 已总结: {title}')
                except Exception as e:
                    logger.error(f'总结论文时出错: {paper.get("title", "Unknown")} - {e}')
                    # 使用摘要作为后备
                    paper['summary'] = paper.get('abstract', '')[:self.max_length]
                    paper['summary_language'] = 'original'

        return papers

    def _summarize_and_update(self, paper: Dict) -> None:
        """
        总结单篇论文并更新到字典中（用于并行处理）

        Args:
            paper: 论文数据（会被直接修改）
        """
        summary = self._summarize_paper(paper)
        paper['summary'] = summary
        paper['summary_language'] = self.language

    def _summarize_paper(self, paper: Dict) -> str:
        """
        为单篇论文生成总结

        Args:
            paper: 论文数据

        Returns:
            中文总结
        """
        if self.use_skill:
            return self._summarize_with_skill(paper)
        else:
            return self._summarize_with_prompt(paper)

    def _summarize_with_skill(self, paper: Dict) -> str:
        """
        使用 Skill 总结论文

        Args:
            paper: 论文数据

        Returns:
            中文总结
        """
        # 读取 skill 内容
        try:
            with open(self.skill_file, 'r', encoding='utf-8') as f:
                skill_content = f.read()
        except Exception as e:
            logger.warning(f'无法读取 Skill 文件: {e}，使用默认 prompt')
            return self._summarize_with_prompt(paper)

        # 跳过 YAML frontmatter
        lines = skill_content.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 0:
                start_idx = i + 1
                break
        skill_body = '\n'.join(lines[start_idx:])

        title = paper.get('title', '')
        authors = ', '.join(paper.get('authors', [])[:3])

        # 准备论文内容（优先使用 PDF 全文）
        paper_content = self._prepare_paper_content(paper)

        # 将 skill 指令和论文内容组合成一个 prompt
        prompt = f"""{skill_body}

---

请总结以下论文：

**标题**: {title}
**作者**: {authors}

{paper_content}

请严格按照上述格式要求，生成包含具体数据的中文总结。"""

        try:
            # 调用 claude 命令，将 skill 内容作为 prompt 传入
            result = subprocess.run(
                [self.claude_path, '-p', prompt],
                capture_output=True,
                text=True,
                timeout=self.single_paper_timeout,
                env={**os.environ, 'CLAUDECODE': ''}
            )

            if result.returncode == 0:
                summary = result.stdout.strip()

                # 清理可能的英文对话和思考过程
                # 找到中文总结的开始位置（通常以 【研究问题】 或类似标记开始）
                lines = summary.split('\n')
                summary_start = 0

                # 寻找第一个包含中文字符的行作为总结开始
                for i, line in enumerate(lines):
                    # 检查是否包含中文字符（Unicode 范围）
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in line)
                    # 排除纯英文行
                    if has_chinese and not line.strip().startswith('📝'):
                        summary_start = i
                        break

                # 如果找到中文开始位置，截取从那里开始的内容
                if summary_start > 0:
                    summary = '\n'.join(lines[summary_start:]).strip()

                # 清理可能的 markdown 代码块标记
                if summary.startswith('```'):
                    lines = summary.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].startswith('```'):
                        lines = lines[:-1]
                    summary = '\n'.join(lines).strip()

                # 限制长度
                if len(summary) > self.max_length:
                    summary = summary[:self.max_length] + '...'

                logger.debug(f'Skill 总结成功: {len(summary)} 字')
                return summary
            else:
                logger.warning(f'Skill 调用失败: {result.stderr}')
                # 降级到普通 prompt 模式
                return self._summarize_with_prompt(paper)

        except subprocess.TimeoutExpired:
            logger.error('Skill 调用超时，降级到普通 prompt 模式')
            return self._summarize_with_prompt(paper)
        except Exception as e:
            logger.error(f'Skill 调用失败: {e}，降级到普通 prompt 模式')
            return self._summarize_with_prompt(paper)

    def _prepare_paper_content(self, paper: Dict) -> str:
        """
        准备论文内容（优先使用 PDF 全文）

        Args:
            paper: 论文数据

        Returns:
            论文内容文本
        """
        # 1. 优先使用预先提取的 PDF 文本（避免并发读取）
        if paper.get('pdf_text'):
            return f"PDF全文内容:\n{paper['pdf_text']}"

        # 2. 如果有 pdf_path 但没有预先提取的文本，提取文本
        if paper.get('pdf_path') and not paper.get('pdf_text'):
            logger.info(f'提取 PDF 文本: {paper.get("title", "")[:50]}...')
            pdf_text = self._extract_pdf_text(paper['pdf_path'])
            if pdf_text:
                # 缓存提取的文本
                paper['pdf_text'] = pdf_text
                return f"PDF全文内容:\n{pdf_text}"

        # 3. 如果启用了 PDF 下载且有 pdf_url，尝试下载
        if self.pdf_enabled and self.pdf_downloader and paper.get('pdf_url'):
            logger.info(f'尝试下载 PDF: {paper.get("title", "")[:50]}...')
            pdf_text = self.pdf_downloader.download_and_extract(paper)
            if pdf_text:
                return f"PDF全文内容:\n{pdf_text}"

        # 4. 降级到摘要模式
        abstract = paper.get('abstract', '')
        if abstract:
            return f"摘要:\n{abstract}"

        return "无可用内容"

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """
        从已下载的 PDF 提取文本

        Args:
            pdf_path: PDF 文件路径

        Returns:
            提取的文本
        """
        if not self.pdf_downloader:
            return ''

        return self.pdf_downloader.extract_text(pdf_path)

    def _summarize_with_prompt(self, paper: Dict) -> str:
        """
        使用普通 Prompt 总结论文（后备方案）

        Args:
            paper: 论文数据

        Returns:
            中文总结
        """
        # 准备论文内容
        paper_content = self._prepare_paper_content(paper)

        # 构建提示词
        prompt_template = self.config.get('prompt', (
            "请用中文总结以下论文，重点突出：\n"
            "1. 研究问题和动机\n"
            "2. 主要方法和创新点\n"
            "3. 关键结果\n\n"
            "论文标题：{title}\n"
            "作者：{authors}\n"
            "{content}\n\n"
            "请用 200-300 字总结，要简洁清晰。"
        ))

        prompt = prompt_template.format(
            title=paper.get('title', ''),
            authors=', '.join(paper.get('authors', [])[:3]),  # 只取前3个作者
            content=paper_content
        )

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
