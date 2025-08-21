#!/usr/bin/env python3
"""
SearchTools FastAPI 应用
提供异步搜索和去重功能的 REST API
"""

from typing import Any, Dict, List, Optional

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


# 响应模型
class SearchResultResponse(BaseModel):
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


class SearchResponse(BaseModel):
    query: str
    total_results: int
    duplicate_stats: Dict[str, Any]
    results: List[SearchResultResponse]
    search_time: float


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
                    
                    if (!response.ok) {
                        throw new Error('搜索请求失败');
                    }
                    
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    console.error('搜索错误:', error);
                    document.getElementById('results').innerHTML = 
                        '<div class="loading">搜索失败，请重试</div>';
                }
            }
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                const statsDiv = document.getElementById('stats');
                
                // 显示统计信息
                statsDiv.innerHTML = `
                    <strong>搜索查询:</strong> ${data.query} | 
                    <strong>结果数量:</strong> ${data.total_results} | 
                    <strong>搜索时间:</strong> ${data.search_time}秒 | 
                    <strong>去重统计:</strong> 总重复: ${data.duplicate_stats.total}, 
                    DOI重复: ${data.duplicate_stats.by_doi}, 
                    标题重复: ${data.duplicate_stats.by_title}
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
            
            // 页面加载完成后自动搜索默认关键词
            window.onload = function() {
                performSearch();
            };
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


@app.post("/search", response_model=SearchResponse)
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

        # 限制结果数量
        if request.max_results and len(
                deduplicated_results) > request.max_results:
            deduplicated_results = deduplicated_results[:request.max_results]

        # 转换为响应格式
        response_results = []
        for result in deduplicated_results:
            response_results.append(
                SearchResultResponse(
                    title=result.title,
                    authors=result.authors,
                    journal=result.journal,
                    year=result.year,
                    citations=result.citations,
                    doi=result.doi,
                    pmid=result.pmid,
                    pmcid=result.pmid,
                    published_date=result.published_date,
                    url=result.url,
                    abstract=result.abstract,
                    source=result.source,
                ))

        search_time = time.time() - start_time

        return SearchResponse(
            query=request.query,
            total_results=len(response_results),
            duplicate_stats=duplicate_stats,
            results=response_results,
            search_time=round(search_time, 2),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索过程中发生错误: {str(e)}")


if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run("app:app",
                host="0.0.0.0",
                port=8000,
                reload=True,
                log_level="info")
