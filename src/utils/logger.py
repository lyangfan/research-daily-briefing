#!/usr/bin/env python3
"""
日志工具模块
提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import colorlog


def setup_logger(
    name: str = "research_briefing",
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    retain_days: int = 30
) -> logging.Logger:
    """
    设置并返回一个配置好的日志记录器

    Args:
        name: 日志记录器名称
        log_dir: 日志目录，如果为 None 则使用项目根目录下的 logs
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        retain_days: 保留日志的天数

    Returns:
        配置好的 Logger 实例
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 控制台处理器（输出到 stderr，避免与 OpenClaw 捕获的 stdout 混淆）
    import sys
    console_handler = colorlog.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_format = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 按日期命名日志文件
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f'{name}_{today}.log'

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        # 清理旧日志
        _cleanup_old_logs(log_dir, retain_days)

    return logger


def _cleanup_old_logs(log_dir: Path, retain_days: int) -> None:
    """
    清理超过指定天数的旧日志文件

    Args:
        log_dir: 日志目录
        retain_days: 保留天数
    """
    try:
        now = datetime.now()
        for log_file in log_dir.glob('*.log'):
            # 获取文件修改时间
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            age = (now - mtime).days

            if age > retain_days:
                log_file.unlink()
                print(f'已删除旧日志文件: {log_file}')
    except Exception as e:
        print(f'清理旧日志时出错: {e}')


def get_logger(name: str = "research_briefing") -> logging.Logger:
    """
    获取已配置的日志记录器（用于模块导入）

    Args:
        name: 日志记录器名称

    Returns:
        Logger 实例
    """
    return logging.getLogger(name)
