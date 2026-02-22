#!/usr/bin/env python3
"""
数据存储工具模块
使用 SQLite 存储论文数据，提供更好的扩展性和性能
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger()


class PaperStorage:
    """论文存储管理类 (SQLite 版本)"""

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

        # 数据库文件路径
        self.db_path = self.storage_dir / "briefings.db"

        # 初始化数据库
        self._init_db()

        logger.info(f'存储系统初始化完成 (数据库: {self.db_path})')

    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 创建已处理论文表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_papers (
                    paper_id TEXT PRIMARY KEY,
                    processed_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT  -- JSON 格式的额外信息
                )
            ''')

            # 创建索引以提高查询性能
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_processed_date
                ON processed_papers(processed_date)
            ''')

            # 创建早报表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS briefings (
                    date DATE PRIMARY KEY,
                    content TEXT NOT NULL,  -- JSON 格式的早报内容
                    paper_count INTEGER NOT NULL,
                    platforms TEXT,  -- JSON 数组
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def is_paper_processed(self, paper_id: str) -> bool:
        """
        检查论文是否已处理过

        Args:
            paper_id: 论文唯一标识

        Returns:
            是否已处理
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM processed_papers WHERE paper_id = ?',
                (paper_id,)
            )
            return cursor.fetchone() is not None

    def mark_paper_processed(self, paper_id: str, process_date: str, metadata: Dict = None) -> None:
        """
        标记论文为已处理

        Args:
            paper_id: 论文唯一标识
            process_date: 处理日期 (YYYY-MM-DD)
            metadata: 额外的元数据
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO processed_papers (paper_id, processed_date, metadata)
                VALUES (?, ?, ?)
            ''', (paper_id, process_date, json.dumps(metadata) if metadata else None))
            conn.commit()

    def mark_papers_processed(self, papers: List[Dict], process_date: str) -> None:
        """
        批量标记论文为已处理

        Args:
            papers: 论文列表
            process_date: 处理日期 (YYYY-MM-DD)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            for paper in papers:
                paper_id = paper.get('id') or paper.get('paper_id')
                if paper_id:
                    # 只保留必要的元数据
                    metadata = {
                        'title': paper.get('title', '')[:100],  # 只保留前100字符
                        'platform': paper.get('platform', ''),
                        'categories': paper.get('categories', [])[:5]  # 只保留前5个分类
                    }

                    cursor.execute('''
                        INSERT OR REPLACE INTO processed_papers (paper_id, processed_date, metadata)
                        VALUES (?, ?, ?)
                    ''', (paper_id, process_date, json.dumps(metadata)))

            conn.commit()
            logger.info(f'批量标记 {len(papers)} 篇论文为已处理')

    def save_briefing(self, briefing_date: str, briefing_data: Dict) -> Path:
        """
        保存早报数据

        Args:
            briefing_date: 日期 (YYYY-MM-DD)
            briefing_data: 早报数据

        Returns:
            保存的文件路径（用于兼容，实际存储在数据库中）
        """
        # 同时保存到 JSON 文件（用于备份和兼容性）
        briefings_dir = self.storage_dir / "briefings"
        briefings_dir.mkdir(parents=True, exist_ok=True)

        briefing_file = briefings_dir / f"{briefing_date}.json"

        # 保存 JSON 备份
        with open(briefing_file, 'w', encoding='utf-8') as f:
            json.dump(briefing_data, f, ensure_ascii=False, indent=2)

        # 保存到数据库
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO briefings (date, content, paper_count, platforms, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                briefing_date,
                json.dumps(briefing_data, ensure_ascii=False),
                len(briefing_data.get('papers', [])),
                json.dumps(briefing_data.get('platforms', []), ensure_ascii=False)
            ))
            conn.commit()

        logger.info(f'早报已保存: {briefing_date}')
        return briefing_file

    def load_briefing(self, briefing_date: str) -> Optional[Dict]:
        """
        加载指定日期的早报数据

        Args:
            briefing_date: 日期 (YYYY-MM-DD)

        Returns:
            早报数据，如果不存在返回 None
        """
        # 优先从数据库读取
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT content FROM briefings WHERE date = ?',
                (briefing_date,)
            )
            row = cursor.fetchone()

            if row:
                return json.loads(row['content'])

        # 回退到 JSON 文件
        briefing_file = self.storage_dir / "briefings" / f"{briefing_date}.json"
        if briefing_file.exists():
            try:
                with open(briefing_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f'加载 JSON 早报失败: {e}')
                return None

        return None

    def get_latest_briefing(self) -> Optional[Dict]:
        """
        获取最新的早报数据

        Returns:
            最新的早报数据，如果没有返回 None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, content FROM briefings
                ORDER BY date DESC
                LIMIT 1
            ''')
            row = cursor.fetchone()

            if row:
                return json.loads(row['content'])
        return None

    def cleanup_old_data(self) -> None:
        """
        清理超过保留天数的数据

        使用事务批量删除，提高性能
        """
        cutoff_date = datetime.now() - timedelta(days=self.retain_days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 清理旧的早报记录
            cursor.execute('''
                DELETE FROM briefings WHERE date < ?
            ''', (cutoff_str,))
            briefings_deleted = cursor.rowcount

            # 清理旧的论文记录
            cursor.execute('''
                DELETE FROM processed_papers WHERE processed_date < ?
            ''', (cutoff_str,))
            papers_deleted = cursor.rowcount

            # 执行 VACUUM 回收磁盘空间
            cursor.execute('VACUUM')

            conn.commit()

            if briefings_deleted > 0 or papers_deleted > 0:
                logger.info(f'清理旧数据: {briefings_deleted} 条早报, {papers_deleted} 条论文记录')

    def get_processed_papers_by_date(self, process_date: str) -> List[str]:
        """
        获取指定日期处理的所有论文ID

        Args:
            process_date: 日期 (YYYY-MM-DD)

        Returns:
            论文ID列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT paper_id FROM processed_papers
                WHERE processed_date = ?
                ORDER BY created_at
            ''', (process_date,))

            return [row['paper_id'] for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """
        获取存储统计信息

        Returns:
            统计信息字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 统计已处理论文数
            cursor.execute('SELECT COUNT(*) as count FROM processed_papers')
            total_processed = cursor.fetchone()['count']

            # 统计早报数
            cursor.execute('SELECT COUNT(*) as count FROM briefings')
            total_briefings = cursor.fetchone()['count']

            # 统计最早和最晚的记录
            cursor.execute('''
                SELECT
                    MIN(processed_date) as earliest,
                    MAX(processed_date) as latest
                FROM processed_papers
            ''')
            date_range = cursor.fetchone()

            # 数据库文件大小
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                'total_processed_papers': total_processed,
                'total_briefings': total_briefings,
                'earliest_record': date_range['earliest'] if date_range['earliest'] else None,
                'latest_record': date_range['latest'] if date_range['latest'] else None,
                'storage_type': 'SQLite',
                'database_path': str(self.db_path),
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / 1024 / 1024, 2)
            }

    def optimize_database(self) -> None:
        """
        优化数据库性能
        - 重建索引
        - 回收空间
        - 分析表统计信息
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 分析表以优化查询计划
            cursor.execute('ANALYZE')

            # 回收空间
            cursor.execute('VACUUM')

            # 重建索引
            cursor.execute('REINDEX')

            conn.commit()

            logger.info('数据库优化完成')
