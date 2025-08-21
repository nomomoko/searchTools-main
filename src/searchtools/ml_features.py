"""
机器学习特征工程模块
提供高级的特征提取和评分算法
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MLFeatures:
    """机器学习特征集合"""
    statistical_features: Dict[str, float]
    linguistic_features: Dict[str, float]
    positional_features: Dict[str, float]
    semantic_features: Dict[str, float]
    combined_score: float


class AdvancedFeatureExtractor:
    """高级特征提取器"""
    
    def __init__(self):
        self.feature_cache = {}
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # 学术领域关键词权重
        self.domain_keywords = {
            'high_impact': {
                'novel', 'breakthrough', 'significant', 'important', 'critical',
                'innovative', 'advanced', 'comprehensive', 'systematic', 'meta-analysis'
            },
            'methodology': {
                'method', 'approach', 'technique', 'algorithm', 'model', 'framework',
                'protocol', 'procedure', 'analysis', 'evaluation'
            },
            'results': {
                'results', 'findings', 'outcomes', 'evidence', 'data', 'statistics',
                'correlation', 'association', 'effect', 'impact'
            }
        }
    
    def extract_statistical_features(self, document: str, query: str) -> Dict[str, float]:
        """提取统计特征"""
        doc_words = re.findall(r'\b\w+\b', document.lower())
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        # 基础统计
        doc_length = len(doc_words)
        query_length = len(query_words)
        unique_doc_words = set(doc_words)
        unique_query_words = set(query_words)
        
        features = {
            # 长度特征
            'doc_length': doc_length,
            'query_length': query_length,
            'doc_length_log': np.log(doc_length + 1),
            
            # 词汇多样性
            'unique_words_ratio': len(unique_doc_words) / max(doc_length, 1),
            'vocabulary_richness': len(unique_doc_words) / max(np.sqrt(doc_length), 1),
            
            # 查询覆盖度
            'query_coverage': len(unique_query_words & unique_doc_words) / max(query_length, 1),
            'query_term_frequency': sum(doc_words.count(word) for word in query_words) / max(doc_length, 1),
            
            # 词长特征
            'avg_word_length': np.mean([len(word) for word in doc_words]) if doc_words else 0,
            'max_word_length': max([len(word) for word in doc_words]) if doc_words else 0,
            
            # 字符特征
            'capital_ratio': sum(1 for char in document if char.isupper()) / max(len(document), 1),
            'digit_ratio': sum(1 for char in document if char.isdigit()) / max(len(document), 1),
            'punctuation_ratio': sum(1 for char in document if not char.isalnum() and not char.isspace()) / max(len(document), 1)
        }
        
        return features
    
    def extract_linguistic_features(self, document: str, query: str) -> Dict[str, float]:
        """提取语言学特征"""
        doc_words = re.findall(r'\b\w+\b', document.lower())
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        # 去除停用词
        doc_content_words = [word for word in doc_words if word not in self.stopwords]
        query_content_words = [word for word in query_words if word not in self.stopwords]
        
        features = {
            # 内容词比例
            'content_word_ratio': len(doc_content_words) / max(len(doc_words), 1),
            
            # 停用词比例
            'stopword_ratio': (len(doc_words) - len(doc_content_words)) / max(len(doc_words), 1),
            
            # 重复词特征
            'word_repetition': len(doc_words) - len(set(doc_words)),
            'repetition_ratio': (len(doc_words) - len(set(doc_words))) / max(len(doc_words), 1),
            
            # 学术词汇特征
            'high_impact_words': sum(1 for word in doc_content_words if word in self.domain_keywords['high_impact']),
            'methodology_words': sum(1 for word in doc_content_words if word in self.domain_keywords['methodology']),
            'results_words': sum(1 for word in doc_content_words if word in self.domain_keywords['results']),
        }
        
        # 标准化学术词汇特征
        total_content_words = max(len(doc_content_words), 1)
        features['high_impact_ratio'] = features['high_impact_words'] / total_content_words
        features['methodology_ratio'] = features['methodology_words'] / total_content_words
        features['results_ratio'] = features['results_words'] / total_content_words
        
        return features
    
    def extract_positional_features(self, document: str, query: str) -> Dict[str, float]:
        """提取位置特征"""
        doc_lower = document.lower()
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        # 假设文档结构：标题(前100字符)，摘要(剩余部分)
        title_part = doc_lower[:100]
        abstract_part = doc_lower[100:] if len(doc_lower) > 100 else ""
        
        features = {
            'title_matches': 0,
            'abstract_matches': 0,
            'early_matches': 0,
            'late_matches': 0,
            'first_match_position': 1.0,
            'last_match_position': 0.0,
            'match_spread': 0.0,
            'match_density': 0.0
        }
        
        positions = []
        doc_length = len(doc_lower)
        
        for word in query_words:
            # 标题匹配
            if word in title_part:
                features['title_matches'] += 1
            
            # 摘要匹配
            if word in abstract_part:
                features['abstract_matches'] += 1
            
            # 位置分析
            pos = doc_lower.find(word)
            if pos != -1:
                relative_pos = pos / max(doc_length, 1)
                positions.append(relative_pos)
                
                # 早期匹配（前25%）
                if relative_pos <= 0.25:
                    features['early_matches'] += 1
                
                # 后期匹配（后25%）
                if relative_pos >= 0.75:
                    features['late_matches'] += 1
        
        # 位置统计
        if positions:
            features['first_match_position'] = min(positions)
            features['last_match_position'] = max(positions)
            features['match_spread'] = max(positions) - min(positions)
            features['match_density'] = len(positions) / max(len(query_words), 1)
        
        # 标准化
        query_length = max(len(query_words), 1)
        features['title_match_ratio'] = features['title_matches'] / query_length
        features['abstract_match_ratio'] = features['abstract_matches'] / query_length
        features['early_match_ratio'] = features['early_matches'] / query_length
        features['late_match_ratio'] = features['late_matches'] / query_length
        
        return features
    
    def extract_semantic_features(self, document: str, query: str) -> Dict[str, float]:
        """提取语义特征"""
        doc_words = set(re.findall(r'\b\w+\b', document.lower()))
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        # 简化的语义相似度计算
        features = {
            'exact_matches': len(query_words & doc_words),
            'partial_matches': 0,
            'semantic_similarity': 0.0,
            'concept_coverage': 0.0
        }
        
        # 部分匹配（词根相似）
        for q_word in query_words:
            for d_word in doc_words:
                if len(q_word) >= 4 and len(d_word) >= 4:
                    # 简单的词根匹配
                    if q_word[:4] == d_word[:4] or q_word[-4:] == d_word[-4:]:
                        features['partial_matches'] += 1
                        break
        
        # 语义相似度（基于共同词汇）
        if query_words:
            features['semantic_similarity'] = len(query_words & doc_words) / len(query_words)
        
        # 概念覆盖度
        total_concepts = len(query_words | doc_words)
        if total_concepts > 0:
            features['concept_coverage'] = len(query_words & doc_words) / total_concepts
        
        return features
    
    def extract_all_features(self, document: str, query: str) -> MLFeatures:
        """提取所有特征并计算综合评分"""
        cache_key = f"{hash(document[:100])}_{hash(query)}"
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        # 提取各类特征
        statistical = self.extract_statistical_features(document, query)
        linguistic = self.extract_linguistic_features(document, query)
        positional = self.extract_positional_features(document, query)
        semantic = self.extract_semantic_features(document, query)
        
        # 计算综合评分
        combined_score = self._calculate_combined_score(statistical, linguistic, positional, semantic)
        
        features = MLFeatures(
            statistical_features=statistical,
            linguistic_features=linguistic,
            positional_features=positional,
            semantic_features=semantic,
            combined_score=combined_score
        )
        
        # 缓存结果
        if len(self.feature_cache) < 1000:  # 限制缓存大小
            self.feature_cache[cache_key] = features
        
        return features
    
    def _calculate_combined_score(self, statistical: Dict[str, float], 
                                linguistic: Dict[str, float], 
                                positional: Dict[str, float], 
                                semantic: Dict[str, float]) -> float:
        """计算综合评分"""
        # 权重配置
        weights = {
            'query_coverage': 0.25,
            'title_match_ratio': 0.20,
            'semantic_similarity': 0.15,
            'early_match_ratio': 0.10,
            'high_impact_ratio': 0.10,
            'content_word_ratio': 0.08,
            'match_density': 0.07,
            'vocabulary_richness': 0.05
        }
        
        # 计算加权评分
        score = 0.0
        for feature, weight in weights.items():
            if feature in statistical:
                score += statistical[feature] * weight
            elif feature in linguistic:
                score += linguistic[feature] * weight
            elif feature in positional:
                score += positional[feature] * weight
            elif feature in semantic:
                score += semantic[feature] * weight
        
        return min(score, 1.0)  # 限制在0-1范围内


def get_ml_feature_extractor() -> AdvancedFeatureExtractor:
    """获取机器学习特征提取器实例（单例模式）"""
    if not hasattr(get_ml_feature_extractor, '_instance'):
        get_ml_feature_extractor._instance = AdvancedFeatureExtractor()
    return get_ml_feature_extractor._instance
