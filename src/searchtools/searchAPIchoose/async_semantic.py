"""
异步版本的 Semantic Scholar API 封装
"""

from typing import List, Dict, Any, Optional
from ..async_http_client import AsyncSearchHTTPClient
from ..search_config import get_api_config


async def async_search_semantic_scholar(
    query: str,
    api_key: str,
    limit: int = 5,
    fields:
    str = "title,authors,year,abstract,url,venue,citationCount,externalIds,publicationDate",
) -> Optional[List[Dict[str, Any]]]:
    """
    异步搜索 Semantic Scholar。

    Args:
        query: 搜索查询字符串
        api_key: Semantic Scholar API key
        limit: 返回结果的最大数量
        fields: 要检索的字段，逗号分隔

    Returns:
        论文列表，每个论文是一个字典，如果出错则返回 None
    """

    base_url = "https://api.semanticscholar.org/graph/v1"
    endpoint = "/paper/search"
    url = f"{base_url}{endpoint}"

    # Set up the headers with your API key
    headers = {"x-api-key": api_key}

    # API request parameters
    params = {"query": query, "limit": limit, "fields": fields}

    print(f"Async sending request to Semantic Scholar API: {query}...")

    try:
        # Get config
        config = get_api_config("semantic_scholar")

        # Create async HTTP client with custom headers
        async_client = AsyncSearchHTTPClient(timeout=config.timeout,
                                             max_retries=config.max_retries,
                                             headers=headers)

        # Send async GET request
        async with async_client:
            response = await async_client.get(url, params=params)
            search_results = response.json()

            # Semantic Scholar API will return an empty "data" list when finding no results
            return search_results.get("data", [])

    except Exception as e:
        print(f"An error occurred during async request: {e}")
        return None


class AsyncSemanticScholarWrapper:
    """
    异步 Semantic Scholar API 封装类，提供统一接口。
    """

    def __init__(self, api_key: str, limit: int = 5):
        self.api_key = api_key
        self.limit = limit
        self.fields = "title,authors,year,abstract,url,venue,citationCount,externalIds,publicationDate"

    async def run(self, query: str) -> List[dict]:
        """
        运行 Semantic Scholar 搜索并返回统一格式的结构化数据。

        Returns:
            List of dictionaries containing paper information
        """
        try:
            # 搜索论文
            papers = await async_search_semantic_scholar(query=query,
                                                         api_key=self.api_key,
                                                         limit=self.limit,
                                                         fields=self.fields)

            if not papers:
                return []

            # 转换为统一格式
            results = []
            for paper in papers:
                # 安全获取所有值
                externalIds = paper.get("externalIds", {})
                doi = externalIds.get("DOI", "") if externalIds else ""
                pmid = externalIds.get("PubMed", "") if externalIds else ""

                # 构建URL
                if paper.get("url"):
                    url = paper["url"]
                elif doi:
                    url = f"https://doi.org/{doi}"
                elif pmid:
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                else:
                    url = ""

                # 处理作者列表
                authors = ", ".join([
                    author.get("name", "")
                    for author in paper.get("authors", [])
                    if author and author.get("name")
                ])

                # 构建结构化结果
                paper_data = {
                    "title": paper.get("title", ""),
                    "authors": authors,
                    "journal": paper.get("venue", ""),
                    "year": str(paper.get("year", "")),
                    "citations": paper.get("citationCount", 0),
                    "doi": doi,
                    "pmid": pmid,
                    "pmcid": "",  # Semantic Scholar 不提供 PMCID
                    "published_date": paper.get("publicationDate", ""),
                    "url": url,
                    "abstract": paper.get("abstract", ""),
                }
                results.append(paper_data)

            return results

        except Exception as ex:
            print(f"Async Semantic Scholar exception: {ex}")
            return []

    def load(self, query: str) -> List[dict]:
        """
        同步包装器 - 为了兼容性保留
        内部调用异步版本
        """
        import asyncio

        return asyncio.run(self.run(query))
