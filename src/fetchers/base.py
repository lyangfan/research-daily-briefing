#!/usr/bin/env python3
"""
论文采集器基类
定义所有采集器的通用接口
"""

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger()


class BaseFetcher(ABC):
    """论文采集器基类"""

    def __init__(self, config: Dict):
        """
        初始化采集器

        Args:
            config: 平台配置字典
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.name = self.__class__.__name__

    @abstractmethod
    def fetch(self, target_date: date) -> List[Dict]:
        """
        获取指定日期的论文列表

        Args:
            target_date: 目标日期

        Returns:
            论文列表，每个论文包含：
            - id: 论文唯一标识
            - title: 标题
            - authors: 作者列表
            - abstract: 摘要
            - url: 链接
            - published_date: 发布日期
            - platform: 平台名称
        """
        pass

    def _normalize_paper(self, paper: Dict, platform: str) -> Dict:
        """
        标准化论文数据格式

        Args:
            paper: 原始论文数据
            platform: 平台名称

        Returns:
            标准化后的论文数据
        """
        return {
            'id': paper.get('id', ''),
            'title': paper.get('title', '').strip(),
            'authors': paper.get('authors', []),
            'abstract': paper.get('abstract', '').strip(),
            'url': paper.get('url', ''),
            'published_date': paper.get('published_date', ''),
            'platform': platform,
            'categories': paper.get('categories', []),
            'raw': paper  # 保留原始数据
        }

    def _is_valid_paper(self, paper: Dict) -> bool:
        """
        验证论文数据是否有效

        Args:
            paper: 论文数据

        Returns:
            是否有效
        """
        if not paper.get('title'):
            return False
        if not paper.get('abstract'):
            return False
        if not paper.get('id'):
            return False
        return True

    def deduplicate(self, papers: List[Dict]) -> List[Dict]:
        """
        去重（基于论文ID）

        Args:
            papers: 论文列表

        Returns:
            去重后的论文列表
        """
        seen_ids = set()
        unique_papers = []

        for paper in papers:
            paper_id = paper.get('id')
            if paper_id and paper_id not in seen_ids:
                seen_ids.add(paper_id)
                unique_papers.append(paper)

        if len(papers) != len(unique_papers):
            logger.info(f'{self.name}: 去重前 {len(papers)} 篇，去重后 {len(unique_papers)} 篇')

        return unique_papers

    def filter_by_date(self, papers: List[Dict], target_date: date) -> List[Dict]:
        """
        按日期过滤论文

        Args:
            papers: 论文列表
            target_date: 目标日期

        Returns:
            符合日期的论文列表
        """
        filtered = []
        for paper in papers:
            pub_date = paper.get('published_date', '')
            if pub_date and str(target_date) in pub_date:
                filtered.append(paper)

        return filtered
