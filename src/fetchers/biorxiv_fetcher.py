#!/usr/bin/env python3
"""
bioRxiv/medRxiv 论文采集器
使用 bioRxiv API 获取论文
"""

import requests
from datetime import date, timedelta, datetime
from typing import Dict, List

from .base import BaseFetcher
from ..utils.logger import get_logger

logger = get_logger()


class BiorxivFetcher(BaseFetcher):
    """bioRxiv 论文采集器"""

    def __init__(self, config: Dict, platform: str = "biorxiv"):
        super().__init__(config)
        self.platform = platform
        self.api_url = config.get('api_url', 'https://api.biorxiv.org/details/biorxiv')
        self.sections = config.get('sections', [])

    def fetch(self, target_date: date, days_back: int = 1) -> List[Dict]:
        """
        获取 bioRxiv/medRxiv 论文

        Args:
            target_date: 目标日期
            days_back: 向前获取多少天的论文

        Returns:
            论文列表
        """
        if not self.enabled:
            logger.info(f"{self.platform} 采集器已禁用")
            return []

        logger.info(f'开始从 {self.platform} 获取论文 (目标日期: {target_date})')

        all_papers = []

        # 计算日期范围
        start_date = target_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = target_date.strftime('%Y-%m-%d')

        # 为每个分区获取论文
        for section in self.sections:
            try:
                papers = self._fetch_by_section(
                    section,
                    start_date_str,
                    end_date_str
                )
                all_papers.extend(papers)
                logger.info(f'{self.platform} {section}: 获取到 {len(papers)} 篇论文')
            except Exception as e:
                logger.error(f'获取 {self.platform} {section} 论文失败: {e}')

        # 去重
        all_papers = self.deduplicate(all_papers)
        all_papers = [self._normalize_paper(p, self.platform) for p in all_papers]
        all_papers = [p for p in all_papers if self._is_valid_paper(p)]

        logger.info(f'{self.platform} 总计获取 {len(all_papers)} 篇有效论文')
        return all_papers

    def _fetch_by_section(
        self,
        section: str,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        按分区获取论文

        Args:
            section: 分区名称
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            论文列表
        """
        # bioRxiv API 使用格式: /details/[server]/[interval]/[cursor]/[format]
        # interval 是 start_date/end_date
        # 对于特定分类，使用 query string 参数
        base_url = self.api_url.rsplit('/', 1)[0]  # 移除末尾的 biorxiv/medrxiv
        server = self.platform  # biorxiv 或 medrxiv

        all_papers = []
        cursor = 0

        # 请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }

        try:
            while True:
                # 构建 URL: /details/biorxiv/start_date/end_date/cursor/json
                # 添加 category 参数作为 query string
                url = f"{base_url}/{server}/{start_date}/{end_date}/{cursor}/json"
                if section:
                    # 使用 category 参数过滤
                    url = f"{url}?category={section}"

                logger.debug(f'{self.platform} API URL: {url}')

                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                data = response.json()
                papers = data.get('collection', [])

                if not papers:
                    break

                # 解析论文
                for paper_data in papers:
                    paper = self._parse_biorxiv_entry(paper_data)
                    if paper:
                        all_papers.append(paper)

                # 检查是否还有更多数据
                messages = data.get('messages', [])
                if messages and len(papers) >= 100:
                    # 每次返回最多 100 篇，继续获取下一批
                    cursor += 100
                else:
                    # 没有更多数据了
                    break

                # 防止无限循环（限制获取数量）
                if len(all_papers) >= 1000:
                    logger.warning(f'{self.platform} {section}: 已获取 1000 篇论文，停止获取')
                    break

        except Exception as e:
            logger.error(f'{self.platform} API 请求失败: {e}')

        return all_papers

    def _parse_biorxiv_entry(self, entry: Dict) -> Dict:
        """
        解析 bioRxiv API 返回的论文数据

        Args:
            entry: API 返回的论文字典

        Returns:
            论文数据字典
        """
        try:
            # 提取作者
            authors = entry.get('authors', '').split(';')

            # 清理作者名
            authors = [a.strip() for a in authors if a.strip()]

            # 从 DOI 构造 URL
            doi = entry.get('doi', '')
            if doi:
                # DOI 格式: 10.1101/2024.03.26.586795
                # landing page: https://www.biorxiv.org/content/10.1101/2024.03.26.586795
                # PDF URL: https://www.biorxiv.org/content/10.1101/2024.03.26.586795v2.full.pdf
                version = entry.get('version', '')
                version_suffix = f'v{version}' if version and version != '1' else ''
                landing_page = f"https://www.{self.platform}.org/content/{doi}{version_suffix}"
                pdf_url = f"{landing_page}.full.pdf"
            else:
                landing_page = ''
                pdf_url = ''

            return {
                'id': f"{self.platform}:{doi}",
                'title': entry.get('title', ''),
                'authors': authors,
                'abstract': entry.get('abstract', '').replace('<p>', '').replace('</p>', ''),
                'url': landing_page,
                'pdf_url': pdf_url,  # PDF 下载链接
                'published_date': entry.get('date', ''),
                'categories': [entry.get('category', '')],
                'doi': doi,
                'version': entry.get('version', '')
            }
        except Exception as e:
            logger.warning(f'解析 {self.platform} 条目失败: {e}')
            return {}


class MedrxivFetcher(BiorxivFetcher):
    """medRxiv 论文采集器（继承自 bioRxiv）"""

    def __init__(self, config: Dict):
        # 使用 medRxiv API URL
        config = config.copy()
        config['api_url'] = config.get('api_url', 'https://api.medrxiv.org/details/medrxiv')
        super().__init__(config, platform="medrxiv")
