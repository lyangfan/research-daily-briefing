#!/usr/bin/env python3
"""
基于 Embedding 的语义过滤器
使用 OpenAI Embeddings API 进行语义相似度匹配
"""

import os
from typing import Dict, List
import numpy as np

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from ..utils.logger import get_logger
from ..utils.math_utils import cosine_similarity

logger = get_logger()


class EmbeddingFilter:
    """基于 Embedding 的语义过滤器"""

    def __init__(self, config: Dict):
        """
        初始化 Embedding 过滤器

        Args:
            config: 过滤器配置
        """
        self.config = config
        self.similarity_threshold = config.get('similarity_threshold', 0.75)
        self.model = config.get('model', 'text-embedding-3-small')
        self.max_papers = config.get('max_papers', 30)

        # 查询文本（描述我们要找的内容）
        self.query = config.get('query', (
            "AI agents and multi-agent systems for scientific research, "
            "autonomous research assistants, LLM-powered scientific tools, "
            "machine learning agents for discovery and automation"
        ))

        # 初始化 OpenAI 客户端
        if not HAS_OPENAI:
            raise ImportError('请安装 openai 库: pip install openai')

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('未设置 OPENAI_API_KEY 环境变量')

        self.client = OpenAI(api_key=api_key)

        # 预计算查询的 embedding
        self.query_embedding = self._get_embedding(self.query)

        logger.info(f'Embedding 过滤器初始化完成 (阈值: {self.similarity_threshold})')

    def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本的 embedding

        Args:
            text: 输入文本

        Returns:
            embedding 向量
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f'获取 embedding 失败: {e}')
            raise

    def filter_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        使用 embedding 相似度过滤论文

        Args:
            papers: 论文列表

        Returns:
            相关的论文列表
        """
        if not papers:
            return []

        logger.info(f'开始 Embedding 过滤，共 {len(papers)} 篇论文')

        # 限制数量（embedding 计算需要时间和费用）
        if len(papers) > self.max_papers:
            logger.info(f'限制数量为 {self.max_papers} 篇')
            papers = papers[:self.max_papers]

        relevant_papers = []

        for i, paper in enumerate(papers):
            try:
                # 计算论文的 embedding
                # 使用标题 + 摘要的组合
                text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
                paper_embedding = self._get_embedding(text)

                # 计算相似度
                similarity = cosine_similarity(self.query_embedding, paper_embedding)

                if similarity >= self.similarity_threshold:
                    paper['similarity_score'] = similarity
                    relevant_papers.append(paper)
                    logger.info(f'[{i+1}/{len(papers)}] ✓ ({similarity:.3f}) {paper["title"][:50]}...')
                else:
                    logger.debug(f'[{i+1}/{len(papers)}] ✗ ({similarity:.3f}) {paper["title"][:50]}...')

            except Exception as e:
                logger.error(f'处理论文时出错: {e}')
                # 出错时跳过这篇论文
                continue

        # 按相似度排序
        relevant_papers.sort(key=lambda p: p.get('similarity_score', 0), reverse=True)

        logger.info(f'Embedding 过滤完成，相关论文 {len(relevant_papers)} 篇')
        return relevant_papers

    def filter_papers_batch(self, papers: List[Dict]) -> List[Dict]:
        """
        批量过滤（一次调用处理多篇论文）

        Args:
            papers: 论文列表

        Returns:
            相关的论文列表
        """
        if not papers:
            return []

        logger.info(f'开始批量 Embedding 过滤，共 {len(papers)} 篇论文')

        # 准备文本
        texts = []
        for paper in papers:
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
            texts.append(text)

        try:
            # 批量获取 embeddings
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )

            # 计算相似度
            relevant_papers = []
            for i, (paper, embedding_data) in enumerate(zip(papers, response.data)):
                similarity = cosine_similarity(self.query_embedding, embedding_data.embedding)

                if similarity >= self.similarity_threshold:
                    paper['similarity_score'] = similarity
                    relevant_papers.append(paper)
                    logger.info(f'[{i+1}/{len(papers)}] ✓ ({similarity:.3f}) {paper["title"][:50]}...')

            # 按相似度排序
            relevant_papers.sort(key=lambda p: p.get('similarity_score', 0), reverse=True)

            logger.info(f'批量 Embedding 过滤完成，相关论文 {len(relevant_papers)} 篇')
            return relevant_papers

        except Exception as e:
            logger.error(f'批量处理失败: {e}，降级为逐个处理')
            return self.filter_papers(papers)
