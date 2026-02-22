#!/usr/bin/env python3
"""
科研早报系统主程序
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.fetchers.biorxiv_fetcher import BiorxivFetcher, MedrxivFetcher
from src.processors.ai_filter import AIFilter
from src.processors.embedding_filter import EmbeddingFilter
from src.processors.zhipu_embedding_filter import ZhipuEmbeddingFilter
from src.processors.summarizer import PaperSummarizer
from src.formatters.feishu_formatter import FeishuFormatter
from src.utils.logger import setup_logger
from src.utils.storage import PaperStorage
from src.utils.pdf_downloader import PDFDownloader

# 加载环境变量
load_dotenv()


class ResearchBriefingSystem:
    """科研早报系统"""

    def __init__(self, config_file: str = None):
        """
        初始化系统

        Args:
            config_file: 配置文件路径
        """
        # 加载配置
        if config_file is None:
            config_file = PROJECT_ROOT / 'config.yaml'
        else:
            config_file = Path(config_file)

        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # 设置日志
        log_dir = PROJECT_ROOT / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger(
            'research_briefing',
            log_dir=log_dir,
            level=self.config.get('logging', {}).get('level', 'INFO')
        )

        # 初始化存储
        storage_config = self.config.get('storage', {})
        storage_dir = PROJECT_ROOT / storage_config.get('briefings_dir', 'data/briefings')
        self.storage = PaperStorage(
            storage_dir=storage_dir,
            retain_days=storage_config.get('retain_days', 90)
        )

        # 初始化采集器
        self.fetchers = self._init_fetchers()

        # 初始化过滤器（根据配置选择模式）
        filter_config = self.config.get('ai_filter', {})
        filter_mode = filter_config.get('mode', 'hybrid')
        embedding_config = filter_config.get('embedding', {})

        if filter_mode == 'embedding':
            # 选择 Embedding 提供商
            provider = embedding_config.get('provider', 'zhipu')
            if provider == 'zhipu':
                self.ai_filter = ZhipuEmbeddingFilter(embedding_config)
            else:
                self.ai_filter = EmbeddingFilter(embedding_config)
        elif filter_mode == 'claude':
            self.ai_filter = AIFilter(filter_config)
        else:  # hybrid 或 keywords
            self.ai_filter = AIFilter(filter_config)

        # 初始化总结器
        summarizer_config = {**self.config.get('summarizer', {}), **self.config.get('ai_filter', {})}
        # 添加 PDF 下载配置
        pdf_config = self.config.get('pdf_download', {})
        if pdf_config.get('enabled', False):
            summarizer_config['pdf_download'] = pdf_config

        self.summarizer = PaperSummarizer(summarizer_config)

        # 初始化格式化器
        self.formatter = FeishuFormatter(
            {**self.config.get('openclaw', {}), **self.config.get('ai_filter', {})}
        )

        self.logger.info('科研早报系统初始化完成')

    def _init_fetchers(self) -> list:
        """初始化采集器"""
        fetchers = []
        platforms = self.config.get('platforms', {})

        # arXiv
        if platforms.get('arxiv', {}).get('enabled', False):
            fetchers.append(ArxivFetcher(platforms['arxiv']))

        # bioRxiv
        if platforms.get('biorxiv', {}).get('enabled', False):
            fetchers.append(BiorxivFetcher(platforms['biorxiv']))

        # medRxiv
        if platforms.get('medrxiv', {}).get('enabled', False):
            fetchers.append(MedrxivFetcher(platforms['medrxiv']))

        return fetchers

    def fetch_and_process(self, target_date: date = None, days_back: int = 1) -> dict:
        """
        采集并处理论文

        Args:
            target_date: 目标日期
            days_back: 向前获取多少天的论文

        Returns:
            早报数据
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)  # 默认获取昨天的

        self.logger.info(f'开始处理日期: {target_date}')

        # 1. 采集论文
        all_papers = []
        for fetcher in self.fetchers:
            try:
                papers = fetcher.fetch(target_date, days_back)
                all_papers.extend(papers)
            except Exception as e:
                self.logger.error(f'采集器 {fetcher.name} 失败: {e}')

        self.logger.info(f'总计采集到 {len(all_papers)} 篇论文')

        if not all_papers:
            self.logger.warning('未采集到任何论文')
            return self._create_empty_briefing(target_date)

        # 2. 去重
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            paper_id = paper.get('id')
            # 检查是否已处理过
            if not self.storage.is_paper_processed(paper_id):
                if paper_id not in seen_ids:
                    seen_ids.add(paper_id)
                    unique_papers.append(paper)
            else:
                self.logger.debug(f'论文已处理过: {paper_id}')

        self.logger.info(f'去重后剩余 {len(unique_papers)} 篇新论文')

        if not unique_papers:
            self.logger.warning('没有新的论文需要处理')
            return self._create_empty_briefing(target_date)

        # 3. AI 过滤
        relevant_papers = self.ai_filter.filter_papers(unique_papers)

        if not relevant_papers:
            self.logger.warning('AI 过滤后没有相关论文')
            return self._create_empty_briefing(target_date)

        # 4. 下载 PDF（如果启用）
        pdf_config = self.config.get('pdf_download', {})
        if pdf_config.get('enabled', False):
            self.logger.info(f'开始下载 {len(relevant_papers)} 篇论文的 PDF...')
            pdf_downloader = PDFDownloader(pdf_config)

            for i, paper in enumerate(relevant_papers):
                if paper.get('pdf_url'):
                    self.logger.debug(f'[{i+1}/{len(relevant_papers)}] 下载 PDF: {paper.get("title", "")[:50]}...')
                    pdf_path = pdf_downloader.download_paper(paper)
                    if pdf_path:
                        paper['pdf_path'] = pdf_path

            # 输出存储信息
            storage_info = pdf_downloader.get_storage_info()
            self.logger.info(f'PDF 存储信息: {storage_info}')

        # 5. 生成总结
        summarized_papers = self.summarizer.summarize_papers(relevant_papers)

        # 6. 标记为已处理
        self.storage.mark_papers_processed(summarized_papers, target_date.strftime('%Y-%m-%d'))

        # 7. 构建早报数据
        briefing_data = {
            'date': target_date.strftime('%Y-%m-%d'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'papers': summarized_papers,
            'total_count': len(summarized_papers),
            'platforms': list(set(p.get('platform', '') for p in summarized_papers))
        }

        # 8. 保存早报
        self.storage.save_briefing(target_date.strftime('%Y-%m-%d'), briefing_data)

        self.logger.info(f'早报生成完成，包含 {len(summarized_papers)} 篇论文')
        return briefing_data

    def send_briefing(self, briefing_date: date = None) -> bool:
        """
        发送早报到飞书

        Args:
            briefing_date: 早报日期

        Returns:
            是否发送成功
        """
        if briefing_date is None:
            briefing_date = date.today() - timedelta(days=1)

        date_str = briefing_date.strftime('%Y-%m-%d')

        # 加载早报数据
        briefing_data = self.storage.load_briefing(date_str)

        if not briefing_data:
            self.logger.error(f'未找到 {date_str} 的早报数据')
            return False

        # 格式化消息
        message = self.formatter.format_briefing(briefing_data)

        # 获取飞书目标
        feishu_target = os.getenv('OPENCLAW_FEISHI_TARGET')
        if not feishu_target:
            # 从配置文件读取
            feishu_target = self.config.get('openclaw', {}).get('feishu_target', '')

        if not feishu_target:
            self.logger.error('未配置飞书目标，请设置 OPENCLAW_FEISHI_TARGET 环境变量')
            return False

        # 发送（这里使用 OpenClaw CLI）
        try:
            import subprocess
            result = subprocess.run(
                ['openclaw', 'message', 'send',
                 '--channel', 'feishu',
                 '--target', feishu_target,
                 '--message', message],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.info(f'早报已发送到飞书 ({date_str})')
                return True
            else:
                self.logger.error(f'发送失败: {result.stderr}')
                return False

        except Exception as e:
            self.logger.error(f'发送早报时出错: {e}')
            return False

    def _create_empty_briefing(self, target_date: date) -> dict:
        """创建空早报"""
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'papers': [],
            'total_count': 0,
            'platforms': []
        }

    def cleanup(self):
        """清理旧数据"""
        self.storage.cleanup_old_data()

        # 定期优化数据库
        if self.config.get('storage', {}).get('auto_optimize', False):
            import random
            # 10% 的概率执行优化（避免每次都执行）
            if random.random() < 0.1:
                self.storage.optimize_database()

        self.logger.info('旧数据清理完成')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='科研早报系统')
    parser.add_argument(
        'action',
        choices=['fetch', 'send', 'test', 'cleanup', 'stats'],
        help='操作: fetch(采集处理), send(发送), test(测试), cleanup(清理), stats(统计)'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='目标日期 (YYYY-MM-DD)，默认昨天'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=1,
        help='向前获取多少天的论文 (默认: 1)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )

    args = parser.parse_args()

    # 解析日期
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f'错误: 无效的日期格式 {args.date}')
            sys.exit(1)

    # 初始化系统
    system = ResearchBriefingSystem(args.config)

    # 执行操作
    if args.action == 'fetch':
        result = system.fetch_and_process(target_date, args.days_back)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.action == 'send':
        success = system.send_briefing(target_date)
        sys.exit(0 if success else 1)

    elif args.action == 'test':
        # 测试模式：发送测试消息
        message = system.formatter.format_test_message()
        print('测试消息:')
        print(message)
        print('\n如需发送到飞书，请使用 send 命令')

    elif args.action == 'cleanup':
        system.cleanup()
        print('清理完成')

    elif args.action == 'stats':
        stats = system.storage.get_statistics()
        print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
