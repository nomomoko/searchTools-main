"""
异步版本的 Europe PMC API 封装类
"""

from datetime import date
from typing import List, AsyncIterator, Optional
from ..async_http_client import AsyncSearchHTTPClient


class AsyncEuropePMCAPIWrapper:
    """
    Europe PMC API 异步封装类。

    支持关键词检索、近五年检索、分页、排序等功能。
    """

    base_url_search = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    page_size: int = 5
    email: str = "your.email@example.com"

    def __init__(self, page_size: int = 5, email: Optional[str] = None):
        from ..search_config import get_api_config

        config = get_api_config("europe_pmc")
        self.page_size = min(page_size, config.max_results)
        if email:
            self.email = email
        self.http_client = AsyncSearchHTTPClient(
            timeout=config.timeout, max_retries=config.max_retries)

    async def run(self, query: str) -> List[dict]:
        """
        运行 Europe PMC 检索，返回结构化数据。

        Returns:
            List of dictionaries containing paper information
        """
        try:
            results = []
            max_results = self.page_size  # 使用配置的页面大小作为最大结果数
            result_count = 0

            async for result in self.lazy_load(query):
                # 检查是否已达到最大结果数
                if result_count >= max_results:
                    break

                # 构建URL（复用原有逻辑）
                pmid = result.get("pmid", "")
                pmcid = result.get("pmcid", "")
                doi = result.get("doi", "")

                if pmid:
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                elif pmcid:
                    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
                elif doi:
                    url = f"https://doi.org/{doi}"
                else:
                    url = ""

                # 构建结构化结果（复用原有逻辑）
                paper_data = {
                    "title":
                    result.get("title", ""),
                    "authors":
                    result.get("authorString", ""),
                    "journal":
                    result.get("journalTitle", "") or result.get(
                        "journalInfo", {}).get("journal", {}).get("title", ""),
                    "year":
                    result.get("pubYear", ""),
                    "citations":
                    result.get("citedByCount", 0),
                    "doi":
                    doi,
                    "pmid":
                    pmid,
                    "pmcid":
                    pmcid,
                    "published_date":
                    result.get("firstPublicationDate", ""),
                    "url":
                    url,
                    "abstract":
                    result.get("abstractText", ""),
                }
                results.append(paper_data)
                result_count += 1

            return results
        except Exception as ex:
            # 返回空列表而不是错误字符串
            print(f"Async Europe PMC exception: {ex}")
            return []

    async def lazy_load(self, query: str) -> AsyncIterator[dict]:
        """
        异步检索 Europe PMC，默认返回近五年文献。
        """
        today = date.today()
        start_year = today.year - 5
        end_year = today.year

        # Europe PMC 支持用 PUB_YEAR:[YYYY TO YYYY] 过滤年份
        time_filter = f"PUB_YEAR:[{start_year} TO {end_year}]"
        full_query = f"{query} AND {time_filter}"

        params = {
            "query": full_query,
            "format": "json",
            "pageSize": self.page_size,
            "resultType": "core",
            "cursorMark": "*",
            "sort": "CITED desc",  # 按引用量倒序
            "email": self.email,
        }

        url = self.base_url_search

        async with self.http_client:
            response = await self.http_client.get(url, params=params)
            data = response.json()

            results = data.get("resultList", {}).get("result", [])
            for result in results:
                yield result

            # 处理分页
            while data.get("nextCursorMark"):
                params["cursorMark"] = data["nextCursorMark"]
                response = await self.http_client.get(url, params=params)
                data = response.json()

                results = data.get("resultList", {}).get("result", [])
                if not results:
                    break

                for result in results:
                    yield result

    def load(self, query: str) -> List[dict]:
        """
        同步包装器 - 为了兼容性保留
        内部调用异步版本
        """
        import asyncio

        return asyncio.run(self.run(query))
