#!/usr/bin/env python3
"""
学术论文特征提取器

专门针对学术文献设计的高级特征提取系统，包括：
- 引用网络分析
- 作者权威性评估
- 期刊影响因子
- 时间衰减因子
- 学科领域匹配
- 文本质量评估
- 多模态特征融合

这些特征将用于改进搜索排序和相关性评估。
"""

import re
import math
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

@dataclass
class AcademicFeatures:
    """学术论文特征数据类"""
    # 基础特征
    citation_count: int = 0
    publication_year: int = 0
    journal_impact_factor: float = 0.0
    h_index: float = 0.0
    
    # 文本特征
    title_length: int = 0
    abstract_length: int = 0
    keyword_count: int = 0
    reference_count: int = 0
    
    # 权威性特征
    author_reputation: float = 0.0
    venue_prestige: float = 0.0
    institutional_ranking: float = 0.0
    
    # 网络特征
    citation_velocity: float = 0.0  # 引用增长速度
    co_citation_strength: float = 0.0  # 共引强度
    bibliographic_coupling: float = 0.0  # 文献耦合
    
    # 时间特征
    recency_score: float = 0.0
    temporal_relevance: float = 0.0
    
    # 质量特征
    completeness_score: float = 0.0
    methodology_score: float = 0.0
    reproducibility_score: float = 0.0
    
    # 领域特征
    field_specificity: float = 0.0
    interdisciplinary_score: float = 0.0
    novelty_score: float = 0.0

class AcademicFeatureExtractor:
    """学术特征提取器"""
    
    def __init__(self):
        self.journal_impact_factors = self._load_journal_impact_factors()
        self.institution_rankings = self._load_institution_rankings()
        self.field_keywords = self._load_field_keywords()
        self.methodology_patterns = self._load_methodology_patterns()
        
    def _load_journal_impact_factors(self) -> Dict[str, float]:
        """加载期刊影响因子数据"""
        # 这里应该加载真实的JCR数据，现在使用示例数据
        return {
            "nature": 49.962,
            "science": 47.728,
            "cell": 41.582,
            "new england journal of medicine": 91.245,
            "lancet": 79.321,
            "plos one": 3.240,
            "scientific reports": 4.380,
            "proceedings of the national academy of sciences": 11.205,
            "journal of biological chemistry": 5.157,
            "bioinformatics": 6.931,
            # 可以扩展更多期刊
        }
    
    def _load_institution_rankings(self) -> Dict[str, float]:
        """加载机构排名数据"""
        # 基于QS、THE等排名的归一化分数
        return {
            "harvard university": 1.0,
            "stanford university": 0.98,
            "mit": 0.96,
            "cambridge university": 0.94,
            "oxford university": 0.92,
            "caltech": 0.90,
            "princeton university": 0.88,
            "yale university": 0.86,
            # 可以扩展更多机构
        }
    
    def _load_field_keywords(self) -> Dict[str, Set[str]]:
        """加载学科领域关键词"""
        return {
            "machine_learning": {
                "machine learning", "deep learning", "neural network", "artificial intelligence",
                "supervised learning", "unsupervised learning", "reinforcement learning",
                "convolutional neural network", "transformer", "bert", "gpt"
            },
            "bioinformatics": {
                "bioinformatics", "computational biology", "genomics", "proteomics",
                "sequence analysis", "phylogenetics", "systems biology", "biomarker"
            },
            "medicine": {
                "clinical trial", "diagnosis", "treatment", "therapy", "patient",
                "disease", "syndrome", "pathology", "epidemiology", "pharmacology"
            },
            "physics": {
                "quantum", "particle physics", "condensed matter", "astrophysics",
                "theoretical physics", "experimental physics", "cosmology"
            },
            "chemistry": {
                "organic chemistry", "inorganic chemistry", "physical chemistry",
                "analytical chemistry", "biochemistry", "catalysis", "synthesis"
            }
        }
    
    def _load_methodology_patterns(self) -> List[str]:
        """加载方法学模式"""
        return [
            r"randomized controlled trial",
            r"systematic review",
            r"meta-analysis",
            r"cohort study",
            r"case-control study",
            r"cross-sectional study",
            r"experimental design",
            r"statistical analysis",
            r"machine learning model",
            r"deep learning approach",
            r"computational method",
            r"algorithm",
            r"methodology",
            r"experimental protocol"
        ]
    
    def extract_features(self, paper: Dict) -> AcademicFeatures:
        """提取论文的所有学术特征"""
        features = AcademicFeatures()
        
        # 基础特征
        features.citation_count = paper.get('citations', 0)
        features.publication_year = self._extract_year(paper.get('year', paper.get('published_date', '')))
        features.journal_impact_factor = self._get_journal_impact_factor(paper.get('journal', ''))
        
        # 文本特征
        features.title_length = len(paper.get('title', ''))
        features.abstract_length = len(paper.get('abstract', ''))
        features.keyword_count = self._count_keywords(paper)
        features.reference_count = self._estimate_reference_count(paper)
        
        # 权威性特征
        features.author_reputation = self._calculate_author_reputation(paper.get('authors', ''))
        features.venue_prestige = self._calculate_venue_prestige(paper.get('journal', ''))
        features.institutional_ranking = self._calculate_institutional_ranking(paper.get('authors', ''))
        
        # 网络特征
        features.citation_velocity = self._calculate_citation_velocity(paper)
        features.co_citation_strength = self._calculate_co_citation_strength(paper)
        features.bibliographic_coupling = self._calculate_bibliographic_coupling(paper)
        
        # 时间特征
        features.recency_score = self._calculate_recency_score(features.publication_year)
        features.temporal_relevance = self._calculate_temporal_relevance(paper)
        
        # 质量特征
        features.completeness_score = self._calculate_completeness_score(paper)
        features.methodology_score = self._calculate_methodology_score(paper)
        features.reproducibility_score = self._calculate_reproducibility_score(paper)
        
        # 领域特征
        features.field_specificity = self._calculate_field_specificity(paper)
        features.interdisciplinary_score = self._calculate_interdisciplinary_score(paper)
        features.novelty_score = self._calculate_novelty_score(paper)
        
        return features
    
    def _extract_year(self, date_str: str) -> int:
        """提取发表年份"""
        if isinstance(date_str, int):
            return date_str
        
        if not date_str:
            return datetime.now().year
        
        # 尝试多种日期格式
        patterns = [
            r'(\d{4})',  # 简单的4位年份
            r'(\d{4})-\d{2}-\d{2}',  # YYYY-MM-DD
            r'(\d{4})/\d{2}/\d{2}',  # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(date_str))
            if match:
                return int(match.group(1))
        
        return datetime.now().year
    
    def _get_journal_impact_factor(self, journal: str) -> float:
        """获取期刊影响因子"""
        if not journal:
            return 0.0
        
        journal_lower = journal.lower().strip()
        
        # 精确匹配
        if journal_lower in self.journal_impact_factors:
            return self.journal_impact_factors[journal_lower]
        
        # 模糊匹配
        for known_journal, impact_factor in self.journal_impact_factors.items():
            if known_journal in journal_lower or journal_lower in known_journal:
                return impact_factor
        
        # 基于期刊类型的估算
        if any(keyword in journal_lower for keyword in ['nature', 'science', 'cell']):
            return 30.0  # 顶级期刊
        elif any(keyword in journal_lower for keyword in ['plos', 'bmc', 'frontiers']):
            return 3.0   # 开放获取期刊
        elif 'proceedings' in journal_lower:
            return 5.0   # 会议论文集
        else:
            return 2.0   # 默认值
    
    def _count_keywords(self, paper: Dict) -> int:
        """统计关键词数量"""
        keywords = paper.get('keywords', '')
        if not keywords:
            return 0
        
        # 简单分割统计
        return len([k.strip() for k in keywords.split(',') if k.strip()])
    
    def _estimate_reference_count(self, paper: Dict) -> int:
        """估算参考文献数量"""
        # 如果有直接的引用数据
        if 'references' in paper:
            return len(paper['references'])
        
        # 基于摘要长度估算
        abstract = paper.get('abstract', '')
        if abstract:
            # 经验公式：每100个单词大约对应1-2个引用
            word_count = len(abstract.split())
            return max(1, word_count // 50)
        
        return 10  # 默认估算值
    
    def _calculate_author_reputation(self, authors: str) -> float:
        """计算作者声誉分数"""
        if not authors:
            return 0.0
        
        # 简化的作者声誉计算
        # 实际应用中应该查询作者的h-index、发表记录等
        author_list = [a.strip() for a in authors.split(',')]
        
        # 基于作者数量的简单评分
        if len(author_list) == 1:
            return 0.6  # 单作者可能是资深研究者
        elif len(author_list) <= 5:
            return 0.8  # 小团队合作
        elif len(author_list) <= 10:
            return 1.0  # 中等规模合作
        else:
            return 0.7  # 大规模合作可能稀释个人贡献
    
    def _calculate_venue_prestige(self, journal: str) -> float:
        """计算发表场所声誉"""
        impact_factor = self._get_journal_impact_factor(journal)
        
        # 将影响因子转换为0-1的声誉分数
        if impact_factor >= 50:
            return 1.0
        elif impact_factor >= 20:
            return 0.9
        elif impact_factor >= 10:
            return 0.8
        elif impact_factor >= 5:
            return 0.7
        elif impact_factor >= 2:
            return 0.6
        else:
            return 0.5
    
    def _calculate_institutional_ranking(self, authors: str) -> float:
        """计算机构排名分数"""
        if not authors:
            return 0.0
        
        # 简化实现：在实际应用中需要解析作者机构信息
        # 这里基于作者字符串中的关键词进行简单匹配
        authors_lower = authors.lower()
        
        max_ranking = 0.0
        for institution, ranking in self.institution_rankings.items():
            if institution in authors_lower:
                max_ranking = max(max_ranking, ranking)
        
        return max_ranking
    
    def _calculate_citation_velocity(self, paper: Dict) -> float:
        """计算引用增长速度"""
        citations = paper.get('citations', 0)
        year = self._extract_year(paper.get('year', paper.get('published_date', '')))
        current_year = datetime.now().year
        
        years_since_publication = max(1, current_year - year)
        
        # 引用速度 = 引用数 / 发表年数
        velocity = citations / years_since_publication
        
        # 归一化到0-1范围
        return min(1.0, velocity / 100.0)  # 假设100引用/年是很高的速度
    
    def _calculate_co_citation_strength(self, paper: Dict) -> float:
        """计算共引强度"""
        # 简化实现：基于引用数和领域相关性
        citations = paper.get('citations', 0)
        
        # 高引用论文通常有更强的共引关系
        if citations > 1000:
            return 1.0
        elif citations > 100:
            return 0.8
        elif citations > 10:
            return 0.6
        else:
            return 0.3
    
    def _calculate_bibliographic_coupling(self, paper: Dict) -> float:
        """计算文献耦合强度"""
        # 简化实现：基于参考文献数量
        ref_count = self._estimate_reference_count(paper)
        
        # 归一化文献耦合强度
        return min(1.0, ref_count / 50.0)  # 假设50个引用是较高的耦合
    
    def _calculate_recency_score(self, year: int) -> float:
        """计算时效性分数"""
        current_year = datetime.now().year
        years_old = current_year - year
        
        # 指数衰减：越新的论文分数越高
        if years_old <= 0:
            return 1.0
        elif years_old <= 2:
            return 0.9
        elif years_old <= 5:
            return 0.7
        elif years_old <= 10:
            return 0.5
        else:
            return 0.3
    
    def _calculate_temporal_relevance(self, paper: Dict) -> float:
        """计算时间相关性"""
        # 结合发表时间和引用模式
        recency = self._calculate_recency_score(
            self._extract_year(paper.get('year', paper.get('published_date', '')))
        )
        citation_velocity = self._calculate_citation_velocity(paper)
        
        # 加权组合
        return 0.6 * recency + 0.4 * citation_velocity
    
    def _calculate_completeness_score(self, paper: Dict) -> float:
        """计算信息完整性分数"""
        score = 0.0
        total_fields = 8
        
        # 检查各个字段的完整性
        if paper.get('title'):
            score += 1
        if paper.get('abstract') and len(paper['abstract']) > 100:
            score += 1
        if paper.get('authors'):
            score += 1
        if paper.get('journal'):
            score += 1
        if paper.get('year') or paper.get('published_date'):
            score += 1
        if paper.get('doi'):
            score += 1
        if paper.get('keywords'):
            score += 1
        if paper.get('citations') is not None:
            score += 1
        
        return score / total_fields
    
    def _calculate_methodology_score(self, paper: Dict) -> float:
        """计算方法学分数"""
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        
        methodology_count = 0
        for pattern in self.methodology_patterns:
            if re.search(pattern, text):
                methodology_count += 1
        
        # 归一化分数
        return min(1.0, methodology_count / 5.0)  # 假设5个方法学关键词是很好的
    
    def _calculate_reproducibility_score(self, paper: Dict) -> float:
        """计算可重现性分数"""
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        
        reproducibility_keywords = [
            'code', 'data', 'github', 'repository', 'reproducible',
            'replication', 'open source', 'dataset', 'benchmark'
        ]
        
        score = 0.0
        for keyword in reproducibility_keywords:
            if keyword in text:
                score += 1
        
        return min(1.0, score / len(reproducibility_keywords))
    
    def _calculate_field_specificity(self, paper: Dict) -> float:
        """计算领域专一性"""
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        
        field_scores = {}
        for field, keywords in self.field_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                field_scores[field] = score
        
        if not field_scores:
            return 0.5  # 中性分数
        
        # 计算最强领域的专一性
        max_score = max(field_scores.values())
        total_score = sum(field_scores.values())
        
        return max_score / total_score if total_score > 0 else 0.5
    
    def _calculate_interdisciplinary_score(self, paper: Dict) -> float:
        """计算跨学科性分数"""
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        
        field_matches = 0
        for field, keywords in self.field_keywords.items():
            if any(keyword in text for keyword in keywords):
                field_matches += 1
        
        # 跨越的学科越多，跨学科性越强
        return min(1.0, field_matches / len(self.field_keywords))
    
    def _calculate_novelty_score(self, paper: Dict) -> float:
        """计算新颖性分数"""
        # 简化实现：基于时效性和方法学创新
        recency = self._calculate_recency_score(
            self._extract_year(paper.get('year', paper.get('published_date', '')))
        )
        methodology = self._calculate_methodology_score(paper)
        
        # 新论文 + 强方法学 = 高新颖性
        return 0.7 * recency + 0.3 * methodology

def extract_academic_features(paper: Dict) -> AcademicFeatures:
    """便捷函数：提取学术特征"""
    extractor = AcademicFeatureExtractor()
    return extractor.extract_features(paper)

def batch_extract_features(papers: List[Dict]) -> List[AcademicFeatures]:
    """批量提取学术特征"""
    extractor = AcademicFeatureExtractor()
    return [extractor.extract_features(paper) for paper in papers]
