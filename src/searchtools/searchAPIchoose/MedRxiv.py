import json
from ..http_client import SearchHTTPClient


# 此py用于修改MedRxiv搜索的参数。
class MedRxivAPIWrapper:
    """
    MedRxiv API Wrapper for fetching papers within a specified date range and query.
    """

    def __init__(self, server="medrxiv"):
        self.server = server
        from ..search_config import get_api_config

        config = get_api_config("medrxiv")
        self.max_results = config.max_results  # 保存配置的最大结果数
        self.http_client = SearchHTTPClient(timeout=config.timeout,
                                            max_retries=config.max_retries)

    def fetch_medrxiv_papers(self, start_date, end_date):
        """
        Fetch papers from MedRxiv API within the specified date range, with auto paging.
        """
        all_papers = []
        cursor = 0
        while True:
            url = f"https://api.biorxiv.org/details/{self.server}/{start_date}/{end_date}/{cursor}"
            print(f"Getting data from: {url}")
            try:
                response = self.http_client.get(url)
                data = response.json()
                papers = data.get("collection", [])
                if not papers:
                    break
                all_papers.extend(papers)
                count = data.get("count", 0)
                if count < 100:
                    break
                cursor += 100
            except Exception as e:
                print(f"Request error: {e}")
                break
            except json.JSONDecodeError:
                print("Failed to parse JSON response.")
                break
        return all_papers

    def filter_papers_by_query(self, papers, query):
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
