"""
智能重排序引擎 v2.0
提供多维度的搜索结果重排序功能，集成最前沿的信息检索和机器学习算法
"""

import re
import math
import logging
import time
from datetime import datetime, date
from typing import List, Set, Dict, Optional, Tuple, Any
from dataclasses import dataclass

from .models import SearchResult
from .advanced_algorithms import AdvancedRerankAlgorithm

logger = logging.getLogger(__name__)


@dataclass
class RerankConfig:
    """重排序配置 v2.0"""

    # 主要维度权重配置 (总和应为1.0)
    relevance_weight: float = 0.40  # 相关性权重
    authority_weight: float = 0.30  # 权威性权重
    recency_weight: float = 0.20    # 时效性权重
    quality_weight: float = 0.10    # 质量权重

    # 高级算法配置
    use_advanced_algorithms: bool = True  # 是否使用高级算法
    algorithm_mode: str = "hybrid"  # hybrid, traditional, ml_only

    # 高级算法权重
    advanced_algorithm_weights: Dict[str, float] = None

    # 传统相关性评分配置
    title_match_weight: float = 3.0
    abstract_match_weight: float = 1.5
    author_match_weight: float = 0.5
    phrase_match_bonus: float = 5.0
    synonym_match_weight: float = 0.8

    # 时效性配置
    recency_decay_days: int = 365  # 时效性衰减天数
    max_recency_bonus: float = 2.0  # 最大时效性奖励

    # 质量评分配置
    min_abstract_length: int = 50
    min_title_length: int = 10

    # 性能配置
    enable_caching: bool = True
    cache_size: int = 1000

    # 数据源权威性映射
    source_authority: Dict[str, float] = None

    def __post_init__(self):
        if self.source_authority is None:
            self.source_authority = {
                "PubMed": 1.0,
                "Europe PMC": 0.95,
                "Semantic Scholar": 0.9,
                "Clinical Trials": 0.85,
                "BioRxiv": 0.7,
                "MedRxiv": 0.7,
                "NIH Reporter": 0.8,
            }

        if self.advanced_algorithm_weights is None:
            self.advanced_algorithm_weights = {
                'bm25': 0.35,
                'tfidf': 0.25,
                'cosine': 0.20,
                'semantic': 0.15,
                'ml_features': 0.05
            }


class RerankEngine:
    """智能重排序引擎 v2.0 - 集成高级算法"""

    def __init__(self, config: Optional[RerankConfig] = None):
        self.config = config or RerankConfig()
        self._synonym_dict = self._build_synonym_dict()

        # 初始化高级算法
        if self.config.use_advanced_algorithms:
            self.advanced_algorithm = AdvancedRerankAlgorithm()
            self.advanced_algorithm.algorithm_weights = self.config.advanced_algorithm_weights
        else:
            self.advanced_algorithm = None

        # 缓存
        self._score_cache = {} if self.config.enable_caching else None
        self._performance_metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'avg_processing_time': 0.0,
            'algorithm_usage': {}
        }
        
    def _build_synonym_dict(self) -> Dict[str, Set[str]]:
        """构建同义词词典"""
        return {
            "cancer": {"tumor", "neoplasm", "malignancy", "carcinoma", "oncology"},
            "diabetes": {"diabetic", "hyperglycemia", "glucose", "insulin"},
            "covid": {"coronavirus", "sars-cov-2", "pandemic", "covid-19"},
            "vaccine": {"vaccination", "immunization", "immunize", "inoculation"},
            "treatment": {"therapy", "therapeutic", "intervention", "medication"},
            "disease": {"illness", "disorder", "condition", "pathology"},
            "study": {"research", "investigation", "analysis", "trial"},
            "patient": {"subject", "participant", "individual", "case"},
            "clinical": {"medical", "healthcare", "hospital", "therapeutic"},
            "drug": {"medication", "pharmaceutical", "medicine", "compound"},
        }
    
    def rerank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """
        对搜索结果进行重排序 v2.0

        Args:
            results: 搜索结果列表
            query: 搜索查询

        Returns:
            重排序后的结果列表
        """
        if not results or not query:
            return results

        start_time = time.time()
        self._performance_metrics['total_queries'] += 1

        logger.info(f"[RerankEngine v2.0] Starting rerank for {len(results)} results with query: '{query}'")
        logger.info(f"[RerankEngine] Algorithm mode: {self.config.algorithm_mode}")

        # 检查缓存
        cache_key = f"{hash(query)}_{len(results)}"
        if self._score_cache and cache_key in self._score_cache:
            self._performance_metrics['cache_hits'] += 1
            logger.info(f"[RerankEngine] Cache hit for query")
            return self._score_cache[cache_key]

        # 准备文档数据用于高级算法
        documents = []
        for result in results:
            doc_text = f"{result.title} {result.abstract}"
            documents.append(doc_text)

        # 预处理文档（如果使用高级算法）
        if self.advanced_algorithm and documents:
            self.advanced_algorithm.prepare_documents(documents)
            avg_doc_length = sum(len(doc.split()) for doc in documents) / len(documents)
        else:
            avg_doc_length = 0

        # 计算各维度评分
        scored_results = []
        query_keywords = self._extract_keywords(query)

        for i, result in enumerate(results):
            # 基础评分
            authority_score = self._calculate_authority_score(result)
            recency_score = self._calculate_recency_score(result)
            quality_score = self._calculate_quality_score(result)

            # 相关性评分（根据算法模式选择）
            if self.config.algorithm_mode == "traditional":
                relevance_score = self._calculate_relevance_score(result, query, query_keywords)
                advanced_scores = {}
            elif self.config.algorithm_mode == "ml_only" and self.advanced_algorithm:
                relevance_score = self._calculate_advanced_relevance_score(result, query, documents, avg_doc_length)
                advanced_scores = getattr(result, '_advanced_scores', {})
            else:  # hybrid mode
                traditional_score = self._calculate_relevance_score(result, query, query_keywords)
                if self.advanced_algorithm:
                    advanced_score = self._calculate_advanced_relevance_score(result, query, documents, avg_doc_length)
                    relevance_score = (traditional_score * 0.4 + advanced_score * 0.6)
                    advanced_scores = getattr(result, '_advanced_scores', {})
                else:
                    relevance_score = traditional_score
                    advanced_scores = {}

            # 计算最终评分
            final_score = (
                relevance_score * self.config.relevance_weight +
                authority_score * self.config.authority_weight +
                recency_score * self.config.recency_weight +
                quality_score * self.config.quality_weight
            )

            # 更新结果对象的评分字段
            result.relevance_score = relevance_score
            result.authority_score = authority_score
            result.recency_score = recency_score
            result.quality_score = quality_score
            result.final_score = final_score

            # 添加高级算法评分
            if advanced_scores:
                result.bm25_score = advanced_scores.get('bm25', 0.0)
                result.tfidf_score = advanced_scores.get('tfidf', 0.0)
                result.semantic_score = advanced_scores.get('semantic', 0.0)
                result.ml_score = advanced_scores.get('ml_features', 0.0)

            scored_results.append((result, final_score))

        # 按最终评分排序
        scored_results.sort(key=lambda x: x[1], reverse=True)
        reranked_results = [result for result, score in scored_results]

        # 更新性能指标
        processing_time = time.time() - start_time
        self._update_performance_metrics(processing_time)

        # 缓存结果
        if self._score_cache:
            if len(self._score_cache) >= self.config.cache_size:
                # 简单的LRU：删除最旧的条目
                oldest_key = next(iter(self._score_cache))
                del self._score_cache[oldest_key]
            self._score_cache[cache_key] = reranked_results

        # 记录前几个结果的评分
        if scored_results:
            top_scores = [round(score, 3) for _, score in scored_results[:5]]
            logger.info(f"[RerankEngine] Top 5 final scores: {top_scores}")

        logger.info(f"[RerankEngine] Rerank completed in {processing_time:.3f}s")
        return reranked_results
    
    def _extract_keywords(self, query: str) -> Set[str]:
        """提取查询关键词"""
        # 转换为小写并移除标点符号
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        words = clean_query.split()
        
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}
        
        return keywords

    def _calculate_advanced_relevance_score(self, result: SearchResult, query: str,
                                          all_documents: List[str], avg_doc_length: float) -> float:
        """使用高级算法计算相关性评分"""
        if not self.advanced_algorithm:
            return self._calculate_relevance_score(result, query, self._extract_keywords(query))

        document = f"{result.title or ''} {result.abstract or ''}"

        try:
            # 计算高级算法评分
            advanced_scores = self.advanced_algorithm.calculate_advanced_score(
                query, document, all_documents, avg_doc_length
            )

            # 存储详细评分供后续使用
            result._advanced_scores = advanced_scores

            # 更新算法使用统计
            for alg_name in advanced_scores:
                if alg_name != 'final':
                    self._performance_metrics['algorithm_usage'][alg_name] = \
                        self._performance_metrics['algorithm_usage'].get(alg_name, 0) + 1

            # 返回最终评分，标准化到0-10范围
            final_score = advanced_scores.get('final', 0.0)
            return min(max(final_score * 10, 0), 10)  # 标准化到0-10

        except Exception as e:
            logger.warning(f"[RerankEngine] Advanced algorithm failed: {e}, falling back to traditional")
            return self._calculate_relevance_score(result, query, self._extract_keywords(query))

    def _update_performance_metrics(self, processing_time: float):
        """更新性能指标"""
        total_queries = self._performance_metrics['total_queries']
        current_avg = self._performance_metrics['avg_processing_time']

        # 计算新的平均处理时间
        new_avg = ((current_avg * (total_queries - 1)) + processing_time) / total_queries
        self._performance_metrics['avg_processing_time'] = new_avg

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        metrics = self._performance_metrics.copy()
        if metrics['total_queries'] > 0:
            metrics['cache_hit_rate'] = metrics['cache_hits'] / metrics['total_queries']
        else:
            metrics['cache_hit_rate'] = 0.0

        return metrics

    def clear_cache(self):
        """清空缓存"""
        if self._score_cache:
            self._score_cache.clear()
            logger.info("[RerankEngine] Cache cleared")
    
    def _expand_keywords(self, keywords: Set[str]) -> Set[str]:
        """扩展关键词（添加同义词）"""
        expanded = keywords.copy()
        
        for keyword in keywords:
            if keyword in self._synonym_dict:
                expanded.update(self._synonym_dict[keyword])
        
        return expanded
    
    def _calculate_relevance_score(self, result: SearchResult, query: str, keywords: Set[str]) -> float:
        """计算相关性评分"""
        score = 0.0

        # 扩展关键词
        expanded_keywords = self._expand_keywords(keywords)

        # 安全获取字段值
        title = (result.title or "").lower()
        abstract = (result.abstract or "").lower()
        authors = (result.authors or "").lower()

        # 标题匹配
        title_words = set(re.sub(r'[^\w\s]', ' ', title).split())
        title_matches = len(expanded_keywords.intersection(title_words))
        score += title_matches * self.config.title_match_weight

        # 摘要匹配
        abstract_words = set(re.sub(r'[^\w\s]', ' ', abstract).split())
        abstract_matches = len(expanded_keywords.intersection(abstract_words))
        score += abstract_matches * self.config.abstract_match_weight

        # 作者匹配
        author_words = set(re.sub(r'[^\w\s]', ' ', authors).split())
        author_matches = len(expanded_keywords.intersection(author_words))
        score += author_matches * self.config.author_match_weight

        # 完整短语匹配奖励
        query_lower = query.lower()
        if query_lower in title:
            score += self.config.phrase_match_bonus
        elif query_lower in abstract:
            score += self.config.phrase_match_bonus * 0.5

        # 同义词匹配奖励
        synonym_matches = 0
        for keyword in keywords:
            if keyword in self._synonym_dict:
                for synonym in self._synonym_dict[keyword]:
                    if synonym in title_words or synonym in abstract_words:
                        synonym_matches += 1
        score += synonym_matches * self.config.synonym_match_weight

        # 标准化评分 (0-10)
        return min(score, 10.0)
    
    def _calculate_authority_score(self, result: SearchResult) -> float:
        """计算权威性评分"""
        score = 0.0
        
        # 数据源权威性
        source_score = self.config.source_authority.get(result.source, 0.5)
        score += source_score * 3.0
        
        # 引用数量 (对数缩放)
        if result.citations > 0:
            citation_score = math.log10(result.citations + 1) * 2.0
            score += min(citation_score, 5.0)
        
        # DOI/PMID可用性奖励
        if result.doi:
            score += 1.0
        if result.pmid:
            score += 1.0
        
        # 标准化评分 (0-10)
        return min(score, 10.0)
    
    def _calculate_recency_score(self, result: SearchResult) -> float:
        """计算时效性评分"""
        try:
            # 解析发表日期
            pub_date = self._parse_date(result.published_date or result.year)
            if not pub_date:
                return 5.0  # 默认中等评分
            
            # 计算天数差
            today = date.today()
            days_diff = (today - pub_date).days
            
            # 指数衰减函数
            if days_diff <= 0:
                return 10.0
            elif days_diff <= 30:
                return 9.0 + (30 - days_diff) / 30
            elif days_diff <= 365:
                return 5.0 + 4.0 * math.exp(-days_diff / self.config.recency_decay_days)
            else:
                return max(1.0, 5.0 * math.exp(-days_diff / (self.config.recency_decay_days * 2)))
                
        except Exception as e:
            logger.debug(f"[RerankEngine] Error calculating recency score: {e}")
            return 5.0
    
    def _calculate_quality_score(self, result: SearchResult) -> float:
        """计算质量评分"""
        score = 5.0  # 基础分

        # 安全获取字段值
        title = result.title or ""
        abstract = result.abstract or ""
        doi = result.doi or ""
        pmid = result.pmid or ""

        # 标题质量
        if len(title) >= self.config.min_title_length:
            score += 1.0
        if len(title) > 50:  # 适中长度奖励
            score += 1.0

        # 摘要质量
        if len(abstract) >= self.config.min_abstract_length:
            score += 2.0
        if len(abstract) > 200:  # 详细摘要奖励
            score += 1.0

        # 标识符完整性
        if doi:
            score += 0.5
        if pmid:
            score += 0.5

        # 标准化评分 (0-10)
        return min(score, 10.0)
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        if not date_str:
            return None
            
        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d", 
            "%Y",
            "%Y-%m",
            "%d/%m/%Y",
            "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(str(date_str).strip(), fmt)
                return parsed.date()
            except ValueError:
                continue
        
        # 尝试提取年份
        year_match = re.search(r'\b(19|20)\d{2}\b', str(date_str))
        if year_match:
            try:
                year = int(year_match.group())
                return date(year, 1, 1)
            except ValueError:
                pass
        
        return None


def get_rerank_engine(config: Optional[RerankConfig] = None) -> RerankEngine:
    """获取重排序引擎实例（单例模式）"""
    if not hasattr(get_rerank_engine, '_instance'):
        get_rerank_engine._instance = RerankEngine(config)
    return get_rerank_engine._instance
