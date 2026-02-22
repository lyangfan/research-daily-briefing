#!/usr/bin/env python3
"""
arXiv 论文采集器
使用 arXiv API 和 RSS 获取论文
"""

import feedparser
import requests
from datetime import date, timedelta
from typing import Dict, List

from .base import BaseFetcher
from ..utils.logger import get_logger

logger = get_logger()


class ArxivFetcher(BaseFetcher):
    """arXiv 论文采集器"""

    BASE_URL = "http://export.arxiv.org/api/query?"

    def __init__(self, config: Dict):
        super().__init__(config)
        self.categories = config.get('categories', [])
        self.rss_url = config.get('rss_url', 'http://export.arxiv.org/rss/')

    def fetch(self, target_date: date, days_back: int = 1) -> List[Dict]:
        """
        获取 arXiv 论文

        Args:
            target_date: 目标日期
            days_back: 向前获取多少天的论文

        Returns:
            论文列表
        """
        if not self.enabled:
            logger.info("arXiv 采集器已禁用")
            return []

        logger.info(f'开始从 arXiv 获取论文 (目标日期: {target_date})')

        all_papers = []

        # 为每个分类获取论文
        for category in self.categories:
            try:
                papers = self._fetch_by_category(category, target_date, days_back)
                all_papers.extend(papers)
                logger.info(f'arXiv {category}: 获取到 {len(papers)} 篇论文')
            except Exception as e:
                logger.error(f'获取 arXiv {category} 论文失败: {e}')

        # 去重
        all_papers = self.deduplicate(all_papers)
        all_papers = [self._normalize_paper(p, 'arxiv') for p in all_papers]
        all_papers = [p for p in all_papers if self._is_valid_paper(p)]

        logger.info(f'arXiv 总计获取 {len(all_papers)} 篇有效论文')
        return all_papers

    def _fetch_by_category(
        self,
        category: str,
        target_date: date,
        days_back: int
    ) -> List[Dict]:
        """
        按分类获取论文

        Args:
            category: arXiv 分类
            target_date: 目标日期
            days_back: 向前获取多少天

        Returns:
            论文列表
        """
        # 计算日期范围
        start_date = target_date - timedelta(days=days_back)

        # 构建 API 查询
        query = f'cat:{category} AND submittedDate:[{start_date.strftime("%Y%m%d")}0000 TO {target_date.strftime("%Y%m%d")}2359]'

        params = {
            'search_query': query,
            'start': 0,
            'max_results': 100,  # 每次最多获取100篇
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            # 解析 Atom 格式响应
            feed = feedparser.parse(response.content)

            papers = []
            for entry in feed.entries:
                paper = self._parse_arxiv_entry(entry)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            logger.error(f'arXiv API 请求失败: {e}')
            return []

    def _parse_arxiv_entry(self, entry: Dict) -> Dict:
        """
        解析 arXiv Atom 条目

        Args:
            entry: feedparser 解析的条目

        Returns:
            论文数据字典
        """
        try:
            # 提取作者
            authors = []
            if hasattr(entry, 'authors'):
                authors = [author.name for author in entry.authors]

            # 提取 arXiv ID
            arxiv_id = entry.id.split('/').pop()
            # 移除版本号
            arxiv_id = arxiv_id.split('v')[0]

            # 发布日期
            published = entry.get('published', '')

            return {
                'id': f"arxiv:{arxiv_id}",
                'title': entry.get('title', ''),
                'authors': authors,
                'abstract': entry.get('summary', '').replace('\n', ' ').strip(),
                'url': entry.get('link', ''),
                'published_date': published,
                'categories': [tag.term for tag in entry.get('tags', [])],
                'arxiv_id': arxiv_id
            }
        except Exception as e:
            logger.warning(f'解析 arXiv 条目失败: {e}')
            return {}

    def fetch_by_ids(self, arxiv_ids: List[str]) -> List[Dict]:
        """
        根据 arXiv ID 列表获取论文详情

        Args:
            arxiv_ids: arXiv ID 列表

        Returns:
            论文列表
        """
        if not arxiv_ids:
            return []

        logger.info(f'根据 ID 获取 {len(arxiv_ids)} 篇 arXiv 论文')

        # 构建查询
        query = ' OR '.join([f'id:{aid}' for aid in arxiv_ids])

        params = {
            'search_query': query,
            'start': 0,
            'max_results': len(arxiv_ids),
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            papers = []
            for entry in feed.entries:
                paper = self._parse_arxiv_entry(entry)
                if paper:
                    papers.append(self._normalize_paper(paper, 'arxiv'))

            return papers

        except Exception as e:
            logger.error(f'根据 ID 获取 arXiv 论文失败: {e}')
            return []
