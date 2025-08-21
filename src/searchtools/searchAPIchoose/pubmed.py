"""
Migrated PubMed API wrapper using unified HTTP client.
This is a simplified version focusing on the main search functionality.
"""

import logging
import os
from typing import Iterator, List, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

from pydantic import BaseModel, Field
from ..http_client import SearchHTTPClient
from ..search_config import get_api_config

logger = logging.getLogger(__name__)


class PubMedAPIWrapper(BaseModel):
    """
    Wrapper around PubMed API using unified HTTP client.
    """

    # Base URLs
    base_url_esearch: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    base_url_efetch: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    # Configuration
    top_k_results: int = 5
    MAX_QUERY_LENGTH: int = 300
    doc_content_chars_max: int = 2000
    email: str = "searchtools@example.com"  # 更专业的邮箱地址

    # Non-serialized fields (excluded from model)
    http_client: Optional[SearchHTTPClient] = Field(default=None, exclude=True)
    rate_limit_delay: Optional[float] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Get configuration
        config = get_api_config("pubmed")
        self.top_k_results = config.max_results
        # Initialize HTTP client and rate limit
        self.http_client = SearchHTTPClient(timeout=config.timeout,
                                            max_retries=config.max_retries)
        self.rate_limit_delay = config.rate_limit_delay

    def run(self, query: str) -> List[dict]:
        """
        Run PubMed search and return structured data.

        Returns:
            List of dictionaries containing paper information
        """
        try:
            # Retrieve the top-k results for the query
            results = []
            for doc in self.lazy_load(query):
                # 构建 URL
                pmid = doc.get("pmid", "")
                pmcid = doc.get("pmcid", "")
                doi = doc.get("doi", "")

                if pmid:
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                elif pmcid:
                    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
                elif doi:
                    url = f"https://doi.org/{doi}"
                else:
                    url = ""

                # 构建结构化结果
                paper_data = {
                    "title": doc.get("title", ""),
                    "authors": doc.get("authors", ""),
                    "journal": doc.get("journal", ""),
                    "year": doc.get("year", ""),
                    "citations":
                    0,  # PubMed API doesn't provide citation count
                    "doi": doi,
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "published_date": doc.get("year",
                                              ""),  # Only year available
                    "url": url,
                    "abstract": doc.get("abstract", ""),
                }
                results.append(paper_data)

            return results

        except Exception as e:
            logger.error(f"Error in PubMed search: {e}")
            return []

    def lazy_load(self, query: str) -> Iterator[dict]:
        """
        Search PubMed for a given query and yield results.
        """
        query = query.strip()
        if not query:
            return

        if len(query) > self.MAX_QUERY_LENGTH:
            query = query[:self.MAX_QUERY_LENGTH]

        try:
            # Search PubMed for IDs
            article_ids = self._search_pubmed(query)

            # Fetch details for the IDs
            for article in self._fetch_details(article_ids):
                yield article

        except Exception as e:
            logger.error(f"Error in lazy_load: {e}")
            return

    def _search_pubmed_fallback(self, query: str) -> List[str]:
        """
        使用Europe PMC作为PubMed的稳定替代方案
        """
        try:
            logger.info(f"[PubMed Fallback] Using Europe PMC for: {query[:100]}...")

            # 使用Europe PMC的PubMed数据
            params = {
                "query": f"{query} AND SRC:MED",  # 限制为PubMed数据
                "format": "json",
                "pageSize": self.top_k_results,
                "resultType": "core",
                "cursorMark": "*",
                "sort": "CITED desc",
                "email": self.email,
            }

            response = self.http_client.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params=params
            )

            data = response.json()
            results = data.get("resultList", {}).get("result", [])

            # 提取PMID
            pmids = []
            for result in results:
                pmid = result.get("pmid")
                if pmid:
                    pmids.append(pmid)

            logger.info(f"[PubMed Fallback] Found {len(pmids)} PMIDs via Europe PMC")
            return pmids

        except Exception as e:
            logger.error(f"[PubMed Fallback] Europe PMC search failed: {e}")
            return []

    @retry(
        stop=stop_after_attempt(2),  # 减少重试次数
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=False,  # 不重新抛出异常，使用降级策略
    )
    def _search_pubmed(self, query: str) -> List[str]:
        """
        Search PubMed and return a list of article IDs.
        增强了错误处理和降级策略。
        """
        # 首先尝试直接PubMed搜索（如果有API密钥）
        api_key = os.getenv("NCBI_API_KEY") or os.getenv("PUBMED_API_KEY")

        if api_key:
            try:
                params = {
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": self.top_k_results,
                    "usehistory": "y",
                    "email": self.email,
                    "tool": "searchtools",
                    "api_key": api_key,
                }

                logger.info(f"[PubMed] Searching with API key: {query[:100]}...")
                response = self.http_client.get(self.base_url_esearch, params=params)

                if response.status_code == 200:
                    data = response.json()
                    if "esearchresult" in data:
                        id_list = data.get("esearchresult", {}).get("idlist", [])
                        logger.info(f"[PubMed] Found {len(id_list)} article IDs")

                        import time as _time
                        _time.sleep(max(0.5, float(self.rate_limit_delay or 0.5)))
                        return id_list

            except Exception as e:
                logger.warning(f"[PubMed] Direct API search failed: {e}")

        # 降级到Europe PMC
        logger.info("[PubMed] Using Europe PMC fallback strategy")
        return self._search_pubmed_fallback(query)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _fetch_details(self, article_ids: List[str]) -> Iterator[dict]:
        """
        Fetch details for a list of PubMed IDs.
        增强了错误处理和批处理逻辑。
        """
        if not article_ids:
            return

        # 分批处理以避免请求过大
        batch_size = min(10, len(article_ids))  # 限制批次大小
        for i in range(0, len(article_ids), batch_size):
            batch_ids = article_ids[i:i + batch_size]
            id_str = ",".join(batch_ids)

            params = {
                "db": "pubmed",
                "id": id_str,
                "retmode": "xml",
                "email": self.email,
                "tool": "searchtools",  # 添加工具标识符
            }

            try:
                logger.info(f"[PubMed] Fetching details for {len(batch_ids)} articles")
                response = self.http_client.get(self.base_url_efetch,
                                                params=params)

                # 检查响应状态
                if response.status_code == 429:
                    logger.warning("[PubMed] Rate limit exceeded during fetch")
                    import time as _time
                    _time.sleep(3.0)  # 更长的等待时间
                    raise Exception("Rate limit exceeded during fetch")

                xml_content = response.text

                # Parse XML content
                articles = self._parse_xml_content(xml_content)

                for article in articles:
                    if article:  # 确保文章数据有效
                        yield article

                # NCBI 友好：请求后短暂停顿
                import time as _time
                _time.sleep(max(0.5, float(self.rate_limit_delay or 0.5)))

            except Exception as e:
                logger.error(f"Error fetching PubMed details for batch: {e}")
                # 继续处理下一批，不中断整个流程
                continue

    def _parse_xml_content(self, xml_content: str) -> List[dict]:
        """
        Parse XML content from PubMed.
        This is a simplified parser - in production use proper XML parsing.
        """
        articles = []

        # Basic XML parsing (simplified)
        # In production, use xml.etree.ElementTree or lxml
        try:
            # Extract articles
            article_blocks = xml_content.split("<PubmedArticle>")[1:]

            for block in article_blocks:
                article = {}

                # Extract PMID
                if "<PMID" in block and "</PMID>" in block:
                    pmid_start = block.find(">", block.find("<PMID")) + 1
                    pmid_end = block.find("</PMID>")
                    article["pmid"] = block[pmid_start:pmid_end]

                # Extract title
                if "<ArticleTitle>" in block:
                    title_start = block.find("<ArticleTitle>") + len(
                        "<ArticleTitle>")
                    title_end = block.find("</ArticleTitle>")
                    article["title"] = block[title_start:title_end]

                # Extract abstract
                if "<AbstractText" in block:
                    abstract_start = block.find(
                        ">", block.find("<AbstractText")) + 1
                    abstract_end = block.find("</AbstractText>")
                    abstract = block[abstract_start:abstract_end]
                    if len(abstract) > self.doc_content_chars_max:
                        abstract = abstract[:self.
                                            doc_content_chars_max] + "..."
                    article["abstract"] = abstract

                # Extract authors (simplified)
                if "<Author " in block:
                    authors = []
                    author_blocks = block.split("<Author ")[1:]
                    for author_block in author_blocks[:
                                                      5]:  # Limit to 5 authors
                        if ("<LastName>" in author_block
                                and "<ForeName>" in author_block):
                            last_name_start = author_block.find(
                                "<LastName>") + len("<LastName>")
                            last_name_end = author_block.find("</LastName>")
                            first_name_start = author_block.find(
                                "<ForeName>") + len("<ForeName>")
                            first_name_end = author_block.find("</ForeName>")

                            last_name = author_block[
                                last_name_start:last_name_end]
                            first_name = author_block[
                                first_name_start:first_name_end]
                            authors.append(f"{last_name} {first_name}")

                    article["authors"] = ", ".join(authors)

                # Extract journal
                if "<Title>" in block:
                    journal_start = block.find("<Title>") + len("<Title>")
                    journal_end = block.find("</Title>", journal_start)
                    article["journal"] = block[journal_start:journal_end]

                # Extract year
                if "<Year>" in block:
                    year_start = block.find("<Year>") + len("<Year>")
                    year_end = block.find("</Year>")
                    article["year"] = block[year_start:year_end]

                articles.append(article)

        except Exception as e:
            logger.error(f"Error parsing XML: {e}")

        return articles
