"""
异步版本的 PubMed API 封装类
"""

import logging
from typing import AsyncIterator, List, Optional
from tenacity import retry, stop_after_attempt, wait_fixed

from pydantic import BaseModel, Field
from ..async_http_client import AsyncSearchHTTPClient
from ..search_config import get_api_config

logger = logging.getLogger(__name__)


class AsyncPubMedAPIWrapper(BaseModel):
    """
    异步版本的 PubMed API 封装类。
    """

    # Base URLs
    base_url_esearch: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    base_url_efetch: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    # Configuration
    top_k_results: int = 5
    MAX_QUERY_LENGTH: int = 300
    doc_content_chars_max: int = 2000
    email: str = "your.email@example.com"

    # Non-serialized fields (excluded from model)
    http_client: Optional[AsyncSearchHTTPClient] = Field(default=None,
                                                         exclude=True)
    rate_limit_delay: Optional[float] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Get configuration
        config = get_api_config("pubmed")
        self.top_k_results = config.max_results
        # Initialize async HTTP client and rate limit
        self.http_client = AsyncSearchHTTPClient(
            timeout=config.timeout, max_retries=config.max_retries)
        self.rate_limit_delay = config.rate_limit_delay

    async def run(self, query: str) -> List[dict]:
        """
        异步运行 PubMed 搜索并返回结构化数据。

        Returns:
            List of dictionaries containing paper information
        """
        try:
            # Retrieve the top-k results for the query
            results = []
            async for doc in self.lazy_load(query):
                # 构建 URL（复用原有逻辑）
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

                # 构建结构化结果（复用原有逻辑）
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
            logger.error(f"Error in async PubMed search: {e}")
            return []

    async def lazy_load(self, query: str) -> AsyncIterator[dict]:
        """
        异步搜索 PubMed 并逐个返回结果。
        """
        query = query.strip()
        if not query:
            return

        if len(query) > self.MAX_QUERY_LENGTH:
            query = query[:self.MAX_QUERY_LENGTH]

        try:
            # Search PubMed for IDs
            article_ids = await self._search_pubmed(query)

            # Fetch details for the IDs
            async for article in self._fetch_details(article_ids):
                yield article

        except Exception as e:
            logger.error(f"Error in async lazy_load: {e}")
            return

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        reraise=True,
    )
    async def _search_pubmed(self, query: str) -> List[str]:
        """
        异步搜索 PubMed 并返回文章 ID 列表。
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": self.top_k_results,
            "usehistory": "y",
            "email": self.email,
        }

        try:
            async with self.http_client:
                response = await self.http_client.get(self.base_url_esearch,
                                                      params=params)
                data = response.json()

                # Extract IDs from the response
                id_list = data.get("esearchresult", {}).get("idlist", [])
                return id_list

        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        reraise=True,
    )
    async def _fetch_details(self,
                             article_ids: List[str]) -> AsyncIterator[dict]:
        """
        异步获取 PubMed ID 列表的详细信息。
        """
        if not article_ids:
            return

        # Convert IDs to comma-separated string
        id_str = ",".join(article_ids)

        params = {
            "db": "pubmed",
            "id": id_str,
            "retmode": "xml",
            "email": self.email
        }

        try:
            async with self.http_client:
                response = await self.http_client.get(self.base_url_efetch,
                                                      params=params)
                xml_content = response.text

                # Parse XML content
                articles = self._parse_xml_content(xml_content)

                for article in articles:
                    yield article

        except Exception as e:
            logger.error(f"Error fetching PubMed details: {e}")
            return

    def _parse_xml_content(self, xml_content: str) -> List[dict]:
        """
        Parse XML content from PubMed.
        This is a simplified parser - in production use proper XML parsing.

        注：这个方法不需要异步，因为是纯计算操作
        """
        articles = []

        # Basic XML parsing (simplified)
        # In production, use xml.etree.ElementTree or lxml
        try:
            # Extract articles using simple string parsing
            # This is a simplified version - real implementation would use XML parser
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_content)

            for article in root.findall(".//PubmedArticle"):
                article_data = {}

                # Extract PMID
                pmid_elem = article.find(".//PMID")
                if pmid_elem is not None:
                    article_data["pmid"] = pmid_elem.text

                # Extract title
                title_elem = article.find(".//ArticleTitle")
                if title_elem is not None:
                    article_data["title"] = title_elem.text or ""

                # Extract abstract
                abstract_elem = article.find(".//AbstractText")
                if abstract_elem is not None:
                    article_data["abstract"] = abstract_elem.text or ""

                # Extract authors
                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.find(".//LastName")
                    fore_name = author.find(".//ForeName")
                    if last_name is not None and fore_name is not None:
                        authors.append(f"{fore_name.text} {last_name.text}")
                article_data["authors"] = ", ".join(authors)

                # Extract journal
                journal_elem = article.find(".//Journal/Title")
                if journal_elem is not None:
                    article_data["journal"] = journal_elem.text or ""

                # Extract year
                year_elem = article.find(".//PubDate/Year")
                if year_elem is not None:
                    article_data["year"] = year_elem.text or ""

                # Extract DOI
                for id_elem in article.findall(".//ArticleId"):
                    if id_elem.get("IdType") == "doi":
                        article_data["doi"] = id_elem.text or ""
                    elif id_elem.get("IdType") == "pmc":
                        article_data["pmcid"] = id_elem.text or ""

                articles.append(article_data)

        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            # Fallback to basic parsing
            # Extract basic info using string operations if XML parsing fails

        return articles

    def load(self, query: str) -> List[dict]:
        """
        同步包装器 - 为了兼容性保留
        内部调用异步版本
        """
        import asyncio

        return asyncio.run(self.run(query))
