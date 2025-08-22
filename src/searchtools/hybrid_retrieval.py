#!/usr/bin/env python3
"""
混合检索系统

整合多种先进的检索和排序技术：
1. Dense Retrieval: 基于SPECTER2/SciBERT的语义检索
2. Sparse Retrieval: 基于BM25/TF-IDF的关键词检索  
3. ColBERT Reranking: 多向量精确重排序
4. Academic Features: 学术特征加权
5. Ensemble Learning: 多模型融合

系统架构：
Query -> [Dense + Sparse] -> Candidate Retrieval -> ColBERT Rerank -> Academic Boost -> Final Ranking
"""

import logging
import time
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from .academic_embeddings import AcademicEmbeddingManager, EmbeddingConfig
from .colbert_reranker import ColBERTReranker, ColBERTConfig
from .academic_features import AcademicFeatureExtractor, AcademicFeatures
from .rerank_engine import RerankEngine, RerankConfig

logger = logging.getLogger(__name__)

@dataclass
class HybridConfig:
    """混合检索配置"""
    # 检索阶段权重
    dense_weight: float = 0.4      # 语义检索权重
    sparse_weight: float = 0.3     # 关键词检索权重
    colbert_weight: float = 0.2    # ColBERT重排序权重
    academic_weight: float = 0.1   # 学术特征权重
    
    # 检索参数
    candidate_size: int = 100      # 候选集大小
    rerank_size: int = 50          # 重排序大小
    final_size: int = 20           # 最终返回大小
    
    # 模型配置
    embedding_model: str = "specter2"  # specter2, scibert, bge-m3
    enable_colbert: bool = True
    enable_academic_features: bool = True
    
    # 性能配置
    enable_parallel: bool = True
    max_workers: int = 4
    enable_caching: bool = True
    
    # 学术优化
    citation_boost_threshold: int = 100  # 高引用论文阈值
    recency_boost_years: int = 3         # 近期论文加权年数
    venue_boost_factor: float = 1.2      # 顶级期刊加权因子

class HybridRetrievalSystem:
    """混合检索系统"""
    
    def __init__(self, config: HybridConfig):
        self.config = config
        
        # 初始化各个组件
        self.embedding_manager = None
        self.colbert_reranker = None
        self.feature_extractor = None
        self.traditional_reranker = None
        
        # 性能统计
        self.stats = {
            'total_queries': 0,
            'avg_retrieval_time': 0.0,
            'avg_rerank_time': 0.0,
            'cache_hit_rate': 0.0
        }
    
    def _initialize_components(self):
        """延迟初始化组件"""
        if self.embedding_manager is None:
            embedding_config = EmbeddingConfig(
                model_name=self.config.embedding_model,
                enable_caching=self.config.enable_caching
            )
            self.embedding_manager = AcademicEmbeddingManager(embedding_config)
            logger.info(f"Initialized embedding manager with {self.config.embedding_model}")
        
        if self.config.enable_colbert and self.colbert_reranker is None:
            colbert_config = ColBERTConfig(
                academic_mode=True,
                enable_caching=self.config.enable_caching
            )
            self.colbert_reranker = ColBERTReranker(colbert_config)
            logger.info("Initialized ColBERT reranker")
        
        if self.config.enable_academic_features and self.feature_extractor is None:
            self.feature_extractor = AcademicFeatureExtractor()
            logger.info("Initialized academic feature extractor")
        
        if self.traditional_reranker is None:
            rerank_config = RerankConfig(
                algorithm_mode="hybrid",
                enable_caching=self.config.enable_caching
            )
            self.traditional_reranker = RerankEngine(rerank_config)
            logger.info("Initialized traditional reranker")
    
    def retrieve_and_rank(self, query: str, documents: List[Dict], 
                         top_k: int = None) -> List[Tuple[int, float, Dict]]:
        """混合检索和排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个结果
            
        Returns:
            (原始索引, 综合分数, 文档)的列表，按分数降序排列
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        if top_k is None:
            top_k = self.config.final_size
        
        try:
            self._initialize_components()
            
            # 第一阶段：多路检索获取候选集
            candidates = self._multi_retrieval(query, documents)
            
            # 第二阶段：ColBERT精确重排序
            reranked = self._colbert_reranking(query, candidates)
            
            # 第三阶段：学术特征加权
            final_results = self._academic_boosting(query, reranked)
            
            # 第四阶段：最终融合排序
            final_scores = self._ensemble_ranking(query, final_results)
            
            # 返回top_k结果
            final_scores = final_scores[:top_k]
            
            # 更新统计
            retrieval_time = time.time() - start_time
            self.stats['avg_retrieval_time'] = (
                self.stats['avg_retrieval_time'] * (self.stats['total_queries'] - 1) + 
                retrieval_time
            ) / self.stats['total_queries']
            
            logger.info(f"Hybrid retrieval completed in {retrieval_time:.3f}s, returned {len(final_scores)} results")
            
            return final_scores
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            # 回退到简单排序
            return [(i, 0.0, doc) for i, doc in enumerate(documents[:top_k])]
    
    def _multi_retrieval(self, query: str, documents: List[Dict]) -> List[Tuple[int, float, Dict]]:
        """多路检索获取候选集"""
        logger.debug("Starting multi-retrieval phase")
        
        if self.config.enable_parallel:
            return self._parallel_retrieval(query, documents)
        else:
            return self._sequential_retrieval(query, documents)
    
    def _parallel_retrieval(self, query: str, documents: List[Dict]) -> List[Tuple[int, float, Dict]]:
        """并行多路检索"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {}
            
            # 提交各种检索任务
            if self.config.dense_weight > 0:
                futures['dense'] = executor.submit(self._dense_retrieval, query, documents)
            
            if self.config.sparse_weight > 0:
                futures['sparse'] = executor.submit(self._sparse_retrieval, query, documents)
            
            # 收集结果
            for name, future in futures.items():
                try:
                    results[name] = future.result(timeout=30)
                    logger.debug(f"{name} retrieval completed")
                except Exception as e:
                    logger.error(f"Error in {name} retrieval: {e}")
                    results[name] = []
        
        # 融合多路检索结果
        return self._fuse_retrieval_results(results, documents)
    
    def _sequential_retrieval(self, query: str, documents: List[Dict]) -> List[Tuple[int, float, Dict]]:
        """顺序多路检索"""
        results = {}
        
        if self.config.dense_weight > 0:
            results['dense'] = self._dense_retrieval(query, documents)
        
        if self.config.sparse_weight > 0:
            results['sparse'] = self._sparse_retrieval(query, documents)
        
        return self._fuse_retrieval_results(results, documents)
    
    def _dense_retrieval(self, query: str, documents: List[Dict]) -> List[Tuple[int, float]]:
        """语义检索（Dense Retrieval）"""
        try:
            # 编码查询
            query_papers = [{"title": query, "abstract": ""}]
            query_embedding = self.embedding_manager.encode_papers(query_papers)[0]
            
            # 编码文档
            doc_embeddings = self.embedding_manager.encode_papers(documents)
            
            # 计算相似度
            similarities = []
            for i, doc_emb in enumerate(doc_embeddings):
                sim = self.embedding_manager.compute_similarity(query_embedding, doc_emb)
                similarities.append((i, sim))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:self.config.candidate_size]
            
        except Exception as e:
            logger.error(f"Error in dense retrieval: {e}")
            return []
    
    def _sparse_retrieval(self, query: str, documents: List[Dict]) -> List[Tuple[int, float]]:
        """关键词检索（Sparse Retrieval）"""
        try:
            # 使用传统重排序引擎的BM25算法
            doc_results = []
            for i, doc in enumerate(documents):
                doc_copy = doc.copy()
                doc_copy['index'] = i
                doc_results.append(doc_copy)
            
            # 重排序
            reranked = self.traditional_reranker.rerank_results(doc_results, query)
            
            # 提取分数
            similarities = []
            for doc in reranked:
                if hasattr(doc, 'bm25_score') and doc.bm25_score is not None:
                    similarities.append((doc.index, doc.bm25_score))
                else:
                    similarities.append((doc.index, 0.0))
            
            return similarities[:self.config.candidate_size]
            
        except Exception as e:
            logger.error(f"Error in sparse retrieval: {e}")
            return []
    
    def _fuse_retrieval_results(self, results: Dict[str, List[Tuple[int, float]]], 
                               documents: List[Dict]) -> List[Tuple[int, float, Dict]]:
        """融合多路检索结果"""
        # 收集所有候选文档
        candidate_scores = {}
        
        # Dense检索结果
        if 'dense' in results:
            for doc_idx, score in results['dense']:
                if doc_idx not in candidate_scores:
                    candidate_scores[doc_idx] = {}
                candidate_scores[doc_idx]['dense'] = score
        
        # Sparse检索结果
        if 'sparse' in results:
            for doc_idx, score in results['sparse']:
                if doc_idx not in candidate_scores:
                    candidate_scores[doc_idx] = {}
                candidate_scores[doc_idx]['sparse'] = score
        
        # 计算融合分数
        fused_results = []
        for doc_idx, scores in candidate_scores.items():
            dense_score = scores.get('dense', 0.0)
            sparse_score = scores.get('sparse', 0.0)
            
            # 加权融合
            fused_score = (
                self.config.dense_weight * dense_score +
                self.config.sparse_weight * sparse_score
            )
            
            fused_results.append((doc_idx, fused_score, documents[doc_idx]))
        
        # 按融合分数排序
        fused_results.sort(key=lambda x: x[1], reverse=True)
        
        return fused_results[:self.config.candidate_size]
    
    def _colbert_reranking(self, query: str, candidates: List[Tuple[int, float, Dict]]) -> List[Tuple[int, float, Dict]]:
        """ColBERT重排序"""
        if not self.config.enable_colbert or not candidates:
            return candidates
        
        try:
            logger.debug("Starting ColBERT reranking phase")
            
            # 提取候选文档
            candidate_docs = [doc for _, _, doc in candidates]
            
            # ColBERT重排序
            reranked = self.colbert_reranker.rerank(
                query, 
                candidate_docs, 
                top_k=self.config.rerank_size
            )
            
            # 重新映射到原始索引
            reranked_results = []
            for new_idx, colbert_score, doc in reranked:
                # 找到原始索引
                original_idx = candidates[new_idx][0]
                original_score = candidates[new_idx][1]
                
                # 融合分数
                fused_score = (
                    (1 - self.config.colbert_weight) * original_score +
                    self.config.colbert_weight * colbert_score
                )
                
                reranked_results.append((original_idx, fused_score, doc))
            
            logger.debug(f"ColBERT reranking completed, processed {len(reranked_results)} candidates")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error in ColBERT reranking: {e}")
            return candidates
    
    def _academic_boosting(self, query: str, candidates: List[Tuple[int, float, Dict]]) -> List[Tuple[int, float, Dict]]:
        """学术特征加权"""
        if not self.config.enable_academic_features or not candidates:
            return candidates
        
        try:
            logger.debug("Starting academic feature boosting phase")
            
            boosted_results = []
            for original_idx, score, doc in candidates:
                # 提取学术特征
                features = self.feature_extractor.extract_features(doc)
                
                # 计算学术加权
                academic_boost = self._calculate_academic_boost(features, doc)
                
                # 融合分数
                boosted_score = (
                    (1 - self.config.academic_weight) * score +
                    self.config.academic_weight * academic_boost
                )
                
                boosted_results.append((original_idx, boosted_score, doc))
            
            # 按加权后分数排序
            boosted_results.sort(key=lambda x: x[1], reverse=True)
            
            logger.debug(f"Academic boosting completed, processed {len(boosted_results)} candidates")
            return boosted_results
            
        except Exception as e:
            logger.error(f"Error in academic boosting: {e}")
            return candidates
    
    def _calculate_academic_boost(self, features: AcademicFeatures, doc: Dict) -> float:
        """计算学术加权分数"""
        boost_score = 0.0
        
        # 引用数加权
        if features.citation_count >= self.config.citation_boost_threshold:
            boost_score += 0.3
        elif features.citation_count >= 50:
            boost_score += 0.2
        elif features.citation_count >= 10:
            boost_score += 0.1
        
        # 时效性加权
        current_year = 2024  # 可以动态获取
        if current_year - features.publication_year <= self.config.recency_boost_years:
            boost_score += 0.2
        
        # 期刊声誉加权
        if features.journal_impact_factor >= 20:
            boost_score += 0.3 * self.config.venue_boost_factor
        elif features.journal_impact_factor >= 10:
            boost_score += 0.2 * self.config.venue_boost_factor
        elif features.journal_impact_factor >= 5:
            boost_score += 0.1 * self.config.venue_boost_factor
        
        # 完整性加权
        boost_score += 0.2 * features.completeness_score
        
        # 方法学加权
        boost_score += 0.1 * features.methodology_score
        
        return min(1.0, boost_score)  # 限制在0-1范围
    
    def _ensemble_ranking(self, query: str, candidates: List[Tuple[int, float, Dict]]) -> List[Tuple[int, float, Dict]]:
        """最终融合排序"""
        # 当前实现直接返回，可以在这里添加更复杂的融合逻辑
        # 例如：学习排序(Learning to Rank)、多模型投票等
        return candidates
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        stats = self.stats.copy()
        
        # 添加各组件的统计
        if self.embedding_manager:
            stats['embedding_stats'] = self.embedding_manager.get_stats()
        
        if self.colbert_reranker:
            stats['colbert_stats'] = self.colbert_reranker.get_stats()
        
        return stats
    
    def clear_cache(self):
        """清理所有缓存"""
        if self.embedding_manager:
            self.embedding_manager.clear_cache()
        
        if self.colbert_reranker:
            self.colbert_reranker.clear_cache()
        
        if self.traditional_reranker:
            self.traditional_reranker.clear_cache()
        
        logger.info("All caches cleared")

# 便捷函数
def create_hybrid_system(embedding_model: str = "specter2", **kwargs) -> HybridRetrievalSystem:
    """创建混合检索系统"""
    config = HybridConfig(embedding_model=embedding_model, **kwargs)
    return HybridRetrievalSystem(config)

def hybrid_search(query: str, documents: List[Dict], top_k: int = 20, **kwargs) -> List[Dict]:
    """快速混合搜索"""
    system = create_hybrid_system(**kwargs)
    results = system.retrieve_and_rank(query, documents, top_k)
    return [doc for _, _, doc in results]
