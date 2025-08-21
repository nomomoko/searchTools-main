"""
高级重排序算法模块
实现最前沿的信息检索和机器学习算法
"""

import re
import math
import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentVector:
    """文档向量表示"""
    title_vector: np.ndarray
    abstract_vector: np.ndarray
    combined_vector: np.ndarray
    term_frequencies: Dict[str, int]
    document_length: int


class BM25Algorithm:
    """BM25算法实现 - 最经典的信息检索算法"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1  # 词频饱和参数
        self.b = b    # 长度归一化参数
        self.idf_cache = {}
        
    def calculate_idf(self, term: str, documents: List[str]) -> float:
        """计算逆文档频率"""
        if term in self.idf_cache:
            return self.idf_cache[term]
            
        doc_count = len(documents)
        term_doc_count = sum(1 for doc in documents if term in doc.lower())
        
        if term_doc_count == 0:
            idf = 0
        else:
            idf = math.log((doc_count - term_doc_count + 0.5) / (term_doc_count + 0.5))
        
        self.idf_cache[term] = idf
        return idf
    
    def calculate_bm25_score(self, query_terms: List[str], document: str, 
                           all_documents: List[str], avg_doc_length: float) -> float:
        """计算BM25评分"""
        doc_terms = document.lower().split()
        doc_length = len(doc_terms)
        term_frequencies = Counter(doc_terms)
        
        score = 0.0
        for term in query_terms:
            term = term.lower()
            tf = term_frequencies.get(term, 0)
            
            if tf > 0:
                idf = self.calculate_idf(term, all_documents)
                
                # BM25公式
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / avg_doc_length))
                
                score += idf * (numerator / denominator)
        
        return score


class TFIDFAlgorithm:
    """TF-IDF算法实现"""
    
    def __init__(self):
        self.idf_cache = {}
        self.vocabulary = set()
    
    def build_vocabulary(self, documents: List[str]):
        """构建词汇表"""
        for doc in documents:
            words = re.findall(r'\b\w+\b', doc.lower())
            self.vocabulary.update(words)
    
    def calculate_tf(self, term: str, document: str) -> float:
        """计算词频"""
        words = re.findall(r'\b\w+\b', document.lower())
        if not words:
            return 0.0
        return words.count(term.lower()) / len(words)
    
    def calculate_idf(self, term: str, documents: List[str]) -> float:
        """计算逆文档频率"""
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        doc_count = len(documents)
        term_doc_count = sum(1 for doc in documents if term.lower() in doc.lower())
        
        if term_doc_count == 0:
            idf = 0
        else:
            idf = math.log(doc_count / term_doc_count)
        
        self.idf_cache[term] = idf
        return idf
    
    def calculate_tfidf_score(self, query_terms: List[str], document: str, 
                             all_documents: List[str]) -> float:
        """计算TF-IDF评分"""
        score = 0.0
        for term in query_terms:
            tf = self.calculate_tf(term, document)
            idf = self.calculate_idf(term, all_documents)
            score += tf * idf
        
        return score


class CosineSimilarity:
    """余弦相似度算法"""
    
    def __init__(self):
        self.vocabulary = set()
        self.doc_vectors = {}
    
    def build_vocabulary(self, documents: List[str]):
        """构建词汇表"""
        if not hasattr(self, 'vocabulary') or not isinstance(self.vocabulary, set):
            self.vocabulary = set()
        for doc in documents:
            words = re.findall(r'\b\w+\b', doc.lower())
            self.vocabulary.update(words)
        self.vocabulary = sorted(list(self.vocabulary))
    
    def vectorize_document(self, document: str) -> np.ndarray:
        """将文档向量化"""
        words = re.findall(r'\b\w+\b', document.lower())
        word_counts = Counter(words)
        
        vector = np.zeros(len(self.vocabulary))
        for i, word in enumerate(self.vocabulary):
            vector[i] = word_counts.get(word, 0)
        
        return vector
    
    def calculate_cosine_similarity(self, query: str, document: str) -> float:
        """计算余弦相似度"""
        query_vector = self.vectorize_document(query)
        doc_vector = self.vectorize_document(document)
        
        # 计算余弦相似度
        dot_product = np.dot(query_vector, doc_vector)
        query_norm = np.linalg.norm(query_vector)
        doc_norm = np.linalg.norm(doc_vector)
        
        if query_norm == 0 or doc_norm == 0:
            return 0.0
        
        return dot_product / (query_norm * doc_norm)


class SemanticSimilarity:
    """语义相似度算法（简化版）"""
    
    def __init__(self):
        # 简化的语义词典
        self.semantic_groups = {
            'medical': {'disease', 'treatment', 'therapy', 'medicine', 'clinical', 'patient', 'diagnosis'},
            'research': {'study', 'analysis', 'investigation', 'research', 'experiment', 'trial'},
            'technology': {'algorithm', 'machine', 'learning', 'artificial', 'intelligence', 'model'},
            'biology': {'gene', 'protein', 'cell', 'molecular', 'biological', 'organism'},
            'covid': {'covid', 'coronavirus', 'sars-cov-2', 'pandemic', 'vaccine', 'vaccination'}
        }
        
        # 构建词到语义组的映射
        self.word_to_groups = {}
        for group, words in self.semantic_groups.items():
            for word in words:
                if word not in self.word_to_groups:
                    self.word_to_groups[word] = []
                self.word_to_groups[word].append(group)
    
    def get_semantic_similarity(self, word1: str, word2: str) -> float:
        """计算两个词的语义相似度"""
        word1, word2 = word1.lower(), word2.lower()
        
        if word1 == word2:
            return 1.0
        
        groups1 = self.word_to_groups.get(word1, [])
        groups2 = self.word_to_groups.get(word2, [])
        
        if not groups1 or not groups2:
            return 0.0
        
        # 计算共同语义组的比例
        common_groups = set(groups1) & set(groups2)
        total_groups = set(groups1) | set(groups2)
        
        if not total_groups:
            return 0.0
        
        return len(common_groups) / len(total_groups)
    
    def calculate_semantic_score(self, query_terms: List[str], document: str) -> float:
        """计算语义相似度评分"""
        doc_words = re.findall(r'\b\w+\b', document.lower())
        
        total_similarity = 0.0
        comparisons = 0
        
        for query_term in query_terms:
            for doc_word in doc_words:
                similarity = self.get_semantic_similarity(query_term, doc_word)
                total_similarity += similarity
                comparisons += 1
        
        if comparisons == 0:
            return 0.0
        
        return total_similarity / comparisons


class MLFeatureExtractor:
    """机器学习特征提取器"""
    
    def __init__(self):
        self.feature_cache = {}
    
    def extract_statistical_features(self, document: str, query: str) -> Dict[str, float]:
        """提取统计特征"""
        doc_words = re.findall(r'\b\w+\b', document.lower())
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        features = {
            'doc_length': len(doc_words),
            'query_length': len(query_words),
            'unique_words_ratio': len(set(doc_words)) / max(len(doc_words), 1),
            'query_coverage': len(set(query_words) & set(doc_words)) / max(len(query_words), 1),
            'avg_word_length': np.mean([len(word) for word in doc_words]) if doc_words else 0,
            'capital_ratio': sum(1 for char in document if char.isupper()) / max(len(document), 1),
            'punctuation_ratio': sum(1 for char in document if not char.isalnum() and not char.isspace()) / max(len(document), 1)
        }
        
        return features
    
    def extract_positional_features(self, document: str, query: str) -> Dict[str, float]:
        """提取位置特征"""
        doc_lower = document.lower()
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        features = {
            'first_match_position': 1.0,  # 默认值
            'last_match_position': 0.0,
            'match_density': 0.0,
            'title_matches': 0.0
        }
        
        # 假设前100个字符是标题
        title_part = doc_lower[:100]
        
        positions = []
        for word in query_words:
            pos = doc_lower.find(word)
            if pos != -1:
                positions.append(pos / len(doc_lower))
                if word in title_part:
                    features['title_matches'] += 1
        
        if positions:
            features['first_match_position'] = min(positions)
            features['last_match_position'] = max(positions)
            features['match_density'] = len(positions) / len(query_words)
        
        features['title_matches'] /= max(len(query_words), 1)
        
        return features
    
    def extract_all_features(self, document: str, query: str) -> Dict[str, float]:
        """提取所有特征"""
        cache_key = f"{hash(document)}_{hash(query)}"
        if cache_key in self.feature_cache:
            return self.feature_cache[cache_key]
        
        features = {}
        features.update(self.extract_statistical_features(document, query))
        features.update(self.extract_positional_features(document, query))
        
        self.feature_cache[cache_key] = features
        return features


class AdvancedRerankAlgorithm:
    """高级重排序算法集成"""
    
    def __init__(self):
        self.bm25 = BM25Algorithm()
        self.tfidf = TFIDFAlgorithm()
        self.cosine = CosineSimilarity()
        self.semantic = SemanticSimilarity()
        self.ml_extractor = MLFeatureExtractor()
        
        # 算法权重
        self.algorithm_weights = {
            'bm25': 0.35,
            'tfidf': 0.25,
            'cosine': 0.20,
            'semantic': 0.15,
            'ml_features': 0.05
        }
    
    def prepare_documents(self, documents: List[str]):
        """预处理文档"""
        self.tfidf.build_vocabulary(documents)
        self.cosine.build_vocabulary(documents)
    
    def calculate_advanced_score(self, query: str, document: str, 
                               all_documents: List[str], avg_doc_length: float) -> Dict[str, float]:
        """计算高级综合评分"""
        query_terms = re.findall(r'\b\w+\b', query.lower())
        
        scores = {}
        
        # BM25评分
        scores['bm25'] = self.bm25.calculate_bm25_score(
            query_terms, document, all_documents, avg_doc_length
        )
        
        # TF-IDF评分
        scores['tfidf'] = self.tfidf.calculate_tfidf_score(
            query_terms, document, all_documents
        )
        
        # 余弦相似度
        scores['cosine'] = self.cosine.calculate_cosine_similarity(query, document)
        
        # 语义相似度
        scores['semantic'] = self.semantic.calculate_semantic_score(query_terms, document)
        
        # 机器学习特征评分
        ml_features = self.ml_extractor.extract_all_features(document, query)
        scores['ml_features'] = np.mean(list(ml_features.values()))
        
        # 计算加权综合评分
        final_score = sum(
            scores[alg] * weight 
            for alg, weight in self.algorithm_weights.items()
        )
        
        scores['final'] = final_score
        return scores
