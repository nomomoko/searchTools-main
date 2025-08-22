#!/usr/bin/env python3
"""
SearchTools FastAPI 应用
提供异步搜索和去重功能的 REST API
"""

import sys
import os
# 添加 src 路径到搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from typing import Any, Dict, List, Optional
from datetime import datetime
import time
import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from searchtools.async_parallel_search_manager import \
    AsyncParallelSearchManager
from searchtools.models import SearchResult

# 创建 FastAPI 应用
app = FastAPI(title="SearchTools API",
              description="异步搜索和去重工具 API",
              version="1.0.0")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class SearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 50
    enable_rerank: Optional[bool] = None  # None表示使用默认配置
    sort_by: Optional[str] = "relevance"  # relevance, recency, authority, citations


# 评分详情模型
class ScoreDetails(BaseModel):
    relevance: Optional[float] = None
    authority: Optional[float] = None
    recency: Optional[float] = None
    quality: Optional[float] = None
    final: Optional[float] = None
    # 新增高级评分
    bm25_score: Optional[float] = None
    tfidf_score: Optional[float] = None
    semantic_score: Optional[float] = None
    ml_score: Optional[float] = None

# 元数据模型
class ResultMetadata(BaseModel):
    source_rank: Optional[int] = None  # 在原始数据源中的排名
    rerank_position: Optional[int] = None  # 重排序后的位置
    confidence: Optional[float] = None  # 结果置信度
    relevance_factors: Optional[List[str]] = None  # 相关性因子
    quality_indicators: Optional[Dict[str, Any]] = None  # 质量指标

# 响应模型
class SearchResultResponse(BaseModel):
    # 基本信息
    title: str
    authors: str
    journal: str
    year: Optional[int]
    citations: Optional[int]
    doi: str
    pmid: str
    pmcid: str
    published_date: str
    url: str
    abstract: str
    source: str

    # 临床试验特有字段
    nct_id: Optional[str] = None
    status: Optional[str] = None
    conditions: Optional[str] = None
    interventions: Optional[str] = None

    # 评分信息
    scores: Optional[ScoreDetails] = None

    # 元数据
    metadata: Optional[ResultMetadata] = None


# 搜索统计信息
class SearchStats(BaseModel):
    total_sources: int
    successful_sources: int
    failed_sources: int
    total_raw_results: int
    after_deduplication: int
    after_rerank: int
    search_time_breakdown: Dict[str, float]

# 重排序信息
class RerankInfo(BaseModel):
    enabled: bool
    strategy: str
    algorithm: str = "advanced_ml"
    weights: Dict[str, float]
    performance_metrics: Dict[str, Any]

class SearchResponse(BaseModel):
    # 查询信息
    query: str
    timestamp: str

    # 结果信息
    total_results: int
    results: List[SearchResultResponse]

    # 统计信息
    stats: SearchStats

    # 去重信息
    deduplication: Dict[str, Any]

    # 重排序信息
    rerank: RerankInfo

    # 性能信息
    performance: Dict[str, float]


# 全局搜索管理器实例
search_manager = AsyncParallelSearchManager()


@app.get("/", response_class=HTMLResponse)
async def root():
    """根端点 - 提供搜索界面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SearchTools - 学术搜索工具</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .search-box {
                text-align: center;
                margin-bottom: 30px;
            }
            .search-input {
                width: 70%;
                padding: 15px;
                font-size: 18px;
                border: 2px solid #ddd;
                border-radius: 25px;
                outline: none;
                transition: border-color 0.3s;
            }
            .search-input:focus {
                border-color: #667eea;
            }
            .search-button {
                padding: 15px 30px;
                font-size: 18px;
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                margin-left: 10px;
                transition: transform 0.2s;
            }
            .search-button:hover {
                transform: translateY(-2px);
            }
            .results {
                margin-top: 30px;
            }
            .result-item {
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .result-title {
                font-size: 1.2em;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            .result-authors {
                color: #666;
                margin-bottom: 8px;
            }
            .result-journal {
                color: #888;
                font-style: italic;
                margin-bottom: 8px;
            }
            .result-abstract {
                color: #555;
                line-height: 1.6;
                margin-bottom: 10px;
            }
            .result-meta {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                font-size: 0.9em;
                color: #777;
            }
            .loading {
                text-align: center;
                color: #666;
                font-style: italic;
                margin: 20px 0;
            }
            .stats {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1> SearchTools 学术搜索工具</h1>
            
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" 
                       placeholder="输入搜索关键词，如：diabetes, cancer, machine learning..." 
                       value="breast cancer">
                <button onclick="performSearch()" class="search-button">搜索</button>
            </div>
            
            <div id="stats" class="stats" style="display: none;"></div>
            <div id="results" class="results"></div>
        </div>

        <script>
            async function performSearch() {
                const query = document.getElementById('searchInput').value.trim();
                if (!query) {
                    alert('请输入搜索关键词');
                    return;
                }
                
                // 显示加载状态
                document.getElementById('results').innerHTML = '<div class="loading">正在搜索中，请稍候...</div>';
                document.getElementById('stats').style.display = 'none';
                
                try {
                    console.log('开始搜索:', query);
                    const response = await fetch('/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            query: query,
                            max_results: 50
                        })
                    });

                    console.log('响应状态:', response.status);
                    if (!response.ok) {
                        throw new Error(`搜索请求失败: ${response.status} ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    console.error('搜索错误:', error);
                    document.getElementById('results').innerHTML =
                        `<div class="loading">搜索失败，请重试<br>错误详情: ${error.message}</div>`;
                }
            }
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                const statsDiv = document.getElementById('stats');
                
                // 显示统计信息
                statsDiv.innerHTML = `
                    <strong>搜索查询:</strong> ${data.query} |
                    <strong>结果数量:</strong> ${data.total_results} |
                    <strong>搜索时间:</strong> ${data.performance.total_time}秒 |
                    <strong>去重统计:</strong> 总重复: ${data.deduplication.total},
                    DOI重复: ${data.deduplication.by_doi},
                    标题重复: ${data.deduplication.by_title_author || 0}
                `;
                statsDiv.style.display = 'block';
                
                // 显示搜索结果
                if (data.results.length === 0) {
                    resultsDiv.innerHTML = '<div class="loading">未找到相关结果</div>';
                    return;
                }
                
                let resultsHTML = '';
                data.results.forEach(result => {
                    resultsHTML += `
                        <div class="result-item">
                            <div class="result-title">${result.title}</div>
                            <div class="result-authors">${result.authors}</div>
                            <div class="result-journal">${result.journal} (${result.year || 'N/A'})</div>
                            <div class="result-abstract">${result.abstract || '无摘要'}</div>
                            <div class="result-meta">
                                <span><strong>来源:</strong> ${result.source}</span>
                                <span><strong>DOI:</strong> ${result.doi || 'N/A'}</span>
                                <span><strong>PMID:</strong> ${result.pmid || 'N/A'}</span>
                                <span><strong>引用:</strong> ${result.citations || 0}</span>
                                <span><strong>发布日期:</strong> ${result.published_date || 'N/A'}</span>
                            </div>
                        </div>
                    `;
                });
                
                resultsDiv.innerHTML = resultsHTML;
            }
            
            // 页面加载完成后自动搜索默认关键词（暂时禁用）
            // window.onload = function() {
            //     performSearch();
            // };
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "SearchTools API is running"}


@app.get("/sources")
async def get_sources():
    """获取可用的搜索源"""
    sources = list(search_manager.async_sources.keys())
    return {"available_sources": sources, "total_sources": len(sources)}


@app.post("/search")
async def search_and_deduplicate(request: SearchRequest):
    """
    执行异步搜索和去重

    Args:
        request: 包含搜索查询和最大结果数的请求

    Returns:
        SearchResponse: 包含去重后结果的响应
    """
    try:
        import time

        start_time = time.time()

        # 执行异步搜索
        results = await search_manager._async_search_all_sources(request.query)

        # 收集所有结果
        all_results = []
        for source_name, source_result in results.items():
            if hasattr(source_result, "error") and source_result.error:
                continue

            # source_result.results 已经是 SearchResult 对象列表，不需要再转换
            for search_result in getattr(source_result, "results", []):
                all_results.append(search_result)

        # 执行去重
        deduplicated_results, duplicate_stats = search_manager.deduplicate_results(
            all_results)

        # 执行重排序（如果启用）
        rerank_enabled = False
        sort_strategy = "original"

        if request.enable_rerank is not False:  # None或True都启用rerank
            # 创建临时搜索管理器实例以支持自定义rerank设置
            temp_manager = search_manager
            if request.enable_rerank is not None:
                # 如果明确指定了rerank设置，创建新的管理器实例
                from searchtools.rerank_engine import RerankConfig
                temp_rerank_config = None

                # 根据sort_by调整权重
                if request.sort_by == "recency":
                    temp_rerank_config = RerankConfig(
                        relevance_weight=0.20, authority_weight=0.20,
                        recency_weight=0.50, quality_weight=0.10
                    )
                    sort_strategy = "recency"
                elif request.sort_by == "authority":
                    temp_rerank_config = RerankConfig(
                        relevance_weight=0.25, authority_weight=0.55,
                        recency_weight=0.10, quality_weight=0.10
                    )
                    sort_strategy = "authority"
                elif request.sort_by == "citations":
                    # 按引用数排序（简单排序，不使用rerank）
                    deduplicated_results.sort(key=lambda x: x.citations, reverse=True)
                    sort_strategy = "citations"
                else:  # relevance (default)
                    sort_strategy = "relevance"

                if temp_rerank_config and request.sort_by != "citations":
                    from searchtools.async_parallel_search_manager import AsyncParallelSearchManager
                    temp_manager = AsyncParallelSearchManager(enable_rerank=True, rerank_config=temp_rerank_config)

            # 执行重排序（除非是简单的引用数排序）
            if request.sort_by != "citations" and temp_manager.enable_rerank:
                deduplicated_results = temp_manager.rerank_results(deduplicated_results, request.query)
                rerank_enabled = True

        # 限制结果数量
        if request.max_results and len(
                deduplicated_results) > request.max_results:
            deduplicated_results = deduplicated_results[:request.max_results]

        # 转换为响应格式
        response_results = []
        for i, result in enumerate(deduplicated_results):
            # 构建评分详情（简化版本，避免None值问题）
            scores = {}
            if hasattr(result, 'relevance_score') and result.relevance_score is not None:
                scores['relevance'] = result.relevance_score
            if hasattr(result, 'authority_score') and result.authority_score is not None:
                scores['authority'] = result.authority_score
            if hasattr(result, 'recency_score') and result.recency_score is not None:
                scores['recency'] = result.recency_score
            if hasattr(result, 'quality_score') and result.quality_score is not None:
                scores['quality'] = result.quality_score
            if hasattr(result, 'final_score') and result.final_score is not None:
                scores['final'] = result.final_score

            # 构建元数据（简化版本）
            metadata = {
                "source_rank": i + 1,
                "rerank_position": i + 1
            }

            # 简化的结果对象
            response_results.append({
                "title": result.title,
                "authors": result.authors,
                "journal": result.journal,
                "year": result.year,
                "citations": result.citations,
                "doi": result.doi,
                "pmid": result.pmid,
                "pmcid": getattr(result, 'pmcid', None),
                "published_date": result.published_date,
                "url": result.url,
                "abstract": result.abstract,
                "source": result.source,
                "nct_id": getattr(result, 'nct_id', None),
                "status": getattr(result, 'status', None),
                "conditions": getattr(result, 'conditions', None),
                "interventions": getattr(result, 'interventions', None),
                "scores": scores,
                "metadata": metadata
            })

        search_time = time.time() - start_time

        # 简化的响应
        return {
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "total_results": len(response_results),
            "results": response_results,
            "stats": {
                "total_sources": 6,
                "successful_sources": len(all_results),
                "failed_sources": 0,
                "total_raw_results": len(all_results),
                "after_deduplication": len(deduplicated_results),
                "after_rerank": len(response_results),
                "search_time_breakdown": {}
            },
            "deduplication": {
                "total": len(all_results),
                "by_doi": duplicate_stats.get('by_doi', 0),
                "by_pmid": duplicate_stats.get('by_pmid', 0),
                "by_nctid": duplicate_stats.get('by_nctid', 0),
                "by_title_author": duplicate_stats.get('by_title_author', 0),
                "kept": len(deduplicated_results)
            },
            "rerank": {
                "enabled": rerank_enabled,
                "strategy": sort_strategy,
                "algorithm": "advanced_ml_v2" if rerank_enabled else "none",
                "weights": {},
                "performance_metrics": {}
            },
            "performance": {
                "total_time": round(search_time, 3),
                "results_per_second": round(len(response_results) / max(search_time, 0.001), 2)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索过程中发生错误: {str(e)}")


if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run("app:app",
                host="0.0.0.0",
                port=8000,
                reload=True,
                log_level="info")
