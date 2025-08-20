import json
from ..http_client import SearchHTTPClient

# 此py用于修改BioRxiv搜索的参数。


class BioRxivAPIWrapper:
    """
    BioRxiv API Wrapper for fetching papers within a specified date range and query.
    """

    def __init__(self, server="biorxiv"):
        self.server = server
        from ..search_config import get_api_config

        config = get_api_config("biorxiv")
        self.max_results = config.max_results  # 保存配置的最大结果数
        self.http_client = SearchHTTPClient(timeout=config.timeout,
                                            max_retries=config.max_retries)

    def fetch_papers(self, start_date, end_date):
        """
        Fetch papers from BioRxiv or MedRxiv API within the specified date range.

        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format.

        Returns:
            list: List of paper records, or None if the request fails.
        """
        url = f"https://api.biorxiv.org/details/{self.server}/{start_date}/{end_date}/0"
        print(f"Fetching {url}")

        try:
            response = self.http_client.get(url)
            data = response.json()
            return data.get("collection", [])
        except Exception as e:
            print(f"Error: {e}")
            return None
        except json.JSONDecodeError:
            print("Error: Parsing JSON response failed.")
            return None

    def fetch_biorxiv_papers(self, start_date, end_date, server="biorxiv"):
        """
        从bioRxiv或medRxiv的API获取指定主题，指定日期范围内的论文。

        Args:
            按照指定日期范围获取论文档案。默认设置获得十天内的论文。
            日期范围可以在主函数中修改。
            start_date (str): 开始日期，格式为 'YYYY-MM-DD'.
            end_date (str): 结束日期，格式为 'YYYY-MM-DD'.
            server (str): 服务器，使用'biorxiv' .

        Returns:
            list: 包含论文档案的列表，如果请求失败则返回None.
        """
        # 支持自动翻页，获取所有论文
        # API每页最多返回100条，需用cursor翻页
        all_papers = []
        cursor = 0
        while True:
            url = f"https://api.biorxiv.org/details/{server}/{start_date}/{end_date}/{cursor}"
            print(f"Getting data from: {url}")
            try:
                response = self.http_client.get(url)
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
                print(f"Request error: {e}")
                break
            except json.JSONDecodeError:
                print("Failed to parse JSON response.")
                break
        return all_papers

    def filter_papers_by_query(self, papers, query):
        """
        根据关键词过滤论文，标题或摘要包含query即保留。
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
