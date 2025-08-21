"""
数据模型定义
定义搜索结果和搜索源结果的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class SearchResult:
    """单个搜索结果"""

    title: str = ""
    authors: str = ""
    journal: str = ""
    year: str = ""
    citations: int = 0
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    published_date: str = ""
    url: str = ""
    abstract: str = ""
    source: str = ""

    # 临床试验特有字段
    nct_id: str = ""
    status: str = ""
    conditions: str = ""
    interventions: str = ""

    # Rerank相关字段
    relevance_score: float = 0.0
    authority_score: float = 0.0
    recency_score: float = 0.0
    quality_score: float = 0.0
    final_score: float = 0.0

    def __post_init__(self):
        """后初始化处理"""
        if not self.published_date and self.year:
            self.published_date = self.year


@dataclass
class SourceSearchResult:
    """单个搜索源的结果"""

    source: str
    query: str
    results: List[SearchResult] = field(default_factory=list)
    results_count: int = 0
    search_time: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """后初始化处理"""
        if self.results_count == 0 and self.results:
            self.results_count = len(self.results)


@dataclass
class QuerySearchRecord:
    """查询搜索记录"""

    query: str
    timestamp: datetime
    source_results: Dict[str, SourceSearchResult]
    total_results: int = 0
    successful_sources: int = 0
    search_time: float = 0.0

    def __post_init__(self):
        """后初始化处理"""
        if self.total_results == 0:
            self.total_results = sum(
                len(result.results) for result in self.source_results.values())

        if self.successful_sources == 0:
            self.successful_sources = len([
                result for result in self.source_results.values()
                if not result.error
            ])
