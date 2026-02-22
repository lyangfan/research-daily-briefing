#!/usr/bin/env python3
"""
基于智谱 AI Embedding 的语义过滤器
使用智谱 AI 的 Embedding API 进行语义相似度匹配
"""

import os
from typing import Dict, List
import numpy as np
import json
import requests

from ..utils.logger import get_logger

logger = get_logger()


class ZhipuEmbeddingFilter:
    """基于智谱 AI Embedding 的语义过滤器"""

    def __init__(self, config: Dict):
        """
        初始化智谱 Embedding 过滤器

        Args:
            config: 过滤器配置
        """
        self.config = config
        self.similarity_threshold = config.get('similarity_threshold', 0.75)
        self.model = config.get('model', 'embedding-3')
        self.max_papers = config.get('max_papers', 30)

        # API 配置
        self.api_key = os.getenv('ZHIPU_API_KEY') or config.get('api_key', '')
        if not self.api_key:
            raise ValueError('未设置 ZHIPU_API_KEY 环境变量或配置')

        self.api_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"

        # 查询文本（描述我们要找的内容）
        self.query = config.get('query', (
            "AI agents and multi-agent systems for scientific research, "
            "autonomous research assistants, LLM-powered scientific tools, "
            "machine learning agents for discovery and automation"
        ))

        # 预计算查询的 embedding
        self.query_embedding = self._get_embedding(self.query)

        logger.info(f'智谱 Embedding 过滤器初始化完成 (模型: {self.model}, 阈值: {self.similarity_threshold})')

    def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本的 embedding

        Args:
            text: 输入文本

        Returns:
            embedding 向量
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "input": text
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # 智谱 API 返回格式
            if 'data' in result and len(result['data']) > 0:
                return result['data'][0]['embedding']
            else:
                raise ValueError(f'API 返回格式错误: {result}')

        except Exception as e:
            logger.error(f'获取 embedding 失败: {e}')
            raise

    @staticmethod
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

        logger.info(f'开始智谱 Embedding 过滤，共 {len(papers)} 篇论文')

        # 限制数量
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
                similarity = self.cosine_similarity(self.query_embedding, paper_embedding)

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

        logger.info(f'智谱 Embedding 过滤完成，相关论文 {len(relevant_papers)} 篇')
        return relevant_papers

    def filter_papers_batch(self, papers: List[Dict]) -> List[Dict]:
        """
        批量过滤（一次调用处理多篇论文）

        �谱 API 支持一次请求最多处理多个文本

        Args:
            papers: 论文列表

        Returns:
            相关的论文列表
        """
        if not papers:
            return []

        logger.info(f'开始批量智谱 Embedding 过滤，共 {len(papers)} 篇论文')

        # 限制数量
        if len(papers) > self.max_papers:
            papers = papers[:self.max_papers]

        # 准备文本
        texts = []
        for paper in papers:
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
            texts.append(text)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "input": texts
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            # 计算相似度
            relevant_papers = []
            embeddings = result.get('data', [])

            for i, (paper, embedding_data) in enumerate(zip(papers, embeddings)):
                paper_embedding = embedding_data['embedding']
                similarity = self.cosine_similarity(self.query_embedding, paper_embedding)

                if similarity >= self.similarity_threshold:
                    paper['similarity_score'] = similarity
                    relevant_papers.append(paper)
                    logger.info(f'[{i+1}/{len(papers)}] ✓ ({similarity:.3f}) {paper["title"][:50]}...')

            # 按相似度排序
            relevant_papers.sort(key=lambda p: p.get('similarity_score', 0), reverse=True)

            logger.info(f'批量智谱 Embedding 过滤完成，相关论文 {len(relevant_papers)} 篇')
            return relevant_papers

        except Exception as e:
            logger.error(f'批量处理失败: {e}，降级为逐个处理')
            return self.filter_papers(papers)
