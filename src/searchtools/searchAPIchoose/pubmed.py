"""
Migrated PubMed API wrapper using unified HTTP client.
This is a simplified version focusing on the main search functionality.
"""

import logging
from typing import Iterator, List, Optional
from tenacity import retry, stop_after_attempt, wait_fixed

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _search_pubmed(self, query: str) -> List[str]:
        """
        Search PubMed and return a list of article IDs.
        增强了错误处理和速率限制。
        """
        # 添加工具标识符以符合NCBI政策
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": self.top_k_results,
            "usehistory": "y",
            "email": self.email,
            "tool": "searchtools",  # 添加工具标识符
            "api_key": "",  # 预留API密钥字段
        }

        try:
            logger.info(f"[PubMed] Searching for: {query[:100]}...")
            response = self.http_client.get(self.base_url_esearch,
                                            params=params)

            # 检查响应状态
            if response.status_code == 429:
                logger.warning("[PubMed] Rate limit exceeded, waiting longer...")
                import time as _time
                _time.sleep(2.0)  # 更长的等待时间
                raise Exception("Rate limit exceeded")

            data = response.json()

            # 检查API错误
            if "esearchresult" not in data:
                logger.error(f"[PubMed] Unexpected response format: {data}")
                return []

            # Extract IDs from the response
            id_list = data.get("esearchresult", {}).get("idlist", [])
            logger.info(f"[PubMed] Found {len(id_list)} article IDs")

            # NCBI 友好：轻微等待，降低 429/403 风险
            import time as _time
            _time.sleep(max(0.5, float(self.rate_limit_delay or 0.5)))
            return id_list

        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            # 不立即返回空列表，让重试机制处理
            raise

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
            logger.error(f"Error fetching PubMed details: {e}")
            return

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
