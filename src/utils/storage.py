#!/usr/bin/env python3
"""
数据存储工具模块
处理论文数据的存储和去重
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from .logger import get_logger

logger = get_logger()


class PaperStorage:
    """论文存储管理类"""

    def __init__(self, storage_dir: Path, retain_days: int = 90):
        """
        初始化存储管理器

        Args:
            storage_dir: 存储目录路径
            retain_days: 数据保留天数
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.retain_days = retain_days

        # 已处理论文的记录文件
        self.processed_file = self.storage_dir.parent / "processed_papers.json"
        self.processed_papers: Dict[str, str] = self._load_processed_papers()

    def _load_processed_papers(self) -> Dict[str, str]:
        """
        加载已处理论文的记录

        Returns:
            {paper_id: date} 的字典
        """
        if self.processed_file.exists():
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f'加载已处理论文记录失败: {e}')
                return {}
        return {}

    def _save_processed_papers(self) -> None:
        """保存已处理论文的记录"""
        try:
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_papers, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存已处理论文记录失败: {e}')

    def is_paper_processed(self, paper_id: str) -> bool:
        """
        检查论文是否已处理过

        Args:
            paper_id: 论文唯一标识

        Returns:
            是否已处理
        """
        return paper_id in self.processed_papers

    def mark_paper_processed(self, paper_id: str, date: str) -> None:
        """
        标记论文为已处理

        Args:
            paper_id: 论文唯一标识
            date: 处理日期 (YYYY-MM-DD)
        """
        self.processed_papers[paper_id] = date
        self._save_processed_papers()

    def mark_papers_processed(self, papers: List[Dict], date: str) -> None:
        """
        批量标记论文为已处理

        Args:
            papers: 论文列表
            date: 处理日期 (YYYY-MM-DD)
        """
        for paper in papers:
            paper_id = paper.get('id') or paper.get('paper_id')
            if paper_id:
                self.processed_papers[paper_id] = date
        self._save_processed_papers()

    def save_briefing(self, date: str, briefing_data: Dict) -> Path:
        """
        保存早报数据

        Args:
            date: 日期 (YYYY-MM-DD)
            briefing_data: 早报数据

        Returns:
            保存的文件路径
        """
        briefings_dir = self.storage_dir / "briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        briefing_file = briefings_dir / f"{date}.json"
        try:
            with open(briefing_file, 'w', encoding='utf-8') as f:
                json.dump(briefing_data, f, ensure_ascii=False, indent=2)
            logger.info(f'早报已保存: {briefing_file}')
            return briefing_file
        except Exception as e:
            logger.error(f'保存早报失败: {e}')
            raise

    def load_briefing(self, date: str) -> Optional[Dict]:
        """
        加载指定日期的早报数据

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            早报数据，如果不存在返回 None
        """
        briefing_file = self.storage_dir / "briefings" / f"{date}.json"
        if briefing_file.exists():
            try:
                with open(briefing_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f'加载早报失败: {e}')
                return None
        return None

    def get_latest_briefing(self) -> Optional[Dict]:
        """
        获取最新的早报数据

        Returns:
            最新的早报数据，如果没有返回 None
        """
        briefings_dir = self.storage_dir / "briefings"
        if not briefings_dir.exists():
            return None

        briefing_files = sorted(briefings_dir.glob('*.json'), reverse=True)
        if briefing_files:
            return self.load_briefing(briefing_files[0].stem)
        return None

    def cleanup_old_data(self) -> None:
        """清理超过保留天数的数据"""
        cutoff_date = datetime.now() - timedelta(days=self.retain_days)

        # 清理旧的早报文件
        briefings_dir = self.storage_dir / "briefings"
        if briefings_dir.exists():
            for briefing_file in briefings_dir.glob('*.json'):
                try:
                    # 从文件名提取日期
                    file_date = datetime.strptime(briefing_file.stem, '%Y-%m-%d')
                    if file_date < cutoff_date:
                        briefing_file.unlink()
                        logger.info(f'已删除旧早报: {briefing_file}')
                except Exception as e:
                    logger.warning(f'清理早报文件 {briefing_file} 时出错: {e}')

        # 清理已处理论文记录中的旧条目
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        to_remove = [
            paper_id for paper_id, date in self.processed_papers.items()
            if date < cutoff_str
        ]
        for paper_id in to_remove:
            del self.processed_papers[paper_id]

        if to_remove:
            self._save_processed_papers()
            logger.info(f'已清理 {len(to_remove)} 条旧论文记录')

    def get_processed_papers_by_date(self, date: str) -> List[str]:
        """
        获取指定日期处理的所有论文ID

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            论文ID列表
        """
        return [
            paper_id for paper_id, paper_date in self.processed_papers.items()
            if paper_date == date
        ]

    def get_statistics(self) -> Dict:
        """
        获取存储统计信息

        Returns:
            统计信息字典
        """
        briefings_dir = self.storage_dir / "briefings"

        briefing_count = 0
        if briefings_dir.exists():
            briefing_count = len(list(briefings_dir.glob('*.json')))

        return {
            'total_processed_papers': len(self.processed_papers),
            'total_briefings': briefing_count,
            'storage_dir': str(self.storage_dir),
            'processed_file': str(self.processed_file)
        }
