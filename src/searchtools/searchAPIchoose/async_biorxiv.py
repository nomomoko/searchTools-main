"""
异步版本的 BioRxiv API 封装类
"""

import json
from datetime import date, timedelta
from typing import List, Optional
from ..async_http_client import AsyncSearchHTTPClient


class AsyncBioRxivAPIWrapper:
    """
    BioRxiv API 异步封装类，用于获取指定日期范围和查询条件的论文。
    """

    def __init__(self, server="biorxiv"):
        self.server = server
        from ..search_config import get_api_config

        config = get_api_config("biorxiv")
        self.max_results = config.max_results  # 保存配置的最大结果数
        self.http_client = AsyncSearchHTTPClient(
            timeout=config.timeout, max_retries=config.max_retries)

    async def fetch_papers(self, start_date: str,
                           end_date: str) -> Optional[List[dict]]:
        """
        异步获取指定日期范围内的论文。

        Args:
            start_date: 开始日期，格式为 'YYYY-MM-DD'
            end_date: 结束日期，格式为 'YYYY-MM-DD'

        Returns:
            论文列表，如果请求失败则返回 None
        """
        url = f"https://api.biorxiv.org/details/{self.server}/{start_date}/{end_date}/0"
        print(f"Async fetching {url}")

        try:
            async with self.http_client:
                response = await self.http_client.get(url)
                data = response.json()
                return data.get("collection", [])
        except Exception as e:
            print(f"Async error: {e}")
            return None
        except json.JSONDecodeError:
            print("Error: Parsing JSON response failed.")
            return None

    async def fetch_biorxiv_papers(self,
                                   start_date: str,
                                   end_date: str,
                                   server: str = "biorxiv") -> List[dict]:
        """
        异步获取指定日期范围内的所有论文（支持自动翻页）。

        Args:
            start_date: 开始日期，格式为 'YYYY-MM-DD'
            end_date: 结束日期，格式为 'YYYY-MM-DD'
            server: 服务器，使用 'biorxiv' 或 'medrxiv'

        Returns:
            包含论文档案的列表
        """
        all_papers = []
        cursor = 0

        async with self.http_client:
            while True:
                url = f"https://api.biorxiv.org/details/{server}/{start_date}/{end_date}/{cursor}"
                print(f"Async getting data from: {url}")

                try:
                    response = await self.http_client.get(url)
                    data = response.json()
                    papers = data.get("collection", [])

                    if not papers:
                        break

                    all_papers.extend(papers)

                    # API返回的count字段为本次返回数量，total为总数
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
                               query: str, use_advanced_filter: bool = True) -> List[dict]:
        """
        根据关键词过滤论文，支持简单和高级过滤模式。

        Args:
            papers: 论文列表
            query: 搜索查询
            use_advanced_filter: 是否使用高级过滤（默认True）

        Returns:
            过滤后的论文列表
        """
        if not query:
            return papers

        if use_advanced_filter:
            # 使用智能过滤器
            from ..preprint_filter import get_preprint_filter
            from ..search_config import get_api_config

            config = get_api_config("biorxiv")
            filter_instance = get_preprint_filter()
            return filter_instance.advanced_filter(
                papers, query,
                max_results=self.max_results,
                days_back=getattr(config, 'filter_days_back', 30),
                min_score=getattr(config, 'min_relevance_score', 0.5)
            )
        else:
            # 使用简单过滤器（向后兼容）
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
        运行 BioRxiv 检索，返回结构化数据。

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
            papers = await self.fetch_biorxiv_papers(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                self.server,
            )

            # 过滤论文（根据配置决定是否使用高级过滤器）
            from ..search_config import get_api_config
            config = get_api_config("biorxiv")
            use_advanced = getattr(config, 'use_advanced_filter', True)

            if query:
                papers = self.filter_papers_by_query(papers, query, use_advanced_filter=use_advanced)
            else:
                # 即使没有查询，也应用质量过滤
                from ..preprint_filter import get_preprint_filter
                filter_instance = get_preprint_filter()
                papers = filter_instance.filter_by_quality(papers)

            # 转换为统一格式
            results = []
            for paper in papers[:self.max_results]:  # 使用配置的最大结果数
                paper_data = {
                    "title":
                    paper.get("title", ""),
                    "authors":
                    paper.get("authors", ""),
                    "journal":
                    f"{self.server.upper()} Preprint",
                    "year":
                    paper.get("date", "").split("-")[0]
                    if paper.get("date") else "",
                    "citations":
                    0,  # BioRxiv 不提供引用数
                    "doi":
                    paper.get("doi", ""),
                    "pmid":
                    "",  # BioRxiv 没有 PMID
                    "pmcid":
                    "",  # BioRxiv 没有 PMCID
                    "published_date":
                    paper.get("date", ""),
                    "url":
                    f"https://www.biorxiv.org/content/{paper.get('doi', '')}",
                    "abstract":
                    paper.get("abstract", ""),
                }
                results.append(paper_data)

            return results

        except Exception as ex:
            print(f"Async BioRxiv exception: {ex}")
            return []
