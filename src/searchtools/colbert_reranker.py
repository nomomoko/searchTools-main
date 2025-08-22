#!/usr/bin/env python3
"""
ColBERT重排序系统

ColBERT (Contextualized Late Interaction over BERT) 是一种高效的多向量检索和重排序方法，
特别适合学术文献的精确匹配和语义理解。

核心特点：
- 多向量表示：每个token都有独立的向量表示
- 延迟交互：在检索时才计算query-document交互
- 高效性：比传统cross-encoder快100倍以上
- 精确性：保持接近cross-encoder的准确性

学术优化：
- 针对科学术语的特殊处理
- 引用关系建模
- 多字段融合（标题、摘要、关键词）
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class ColBERTConfig:
    """ColBERT配置类"""
    model_name: str = "colbert-ir/colbertv2.0"  # 或使用学术优化版本
    dim: int = 128  # embedding维度
    similarity: str = "cosine"  # cosine, l2, dot
    max_query_length: int = 32
    max_doc_length: int = 180
    mask_punctuation: bool = True
    attend_to_mask_tokens: bool = False
    interaction: str = "colbert"  # colbert, maxsim
    
    # 学术优化配置
    academic_mode: bool = True
    field_weights: Dict[str, float] = None  # 字段权重
    citation_boost: float = 1.2  # 引用关系加权
    author_boost: float = 1.1   # 作者权威性加权
    
    # 性能配置
    batch_size: int = 32
    device: str = "cpu"
    enable_caching: bool = True
    cache_size: int = 1000

    def __post_init__(self):
        if self.field_weights is None:
            self.field_weights = {
                "title": 0.4,
                "abstract": 0.5,
                "keywords": 0.1
            }

class ColBERTReranker:
    """ColBERT重排序器
    
    实现基于ColBERT的多向量重排序算法，
    专门针对学术文献搜索进行优化。
    """
    
    def __init__(self, config: ColBERTConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.cache = {} if config.enable_caching else None
        self.stats = {
            'total_queries': 0,
            'total_docs': 0,
            'total_time': 0.0,
            'cache_hits': 0
        }
    
    def load_model(self):
        """加载ColBERT模型"""
        try:
            # 尝试使用官方ColBERT库
            try:
                from colbert import Indexer, Searcher
                from colbert.infra import Run, RunConfig, ColBERTConfig as CBConfig
                
                logger.info("Using official ColBERT library")
                self._load_official_colbert()
                
            except ImportError:
                # 回退到transformers实现
                logger.info("Official ColBERT not available, using transformers implementation")
                self._load_transformers_colbert()
                
        except Exception as e:
            logger.error(f"Failed to load ColBERT model: {e}")
            raise
    
    def _load_official_colbert(self):
        """加载官方ColBERT模型"""
        from colbert.modeling.checkpoint import Checkpoint
        
        checkpoint = Checkpoint(self.config.model_name, colbert_config=None)
        self.model = checkpoint
        logger.info("Official ColBERT model loaded successfully")
    
    def _load_transformers_colbert(self):
        """使用transformers加载ColBERT风格模型"""
        from transformers import AutoTokenizer, AutoModel
        
        # 使用BGE-M3的ColBERT模式或其他兼容模型
        model_name = "BAAI/bge-m3"  # 支持ColBERT模式
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
        if self.config.device == "cuda":
            import torch
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info("ColBERT model loaded on GPU")
            else:
                logger.warning("CUDA not available, using CPU")
        
        logger.info("Transformers-based ColBERT model loaded successfully")
    
    def encode_query(self, query: str) -> np.ndarray:
        """编码查询为多向量表示"""
        if self.model is None:
            self.load_model()
        
        # 检查缓存
        cache_key = f"query:{query}"
        if self.cache and cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        try:
            if hasattr(self.model, 'queryFromText'):
                # 官方ColBERT
                Q = self.model.queryFromText([query])
                query_vectors = Q.cpu().numpy()
            else:
                # Transformers实现
                query_vectors = self._encode_with_transformers(query, is_query=True)
            
            # 保存到缓存
            if self.cache:
                if len(self.cache) >= self.config.cache_size:
                    # 简单LRU：删除第一个
                    first_key = next(iter(self.cache))
                    del self.cache[first_key]
                self.cache[cache_key] = query_vectors
            
            return query_vectors
            
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            raise
    
    def encode_documents(self, documents: List[Dict]) -> List[np.ndarray]:
        """编码文档为多向量表示"""
        if self.model is None:
            self.load_model()
        
        doc_vectors = []
        
        for doc in documents:
            # 构建文档文本
            doc_text = self._build_document_text(doc)
            
            # 检查缓存
            cache_key = f"doc:{hash(doc_text)}"
            if self.cache and cache_key in self.cache:
                self.stats['cache_hits'] += 1
                doc_vectors.append(self.cache[cache_key])
                continue
            
            try:
                if hasattr(self.model, 'docFromText'):
                    # 官方ColBERT
                    D = self.model.docFromText([doc_text])
                    vectors = D.cpu().numpy()[0]
                else:
                    # Transformers实现
                    vectors = self._encode_with_transformers(doc_text, is_query=False)
                
                doc_vectors.append(vectors)
                
                # 保存到缓存
                if self.cache:
                    if len(self.cache) >= self.config.cache_size:
                        first_key = next(iter(self.cache))
                        del self.cache[first_key]
                    self.cache[cache_key] = vectors
                
            except Exception as e:
                logger.error(f"Error encoding document: {e}")
                # 返回零向量作为fallback
                vectors = np.zeros((self.config.max_doc_length, self.config.dim))
                doc_vectors.append(vectors)
        
        return doc_vectors
    
    def _encode_with_transformers(self, text: str, is_query: bool = False) -> np.ndarray:
        """使用transformers编码文本"""
        import torch
        
        max_length = self.config.max_query_length if is_query else self.config.max_doc_length
        
        # Tokenize
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        )
        
        if self.config.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # 获取token-level embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            token_embeddings = outputs.last_hidden_state[0]  # [seq_len, hidden_size]
            
            # 投影到ColBERT维度
            if token_embeddings.size(-1) != self.config.dim:
                # 简单线性投影
                projection = torch.nn.Linear(token_embeddings.size(-1), self.config.dim)
                if self.config.device == "cuda":
                    projection = projection.cuda()
                token_embeddings = projection(token_embeddings)
            
            # L2归一化
            token_embeddings = torch.nn.functional.normalize(token_embeddings, p=2, dim=-1)
            
            return token_embeddings.cpu().numpy()
    
    def _build_document_text(self, doc: Dict) -> str:
        """构建文档文本，支持多字段融合"""
        if not self.config.academic_mode:
            # 简单模式：只使用标题和摘要
            title = doc.get('title', '')
            abstract = doc.get('abstract', '')
            return f"{title} {abstract}".strip()
        
        # 学术模式：多字段加权融合
        parts = []
        
        # 标题（高权重）
        title = doc.get('title', '')
        if title:
            weight = self.config.field_weights.get('title', 0.4)
            # 重复标题以增加权重
            repeat_count = max(1, int(weight * 10))
            parts.extend([title] * repeat_count)
        
        # 摘要
        abstract = doc.get('abstract', '')
        if abstract:
            weight = self.config.field_weights.get('abstract', 0.5)
            repeat_count = max(1, int(weight * 10))
            parts.extend([abstract] * repeat_count)
        
        # 关键词
        keywords = doc.get('keywords', '')
        if keywords:
            weight = self.config.field_weights.get('keywords', 0.1)
            repeat_count = max(1, int(weight * 10))
            parts.extend([keywords] * repeat_count)
        
        # 作者权威性加权
        if doc.get('citations', 0) > 100:  # 高引用论文
            parts.append(title)  # 额外加权
        
        return ' '.join(parts)
    
    def compute_colbert_score(self, query_vectors: np.ndarray, 
                             doc_vectors: np.ndarray) -> float:
        """计算ColBERT相似度分数"""
        if self.config.interaction == "maxsim":
            return self._maxsim_interaction(query_vectors, doc_vectors)
        else:
            return self._colbert_interaction(query_vectors, doc_vectors)
    
    def _maxsim_interaction(self, Q: np.ndarray, D: np.ndarray) -> float:
        """MaxSim交互：每个query token与最相似的doc token匹配"""
        # Q: [query_len, dim], D: [doc_len, dim]
        scores = np.dot(Q, D.T)  # [query_len, doc_len]
        max_scores = np.max(scores, axis=1)  # 每个query token的最大相似度
        return np.mean(max_scores)  # 平均所有query token的最大相似度
    
    def _colbert_interaction(self, Q: np.ndarray, D: np.ndarray) -> float:
        """ColBERT交互：改进的MaxSim"""
        # 计算所有token对的相似度
        scores = np.dot(Q, D.T)  # [query_len, doc_len]
        
        # 对每个query token，找到最相似的document token
        max_scores = np.max(scores, axis=1)
        
        # 可以添加位置权重、频率权重等
        # 这里使用简单的平均
        return np.mean(max_scores)
    
    def rerank(self, query: str, documents: List[Dict], 
               top_k: int = None) -> List[Tuple[int, float, Dict]]:
        """重排序文档
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个结果
            
        Returns:
            (原始索引, 分数, 文档)的列表，按分数降序排列
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        self.stats['total_docs'] += len(documents)
        
        try:
            # 编码查询
            query_vectors = self.encode_query(query)
            
            # 编码文档
            doc_vectors_list = self.encode_documents(documents)
            
            # 计算相似度分数
            scores = []
            for i, doc_vectors in enumerate(doc_vectors_list):
                score = self.compute_colbert_score(query_vectors, doc_vectors)
                
                # 学术优化：引用关系加权
                if self.config.academic_mode:
                    doc = documents[i]
                    if doc.get('citations', 0) > 50:
                        score *= self.config.citation_boost
                    
                    # 作者权威性加权（可以基于h-index等）
                    if doc.get('author_h_index', 0) > 20:
                        score *= self.config.author_boost
                
                scores.append((i, score, documents[i]))
            
            # 按分数排序
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # 返回top_k结果
            if top_k:
                scores = scores[:top_k]
            
            # 更新统计
            self.stats['total_time'] += time.time() - start_time
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in ColBERT reranking: {e}")
            # 返回原始顺序
            return [(i, 0.0, doc) for i, doc in enumerate(documents)]
    
    def batch_rerank(self, queries: List[str], documents_list: List[List[Dict]], 
                     top_k: int = None) -> List[List[Tuple[int, float, Dict]]]:
        """批量重排序"""
        results = []
        for query, documents in zip(queries, documents_list):
            result = self.rerank(query, documents, top_k)
            results.append(result)
        return results
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        stats = self.stats.copy()
        if stats['total_queries'] > 0:
            stats['avg_time_per_query'] = stats['total_time'] / stats['total_queries']
            stats['avg_docs_per_query'] = stats['total_docs'] / stats['total_queries']
        if stats['total_docs'] > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / (stats['total_queries'] + stats['total_docs'])
        return stats
    
    def clear_cache(self):
        """清理缓存"""
        if self.cache:
            self.cache.clear()
            logger.info("ColBERT cache cleared")

# 便捷函数
def create_colbert_reranker(academic_mode: bool = True, **kwargs) -> ColBERTReranker:
    """创建ColBERT重排序器"""
    config = ColBERTConfig(academic_mode=academic_mode, **kwargs)
    return ColBERTReranker(config)

def rerank_papers(query: str, papers: List[Dict], 
                  top_k: int = 10, **kwargs) -> List[Dict]:
    """快速重排序论文"""
    reranker = create_colbert_reranker(**kwargs)
    results = reranker.rerank(query, papers, top_k)
    return [doc for _, _, doc in results]
