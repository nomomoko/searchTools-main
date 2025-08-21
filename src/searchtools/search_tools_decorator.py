"""
Decorator-based search tools for medical and biomedical literature searches.
Uses @tool decorator from langchain_core for cleaner implementation and better LangGraph compatibility.
"""

from datetime import date, timedelta
from langchain_core.tools import tool
import sys
import os
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .searchAPIchoose.europe_pmc import EuropePMCAPIWrapper
from .searchAPIchoose.BioRxiv import BioRxivAPIWrapper
from .searchAPIchoose.MedRxiv import MedRxivAPIWrapper
from .searchAPIchoose.clinical_trials import ClinicalTrialsAPIWrapper
from .searchAPIchoose.semantic import search_semantic_scholar
from .searchAPIchoose.pubmed import PubMedAPIWrapper


def format_paper_results(papers: List[Dict[str, Any]],
                         max_results: int = 5) -> str:
    """
    统一格式化搜索结果。

    Args:
        papers: List of paper dictionaries
        max_results: Maximum number of results to format

    Returns:
        Formatted string of search results
    """
    if not papers:
        return "No papers found matching the query."

    results = []
    for i, paper in enumerate(papers[:max_results]):
        # 获取各字段，提供默认值
        title = paper.get("title", "N/A")
        authors = paper.get("authors", "N/A")
        journal = paper.get("journal", "N/A")
        year = paper.get("year", "N/A")
        citations = paper.get("citations", 0)
        doi = paper.get("doi", "")
        pmid = paper.get("pmid", "")
        pmcid = paper.get("pmcid", "")
        published_date = paper.get("published_date", year)  # 如果没有具体日期，使用年份
        url = paper.get("url", "")
        abstract = paper.get("abstract", "N/A")

        # 构建格式化字符串
        result_str = (f"Title: {title}\n"
                      f"Authors: {authors}\n"
                      f"Journal: {journal}\n"
                      f"Year: {year} | Citations: {citations}\n")

        # 添加标识符
        if doi:
            result_str += f"DOI: {doi} "
        if pmid:
            result_str += f"| PMID: {pmid} "
        if pmcid:
            result_str += f"| PMCID: {pmcid}"
        if doi or pmid or pmcid:
            result_str += "\n"

        # 添加其他信息
        if published_date and published_date != year:
            result_str += f"Published: {published_date}\n"
        if url:
            result_str += f"URL: {url}\n"
        result_str += f"Abstract: {abstract}"

        results.append(result_str)

    return "\n\n".join(results)


@tool
def europe_pmc_pubmed_search(query: str) -> str:
    """
    Search PubMed via Europe PMC API.
    Useful for medical, health, and biomedical topics from biomedical literature.
    Supports sorting by citation count.

    Args:
        query: Search query string

    Returns:
        Formatted search results from PubMed/Europe PMC
    """
    wrapper = EuropePMCAPIWrapper()
    papers = wrapper.run(query)
    return format_paper_results(papers)


@tool
def biorxiv_search(query: str, days_back: int = 365) -> str:
    """
    Search BioRxiv preprints.
    Useful for recent preprints in biology and life sciences.

    Args:
        query: Search query string
        days_back: Number of days to look back (default: 365)

    Returns:
        Formatted search results from BioRxiv
    """
    wrapper = BioRxivAPIWrapper()

    # Calculate date range
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Fetch and filter papers
    papers = wrapper.fetch_biorxiv_papers(start_date_str, end_date_str)
    filtered = wrapper.filter_papers_by_query(papers, query)

    if not filtered:
        return "No papers found matching the query or there was an error fetching data."

    # 转换为统一格式（限制结果数量）
    formatted_papers = []
    max_results = wrapper.max_results if hasattr(wrapper,
                                                 "max_results") else 10
    for paper in filtered[:max_results]:
        doi = paper.get("doi", "")
        url = f"https://doi.org/{doi}" if doi else ""

        formatted_paper = {
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "journal": paper.get("journal", "bioRxiv"),  # 默认为 bioRxiv
            "year": paper.get("year", ""),
            "citations":
            paper.get("cited_by", 0) if "cited_by" in paper else 0,
            "doi": doi,
            "pmid": "",  # BioRxiv papers don't have PMID
            "pmcid": "",
            "published_date": paper.get("date", ""),
            "url": url,
            "abstract": paper.get("abstract", ""),
        }
        formatted_papers.append(formatted_paper)

    return format_paper_results(formatted_papers)


@tool
def medrxiv_search(query: str, days_back: int = 365) -> str:
    """
    Search MedRxiv preprints.
    Useful for recent preprints in medicine and health sciences.

    Args:
        query: Search query string
        days_back: Number of days to look back (default: 365)

    Returns:
        Formatted search results from MedRxiv
    """
    wrapper = MedRxivAPIWrapper()

    # Calculate date range
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days_back)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Fetch and filter papers
    papers = wrapper.fetch_medrxiv_papers(start_date_str, end_date_str)
    filtered = wrapper.filter_papers_by_query(papers, query)

    if not filtered:
        return "No papers found matching the query or there was an error fetching data."

    # 转换为统一格式（限制结果数量）
    formatted_papers = []
    max_results = wrapper.max_results if hasattr(wrapper,
                                                 "max_results") else 10
    for paper in filtered[:max_results]:
        doi = paper.get("doi", "")
        url = f"https://doi.org/{doi}" if doi else ""

        formatted_paper = {
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "journal": paper.get("journal", "medRxiv"),  # 默认为 medRxiv
            "year": paper.get("year", ""),
            "citations":
            paper.get("cited_by", 0) if "cited_by" in paper else 0,
            "doi": doi,
            "pmid": "",  # MedRxiv papers don't have PMID
            "pmcid": "",
            "published_date": paper.get("date", ""),
            "url": url,
            "abstract": paper.get("abstract", ""),
        }
        formatted_papers.append(formatted_paper)

    return format_paper_results(formatted_papers)


@tool
def clinical_trials_search(query: str,
                           status: str = None,
                           max_studies: int = 15) -> str:
    """
    Search ClinicalTrials.gov with enhanced stability.
    Useful for finding clinical trials, interventions, and study eligibility.

    Args:
        query: Search query string
        status: Trial status filter (default: None, searches all statuses)
        max_studies: Maximum number of studies to return (default: 15)

    Returns:
        Formatted search results from ClinicalTrials.gov
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        wrapper = ClinicalTrialsAPIWrapper()

        # Use configured max_results if max_studies not specified
        if max_studies == 15:  # default value
            max_studies = wrapper.max_results if hasattr(wrapper,
                                                         "max_results") else 10

        # 限制最大搜索数量以提高稳定性
        max_studies = min(max_studies, 20)

        logger.info(f"[ClinicalTrials Tool] Searching for: {query}")

        # 使用改进的search_and_parse方法（已包含降级策略）
        results = wrapper.search_and_parse(query,
                                           status=status,
                                           max_studies=max_studies)

        if not results:
            logger.warning("[ClinicalTrials Tool] No results found")
            return "No relevant clinical trials found for the given query."

        logger.info(f"[ClinicalTrials Tool] Found {len(results)} trials")

    except Exception as e:
        logger.error(f"[ClinicalTrials Tool] Search failed: {e}")
        return f"Clinical trials search temporarily unavailable. Error: {str(e)[:100]}"

    # 转换为统一格式（临床试验格式略有不同）
    formatted_papers = []
    for item in results[:5]:  # 限制为5个结果以保持一致
        # 构建标题（包含NCT ID）
        title = f"{item.get('briefTitle', '')} (NCT{item.get('nctId', '')})"

        # 构建摘要（包含条件、干预措施和资格标准）
        abstract_parts = []
        if item.get("briefSummary"):
            abstract_parts.append(f"Summary: {item['briefSummary']}")
        if item.get("conditions"):
            abstract_parts.append(f"Conditions: {item['conditions']}")
        if item.get("interventionName"):
            abstract_parts.append(f"Interventions: {item['interventionName']}")
        if item.get("eligibilityCriteria"):
            abstract_parts.append(
                f"Eligibility: {item['eligibilityCriteria'][:200]}...")

        formatted_paper = {
            "title": title,
            "authors": item.get("leadSponsorName", "N/A"),  # 使用赞助商作为"作者"
            "journal": "ClinicalTrials.gov",
            "year": "",  # 临床试验通常没有发表年份
            "citations": 0,
            "doi": "",
            "pmid": "",
            "pmcid": "",
            "published_date": item.get("overallStatus", ""),  # 使用状态代替日期
            "url":
            f"https://clinicaltrials.gov/ct2/show/NCT{item.get('nctId', '')}",
            "abstract": "\n".join(abstract_parts),
        }
        formatted_papers.append(formatted_paper)

    return format_paper_results(formatted_papers)


@tool
def semantic_scholar_search(
    query: str,
    limit: int = 5,
    fields:
    str = "title,authors,year,abstract,url,venue,citationCount,externalIds,publicationDate",
) -> str:
    """
    Search Semantic Scholar for academic papers.
    Useful for finding academic papers with citation counts and comprehensive metadata.

    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 5)
        fields: Comma-separated fields to retrieve (default includes all major fields)

    Returns:
        Formatted search results from Semantic Scholar
    """
    # Get API key from environment variable
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    # Search Semantic Scholar
    papers = search_semantic_scholar(query, api_key, limit, fields)

    if papers is None:
        return "Error occurred while searching Semantic Scholar. Please check your API key and try again."

    if not papers:
        return "No papers found matching the query."

    # Convert to unified format
    formatted_papers = []
    for paper in papers:
        # Extract external IDs
        external_ids = paper.get("externalIds", {}) or {}
        doi = external_ids.get("DOI", "")
        pmid = external_ids.get("PubMed", "")

        # Extract authors
        authors = ", ".join([
            author.get("name", "") for author in paper.get("authors", [])
            if author
        ])

        formatted_paper = {
            "title": paper.get("title", ""),
            "authors": authors,
            "journal": paper.get("venue", ""),
            "year": paper.get("year", ""),
            "citations": paper.get("citationCount", 0),
            "doi": doi,
            "pmid": pmid,
            "pmcid": "",  # Semantic Scholar doesn't provide PMCID
            "published_date": paper.get("publicationDate",
                                        paper.get("year", "")),
            "url": paper.get("url", ""),
            "abstract": paper.get("abstract", ""),
        }
        formatted_papers.append(formatted_paper)

    return format_paper_results(formatted_papers)


# PubMed search tool (using NCBI E-utilities)
@tool
def pubmed_search(query: str) -> str:
    """
    Search PubMed directly via NCBI E-utilities with enhanced stability.
    Includes fallback to Europe PMC for better reliability.

    Args:
        query: Search query string

    Returns:
        Formatted search results from PubMed
    """
    import logging
    logger = logging.getLogger(__name__)

    papers: list = []

    # Primary: direct PubMed with enhanced error handling
    try:
        logger.info(f"[PubMed Tool] Searching PubMed for: {query}")
        wrapper = PubMedAPIWrapper()
        papers = wrapper.run(query)

        if papers:
            logger.info(f"[PubMed Tool] Found {len(papers)} papers from PubMed")
            return format_paper_results(papers)

    except Exception as e:
        logger.warning(f"[PubMed Tool] Direct PubMed search failed: {e}")

    # Fallback: Europe PMC (mirror; generally faster and more stable)
    try:
        logger.info("[PubMed Tool] Trying Europe PMC fallback")
        epmc = EuropePMCAPIWrapper()
        papers = epmc.run(query)

        if papers:
            logger.info(f"[PubMed Tool] Found {len(papers)} papers from Europe PMC")
            return format_paper_results(papers)

    except Exception as e:
        logger.error(f"[PubMed Tool] Europe PMC fallback failed: {e}")

    logger.warning("[PubMed Tool] All search methods failed")
    return "PubMed search temporarily unavailable. Please try again later or use Europe PMC search."


# Export all tools for easy import
__all__ = [
    "europe_pmc_pubmed_search",
    "biorxiv_search",
    "medrxiv_search",
    "clinical_trials_search",
    "semantic_scholar_search",
    "pubmed_search",
]
