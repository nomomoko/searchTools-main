"""
预印本智能过滤器 - 为BioRxiv和MedRxiv提供高级过滤功能
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from collections import Counter
import math

logger = logging.getLogger(__name__)


class PreprintSmartFilter:
    """
    预印本智能过滤器，提供多种过滤和排序策略
    """
    
    def __init__(self):
        # 常见的停用词
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # 医学/生物学常见同义词
        self.synonyms = {
            'covid': ['covid-19', 'coronavirus', 'sars-cov-2', 'pandemic'],
            'cancer': ['tumor', 'tumour', 'carcinoma', 'malignancy', 'neoplasm', 'oncology'],
            'diabetes': ['diabetic', 'hyperglycemia', 'insulin resistance'],
            'heart': ['cardiac', 'cardiovascular', 'cardiology'],
            'brain': ['neural', 'neurological', 'cerebral', 'neuroscience'],
            'immune': ['immunity', 'immunology', 'immunological'],
            'gene': ['genetic', 'genomic', 'dna', 'rna'],
            'protein': ['proteomic', 'peptide', 'amino acid'],
            'cell': ['cellular', 'cytology'],
            'treatment': ['therapy', 'therapeutic', 'intervention'],
            'drug': ['medication', 'pharmaceutical', 'compound'],
            'study': ['research', 'investigation', 'analysis'],
            'patient': ['subject', 'participant', 'individual'],
            'disease': ['disorder', 'condition', 'illness', 'pathology']
        }
    
    def normalize_text(self, text: str) -> str:
        """
        标准化文本：转小写，移除特殊字符，保留字母数字和空格
        """
        if not text:
            return ""
        
        # 转小写
        text = text.lower()
        
        # 移除特殊字符，保留字母数字、空格和连字符
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # 合并多个空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词，移除停用词
        """
        normalized = self.normalize_text(query)
        words = normalized.split()
        
        # 移除停用词和短词
        keywords = [word for word in words 
                   if word not in self.stop_words and len(word) > 2]
        
        return keywords
    
    def expand_keywords(self, keywords: List[str]) -> Set[str]:
        """
        扩展关键词，包括同义词
        """
        expanded = set(keywords)
        
        for keyword in keywords:
            # 添加同义词
            for base_word, synonyms in self.synonyms.items():
                if keyword == base_word or keyword in synonyms:
                    expanded.update(synonyms)
                    expanded.add(base_word)
        
        return expanded
    
    def calculate_relevance_score(self, paper: Dict, query_keywords: Set[str]) -> float:
        """
        计算论文与查询的相关性得分
        """
        title = self.normalize_text(paper.get("title", ""))
        abstract = self.normalize_text(paper.get("abstract", ""))
        authors = self.normalize_text(paper.get("authors", ""))
        
        score = 0.0
        
        # 标题匹配（权重最高）
        title_words = set(title.split())
        title_matches = len(query_keywords.intersection(title_words))
        score += title_matches * 3.0
        
        # 摘要匹配（中等权重）
        abstract_words = set(abstract.split())
        abstract_matches = len(query_keywords.intersection(abstract_words))
        score += abstract_matches * 1.0
        
        # 作者匹配（较低权重）
        author_words = set(authors.split())
        author_matches = len(query_keywords.intersection(author_words))
        score += author_matches * 0.5
        
        # 完整短语匹配奖励
        original_query = " ".join(query_keywords)
        if original_query in title:
            score += 5.0
        elif original_query in abstract:
            score += 2.0
        
        # 标题长度惩罚（避免过长的标题）
        title_length_penalty = max(0, len(title.split()) - 20) * 0.1
        score -= title_length_penalty
        
        return score
    
    def filter_by_date_range(self, papers: List[Dict], days_back: int = 30) -> List[Dict]:
        """
        按日期范围过滤论文
        """
        from datetime import date, timedelta
        
        cutoff_date = date.today() - timedelta(days=days_back)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        filtered = []
        for paper in papers:
            paper_date = paper.get("date", "")
            if paper_date >= cutoff_str:
                filtered.append(paper)
        
        return filtered
    
    def filter_by_quality(self, papers: List[Dict]) -> List[Dict]:
        """
        按质量过滤论文（移除明显的低质量论文）
        """
        filtered = []
        
        for paper in papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            
            # 基本质量检查
            if len(title) < 10:  # 标题太短
                continue
            
            if len(abstract) < 50:  # 摘要太短
                continue
            
            # 检查是否包含明显的垃圾内容
            spam_indicators = ['test', 'example', 'placeholder', 'lorem ipsum']
            if any(indicator in title.lower() for indicator in spam_indicators):
                continue
            
            filtered.append(paper)
        
        return filtered
    
    def advanced_filter(self, papers: List[Dict], query: str, 
                       max_results: int = 20, days_back: int = 30,
                       min_score: float = 0.5) -> List[Dict]:
        """
        高级过滤：结合关键词匹配、相关性评分、日期和质量过滤
        """
        if not papers:
            return []
        
        logger.info(f"[PreprintFilter] Starting with {len(papers)} papers")
        
        # 1. 日期过滤
        papers = self.filter_by_date_range(papers, days_back)
        logger.info(f"[PreprintFilter] After date filter: {len(papers)} papers")
        
        # 2. 质量过滤
        papers = self.filter_by_quality(papers)
        logger.info(f"[PreprintFilter] After quality filter: {len(papers)} papers")
        
        if not query:
            return papers[:max_results]
        
        # 3. 关键词提取和扩展
        keywords = self.extract_keywords(query)
        expanded_keywords = self.expand_keywords(keywords)
        
        logger.info(f"[PreprintFilter] Query keywords: {keywords}")
        logger.info(f"[PreprintFilter] Expanded keywords: {list(expanded_keywords)[:10]}...")
        
        # 4. 计算相关性得分
        scored_papers = []
        for paper in papers:
            score = self.calculate_relevance_score(paper, expanded_keywords)
            if score >= min_score:
                scored_papers.append((paper, score))
        
        logger.info(f"[PreprintFilter] Papers with score >= {min_score}: {len(scored_papers)}")
        
        # 5. 按得分排序
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        
        # 6. 返回最佳结果
        result = [paper for paper, score in scored_papers[:max_results]]
        
        # 记录前几个结果的得分
        if scored_papers:
            logger.info(f"[PreprintFilter] Top scores: {[round(score, 2) for _, score in scored_papers[:5]]}")
        
        return result
    
    def simple_filter(self, papers: List[Dict], query: str) -> List[Dict]:
        """
        简单过滤：保持向后兼容性
        """
        if not query:
            return papers
        
        query_lower = query.lower()
        filtered = []
        
        for paper in papers:
            title = paper.get("title", "").lower()
            abstract = paper.get("abstract", "").lower()
            
            if query_lower in title or query_lower in abstract:
                filtered.append(paper)
        
        return filtered


# 全局过滤器实例
_filter_instance = None

def get_preprint_filter() -> PreprintSmartFilter:
    """
    获取全局过滤器实例（单例模式）
    """
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = PreprintSmartFilter()
    return _filter_instance
