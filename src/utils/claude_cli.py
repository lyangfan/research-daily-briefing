#!/usr/bin/env python3
"""
Claude Code CLI 工具函数
"""

import os
import subprocess
from typing import Optional

from .logger import get_logger

logger = get_logger()

# Claude CLI 常见安装路径
CLAUDE_COMMON_PATHS = [
    os.path.expanduser('~/.local/bin/claude'),
    '/usr/local/bin/claude',
    os.path.expanduser('~/.claude/local/claude'),
]


def find_claude() -> Optional[str]:
    """
    查找 Claude Code CLI 路径

    Returns:
        claude 命令路径，未找到返回 None
    """
    # 1. 检查 PATH 中的 claude
    try:
        result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug(f'查找 claude 命令失败: {e}')

    # 2. 检查常见安装位置
    for path in CLAUDE_COMMON_PATHS:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    return None
