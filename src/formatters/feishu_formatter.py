#!/usr/bin/env python3
"""
飞书消息格式化器
将论文数据格式化为飞书富文本消息
"""

from datetime import date
from typing import Dict, List

from ..utils.logger import get_logger

logger = get_logger()


class FeishuFormatter:
    """飞书消息格式化器"""

    def __init__(self, config: Dict):
        """
        初始化格式化器

        Args:
            config: 格式化配置
        """
        self.config = config
        self.max_summary_papers = config.get('max_summary_papers', 0)  # 0 表示不限制

    def format_briefing(self, briefing_data: Dict) -> str:
        """
        格式化早报为飞书消息

        Args:
            briefing_data: 早报数据

        Returns:
            格式化后的消息文本
        """
        papers = briefing_data.get('papers', [])
        briefing_date = briefing_data.get('date', date.today().strftime('%Y-%m-%d'))

        # 限制论文数量（0 表示不限制）
        if self.max_summary_papers > 0:
            papers_to_show = papers[:self.max_summary_papers]
        else:
            papers_to_show = papers

        # 构建消息
        message_parts = [
            f"📅 科研早报 - {briefing_date}",
            "",
            self._format_overview(papers, briefing_data.get('total_count', len(papers))),
            "",
        ]

        # 添加每篇论文
        for i, paper in enumerate(papers_to_show, 1):
            message_parts.append(self._format_paper(i, paper))

        # 如果有更多论文
        if self.max_summary_papers > 0 and len(papers) > self.max_summary_papers:
            message_parts.append(f"\n... 还有 {len(papers) - self.max_summary_papers} 篇论文")

        # 添加结尾
        message_parts.extend([
            "",
            "━━━━━━━━━━━━━━━━━━",
            f"来源: {', '.join(set(p.get('platform', '') for p in papers))}",
            "数据更新: " + briefing_data.get('update_time', ''),
        ])

        return '\n'.join(message_parts)

    def _format_overview(self, papers: List[Dict], total_count: int) -> str:
        """
        格式化总览部分

        Args:
            papers: 论文列表
            total_count: 总数量

        Returns:
            总览文本
        """
        # 统计各平台数量
        platform_counts = {}
        for paper in papers:
            platform = paper.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        overview_parts = [
            f"📊 今日共发现 {total_count} 篇与「科研相关 AI Agent」的论文："
        ]

        for platform, count in sorted(platform_counts.items()):
            overview_parts.append(f"  • {platform}: {count} 篇")

        return '\n'.join(overview_parts)

    def _format_paper(self, index: int, paper: Dict) -> str:
        """
        格式化单篇论文

        Args:
            index: 序号
            paper: 论文数据

        Returns:
            论文格式化文本
        """
        # 平台图标
        platform_icons = {
            'arxiv': '📜',
            'biorxiv': '🧬',
            'medrxiv': '🏥',
            'ssrn': '📊',
        }
        icon = platform_icons.get(paper.get('platform', ''), '📄')

        parts = [
            f"{icon} 【{index}】{paper.get('title', '无标题')}",
        ]

        # 添加总结（如果有）
        if paper.get('summary'):
            parts.append(f"\n📝 {paper['summary']}")

        # 添加分类（如果有）
        categories = paper.get('categories', [])
        if categories:
            # 只显示前3个分类
            categories_str = ', '.join(categories[:3])
            if len(categories) > 3:
                categories_str += ' ...'
            parts.append(f"\n🏷️ 分类: {categories_str}")

        return '\n'.join(parts)

    def format_error_notification(self, error_message: str, date: str) -> str:
        """
        格式化错误通知

        Args:
            error_message: 错误消息
            date: 日期

        Returns:
            格式化的错误通知
        """
        return f"""⚠️ 早报生成失败

日期: {date}
错误: {error_message}

请检查日志获取更多信息。"""

    def format_success_notification(self, date: str, count: int) -> str:
        """
        格式化成功通知

        Args:
            date: 日期
            count: 论文数量

        Returns:
            格式化的成功通知
        """
        return f"""✅ 早报已生成

日期: {date}
论文数量: {count} 篇

已发送到飞书。"""

    def format_test_message(self) -> str:
        """
        格式化测试消息

        Returns:
            测试消息
        """
        return """🧪 早报系统测试消息

这是一条测试消息，用于验证飞书发送功能是否正常。

如果你看到这条消息，说明配置成功！
"""
