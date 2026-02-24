#!/usr/bin/env python3
"""
PDF 下载和文本提取模块
支持下载论文 PDF 并提取文本内容
使用 PyMuPDF4LLM 进行文本提取，专为 LLM 应用优化
"""

import os
import time
import requests
from pathlib import Path
from typing import Dict, Optional

import pymupdf4llm

from .logger import get_logger

logger = get_logger()


class PDFDownloader:
    """PDF 下载和文本提取器"""

    def __init__(self, config: Dict):
        """
        初始化 PDF 下载器

        Args:
            config: 配置字典
        """
        self.config = config
        self.storage_dir = Path(config.get('storage_dir', 'data/papers'))
        self.max_text_length = config.get('max_text_length', 30000)
        self.timeout = config.get('timeout', 60)
        self.user_agent = config.get(
            'user_agent',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 创建存储目录
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f'PDF 下载器初始化完成 (存储目录: {self.storage_dir})')

    def download_paper(self, paper: Dict) -> Optional[str]:
        """
        下载论文 PDF

        Args:
            paper: 论文数据字典，需包含 pdf_url 字段

        Returns:
            本地 PDF 文件路径，失败返回 None
        """
        pdf_url = paper.get('pdf_url', '')
        if not pdf_url:
            logger.debug(f'论文没有 PDF URL: {paper.get("title", "")[:50]}')
            return None

        # 确定本地存储路径
        platform = paper.get('platform', 'unknown')
        paper_id = paper.get('id', '').replace(':', '_').replace('/', '_')

        # 按平台组织目录
        platform_dir = self.storage_dir / platform
        platform_dir.mkdir(exist_ok=True)

        pdf_path = platform_dir / f'{paper_id}.pdf'

        # 检查是否已存在
        if pdf_path.exists():
            logger.debug(f'PDF 已存在: {pdf_path}')
            return str(pdf_path)

        # 下载 PDF
        try:
            logger.info(f'开始下载 PDF: {pdf_url}')

            headers = {'User-Agent': self.user_agent}
            response = requests.get(
                pdf_url,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not pdf_url.endswith('.pdf'):
                logger.warning(f'URL 可能不是 PDF: {content_type}')
                # 继续尝试，有些服务器不返回正确的 content-type

            # 写入文件
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f'PDF 下载成功: {pdf_path} ({pdf_path.stat().st_size / 1024:.1f} KB)')
            return str(pdf_path)

        except requests.exceptions.Timeout:
            logger.error(f'下载 PDF 超时: {pdf_url}')
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f'下载 PDF 失败: {e}')
            return None
        except Exception as e:
            logger.error(f'保存 PDF 失败: {e}')
            return None

    def extract_text(self, pdf_path: str, max_chars: int = None) -> str:
        """
        从 PDF 提取文本（使用 PyMuPDF4LLM，保留 Markdown 格式）

        Args:
            pdf_path: PDF 文件路径
            max_chars: 最大提取字符数（默认使用配置中的值）

        Returns:
            提取的文本内容（Markdown 格式）
        """
        if max_chars is None:
            max_chars = self.max_text_length

        try:
            # 使用 PyMuPDF4LLM 提取文本，保留 Markdown 格式
            # 这比纯文本提取更适合 LLM 处理
            md_text = pymupdf4llm.to_markdown(pdf_path)

            # 截断到最大长度（设置为 0 表示不截断）
            if max_chars > 0 and len(md_text) > max_chars:
                md_text = md_text[:max_chars] + '\n\n[文本已截断...]'

            logger.debug(f'从 {pdf_path} 提取了 {len(md_text)} 字符文本 (Markdown 格式)')
            return md_text

        except Exception as e:
            # 如果 PyMuPDF4LLM 失败，尝试使用基础 PyMuPDF 提取纯文本
            logger.warning(f'PyMuPDF4LLM 提取失败 ({e})，尝试使用基础 PyMuPDF 提取')
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(pdf_path)
                text_parts = []
                for page in doc:
                    try:
                        page_text = page.get_text()
                        if page_text.strip():
                            text_parts.append(page_text)
                    except Exception as e:
                        # 跳过无法提取的页面（如图像页面）
                        logger.debug(f'跳过无法提取的页面: {e}')
                        continue
                doc.close()

                plain_text = '\n\n'.join(text_parts)

                if max_chars > 0 and len(plain_text) > max_chars:
                    plain_text = plain_text[:max_chars] + '\n\n[文本已截断...]'

                logger.debug(f'使用基础 PyMuPDF 提取了 {len(plain_text)} 字符文本')
                return plain_text

            except Exception as e2:
                logger.error(f'基础 PyMuPDF 提取也失败: {e2}')
                return ''

    def download_and_extract(self, paper: Dict) -> Optional[str]:
        """
        下载 PDF 并提取文本（一步完成）

        Args:
            paper: 论文数据字典

        Returns:
            提取的文本内容，失败返回 None
        """
        # 先下载 PDF
        pdf_path = self.download_paper(paper)
        if not pdf_path:
            return None

        # 提取文本
        text = self.extract_text(pdf_path)
        if text:
            # 将路径保存到 paper 字典中，供后续使用
            paper['pdf_path'] = pdf_path
            return text

        return None

    def cleanup_old_pdfs(self, days: int = 30):
        """
        清理旧的 PDF 文件

        Args:
            days: 保留最近多少天的 PDF
        """
        if not self.storage_dir.exists():
            return

        cutoff_time = time.time() - (days * 86400)
        deleted_count = 0

        for pdf_file in self.storage_dir.rglob('*.pdf'):
            if pdf_file.stat().st_mtime < cutoff_time:
                try:
                    pdf_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f'删除旧 PDF 失败: {pdf_file}, {e}')

        if deleted_count > 0:
            logger.info(f'清理了 {deleted_count} 个旧 PDF 文件')

    def cleanup_all_pdfs(self):
        """
        清理所有 PDF 文件
        """
        if not self.storage_dir.exists():
            return

        deleted_count = 0

        for pdf_file in self.storage_dir.rglob('*.pdf'):
            try:
                pdf_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f'删除 PDF 失败: {pdf_file}, {e}')

        if deleted_count > 0:
            logger.info(f'清理了 {deleted_count} 个 PDF 文件')

    def get_storage_info(self) -> Dict:
        """
        获取存储信息

        Returns:
            存储统计信息
        """
        if not self.storage_dir.exists():
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'by_platform': {}
            }

        total_files = 0
        total_size = 0
        by_platform = {}

        for pdf_file in self.storage_dir.rglob('*.pdf'):
            total_files += 1
            size = pdf_file.stat().st_size
            total_size += size

            platform = pdf_file.parent.name
            by_platform[platform] = by_platform.get(platform, 0) + 1

        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_platform': by_platform
        }
