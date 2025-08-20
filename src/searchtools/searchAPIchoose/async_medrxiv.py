"""
异步版本的 MedRxiv API 封装类
"""

import json
from datetime import date, timedelta
from typing import List
from ..async_http_client import AsyncSearchHTTPClient


class AsyncMedRxivAPIWrapper:
    """
    MedRxiv API 异步封装类，用于获取指定日期范围和查询条件的论文。
    """

    def __init__(self, server="medrxiv"):
        self.server = server
        from ..search_config import get_api_config

        # MedRxiv 使用自己的配置
        config = get_api_config("medrxiv")
        self.max_results = config.max_results  # 保存配置的最大结果数
        self.http_client = AsyncSearchHTTPClient(
            timeout=config.timeout, max_retries=config.max_retries)

    async def fetch_medrxiv_papers(self, start_date: str,
                                   end_date: str) -> List[dict]:
        """
        异步获取指定日期范围内的所有论文（支持自动翻页）。

        Args:
            start_date: 开始日期，格式为 'YYYY-MM-DD'
            end_date: 结束日期，格式为 'YYYY-MM-DD'

        Returns:
            包含论文档案的列表
        """
        all_papers = []
        cursor = 0

        async with self.http_client:
            while True:
                url = f"https://api.biorxiv.org/details/{self.server}/{start_date}/{end_date}/{cursor}"
                print(f"Async getting data from: {url}")

                try:
                    response = await self.http_client.get(url)
                    data = response.json()
                    papers = data.get("collection", [])

                    if not papers:
                        break

                    all_papers.extend(papers)

                    # API返回的count字段为本次返回数量
                    count = data.get("count", 0)
                    if count < 100:
                        break

                    cursor += 100

                except Exception as e:
                    print(f"Async request error: {e}")
                    break
                except json.JSONDecodeError:
                    print("Failed to parse JSON response.")
                    break

        return all_papers

    def filter_papers_by_query(self, papers: List[dict],
                               query: str) -> List[dict]:
        """
        根据关键词过滤论文，标题或摘要包含query即保留。

        注：这个方法不需要异步，因为是纯计算操作
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

    async def run(self, query: str, days_back: int = 30) -> List[dict]:
        """
        运行 MedRxiv 检索，返回结构化数据。

        Args:
            query: 搜索关键词
            days_back: 搜索多少天前的论文（默认30天）

        Returns:
            List of dictionaries containing paper information
        """
        try:
            # 计算日期范围
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)

            # 获取论文
            papers = await self.fetch_medrxiv_papers(
                start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

            # 过滤论文
            if query:
                papers = self.filter_papers_by_query(papers, query)

            # 转换为统一格式
            results = []
            for paper in papers[:self.max_results]:  # 使用配置的最大结果数
                paper_data = {
                    "title":
                    paper.get("title", ""),
                    "authors":
                    paper.get("authors", ""),
                    "journal":
                    "MedRxiv Preprint",
                    "year":
                    paper.get("date", "").split("-")[0]
                    if paper.get("date") else "",
                    "citations":
                    0,  # MedRxiv 不提供引用数
                    "doi":
                    paper.get("doi", ""),
                    "pmid":
                    "",  # MedRxiv 没有 PMID
                    "pmcid":
                    "",  # MedRxiv 没有 PMCID
                    "published_date":
                    paper.get("date", ""),
                    "url":
                    f"https://www.medrxiv.org/content/{paper.get('doi', '')}",
                    "abstract":
                    paper.get("abstract", ""),
                }
                results.append(paper_data)

            return results

        except Exception as ex:
            print(f"Async MedRxiv exception: {ex}")
            return []

    def load(self, query: str) -> List[dict]:
        """
        同步包装器 - 为了兼容性保留
        内部调用异步版本
        """
        import asyncio

        return asyncio.run(self.run(query))
