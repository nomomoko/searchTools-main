import httpx
from datetime import date
from typing import List, Iterator, Optional


class EuropePMCAPIWrapper:
    """
    Europe PMC API 封装类。

    支持关键词检索、近五年检索、分页、排序等功能。
    """

    base_url_search = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    page_size: int = 5
    email: str = "your.email@example.com"

    def __init__(self, page_size: int = 5, email: Optional[str] = None):
        self.page_size = page_size
        if email:
            self.email = email

    def run(self, query: str) -> str:
        """
        运行 Europe PMC 检索，返回格式化摘要。
        """
        try:
            # Retrieve the top-k results for the query
            docs = []
            for result in self.load(query):
                # 按优先级构建URL
                url = ""
                pmid = result.get("pmid", "")
                pmcid = result.get("pmcid", "")
                doi = result.get("doi", "")

                if pmid:
                    # 优先返回PubMed URL
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                #                elif pmid:
                # 其次返回Europe PMC镜像URL
                #                    url = f"https://europepmc.org/article/MED/{pmid}"
                elif pmcid:
                    # 再次返回NCBI PMC URL
                    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
                elif doi:
                    # 最后返回DOI URL
                    url = f"https://doi.org/{doi}"
                else:
                    # 都没有则返回提示
                    url = "have no url"

                doc = f"Title: {result.get('title', '')}\n"
                doc += f"Authors: {result.get('authorString', '')[:100]}\n"
                doc += f"Journal: {result.get('journalTitle', '') or result.get('journalInfo', {}).get('journal', {}).get('title', '')}\n"
                doc += f"Year: {result.get('pubYear', '')} | Citations: {result.get('citedByCount', 0)}\n"
                doc += (
                    f"DOI: {result.get('doi', '')} | PMID: {result.get('pmid', '')}\n"
                )
                doc += f"Published: {result.get('firstPublicationDate', '')}\n"
                doc += f"URL: {url}\n"
                doc += f"Abstract: {result.get('abstractText', '')}"

                docs.append(doc)
            return "\n\n".join(
                docs) if docs else "No good Europe PMC Result was found"
        except Exception as ex:
            return f"Europe PMC exception: {ex}"

    def lazy_load(self, query: str) -> Iterator[dict]:
        """
        检索 Europe PMC，默认返回近五年文献。
        """
        today = date.today()
        start_year = today.year - 5
        end_year = today.year

        # Europe PMC 支持用 PUB_YEAR:[YYYY TO YYYY] 过滤年份
        # 也可以用 FIRST_PDATE:[YYYY-MM-DD TO YYYY-MM-DD] 精确到日
        time_filter = f"PUB_YEAR:[{start_year} TO {end_year}]"
        full_query = f"{query} AND {time_filter}"

        params = {
            "query": full_query,
            "format": "json",
            "pageSize": self.page_size,
            "resultType": "core",
            "cursorMark": "*",
            "sort": "CITED desc",  # 按引用量倒序
            "email": "your.email@example.com",
        }

        url = self.base_url_search
        with httpx.Client() as client:
            response = client.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            for result in data.get("resultList", {}).get("result", []):
                yield result

    def load(self, query: str) -> List[dict]:
        """
        检索 Europe PMC，返回文献元数据列表。
        """
        return list(self.lazy_load(query))
