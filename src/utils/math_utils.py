#!/usr/bin/env python3
"""
数学工具函数
"""

from typing import List
import numpy as np


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    计算余弦相似度

    Args:
        a: 向量 a
        b: 向量 b

    Returns:
        相似度分数 (0-1)
    """
    a_array = np.array(a)
    b_array = np.array(b)

    dot_product = np.dot(a_array, b_array)
    norm_a = np.linalg.norm(a_array)
    norm_b = np.linalg.norm(b_array)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)
