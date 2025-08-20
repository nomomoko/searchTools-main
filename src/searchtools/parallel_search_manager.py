"""
Parallel search manager for multi-source medical literature searches.
Handles concurrent searches across multiple sources with deduplication.
"""

import concurrent.futures
from typing import List, Dict, Set, Tuple, Any
import time
import logging

from src.tools.search_tools_decorator import (
    europe_pmc_pubmed_search,
    biorxiv_search,
    medrxiv_search,
    clinical_trials_search,
    semantic_scholar_search,
    pubmed_search,
)
from src.storage.models import SearchResult, SourceSearchResult

logger = logging.getLogger(__name__)


class ParallelSearchManager:
    """管理多源并行搜索和去重"""

    def __init__(self):
        from src.tools.search_config import get_config

        config = get_config()

        # 所有可用的搜索源
        all_sources = {
            "epmc": europe_pmc_pubmed_search,
            "biorxiv": biorxiv_search,
            "medrxiv": medrxiv_search,
            "clinical_trials": clinical_trials_search,
            "semantic_scholar": semantic_scholar_search,
            "pubmed": pubmed_search,  # 新增 PubMed（默认禁用）
        }

        # 只保留启用的源
        self.sources = {}
        for source_name, tool in all_sources.items():
            # 获取对应的配置名称（epmc -> europe_pmc）
            config_name = "europe_pmc" if source_name == "epmc" else source_name
            api_config = config.get_api_config(config_name)

            if api_config.enabled:
                self.sources[source_name] = tool
                logger.info(
                    f"[ParallelSearch] Source '{source_name}' is enabled")
            else:
                logger.info(
                    f"[ParallelSearch] Source '{source_name}' is disabled in config"
                )

    def search_all_sources(
            self,
            query: str,
            excluded_sources: List[str] = None,
            max_workers: int = 5) -> Dict[str, SourceSearchResult]:
        """
        并行搜索所有源

        Args:
            query: 搜索查询
            excluded_sources: 要排除的源列表
            max_workers: 最大并行工作线程数

        Returns:
            Dict[source_name, SourceSearchResult]
        """
        excluded = set(excluded_sources or [])
        sources_to_search = {
            k: v
            for k, v in self.sources.items() if k not in excluded
        }

        results = {}

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
            # 提交所有搜索任务
            future_to_source = {
                executor.submit(self._search_single_source, source, tool, query):
                source
                for source, tool in sources_to_search.items()
            }

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    result = future.result()
                    results[source] = result
                    logger.info(
                        f"[ParallelSearch] {source} completed: raw response received"
                    )
                except Exception as e:
                    logger.error(f"[ParallelSearch] {source} failed: {e}")
                    results[source] = SourceSearchResult(
                        source=source,
                        query=query,
                        results=[],
                        results_count=0,
                        error=str(e),
                    )

        return results

    def _search_single_source(self, source: str, tool: Any,
                              query: str) -> SourceSearchResult:
        """搜索单个源"""
        start_time = time.time()

        try:
            # 调用搜索工具
            raw_result = tool.invoke({"query": query})
            search_time = time.time() - start_time

            # 解析结果（这里需要根据不同源的返回格式处理）
            # 暂时返回原始结果，后续会在parser中处理
            return SourceSearchResult(
                source=source,
                query=query,
                results=[{
                    "raw": raw_result
                }],  # 临时存储原始结果
                results_count=1,  # 后续会更新
                search_time=search_time,
            )

        except Exception as e:
            search_time = time.time() - start_time
            error_msg = str(e)

            # Special handling for 403 errors - disable the source
            if "403" in error_msg or "Forbidden" in error_msg:
                logger.warning(
                    f"[ParallelSearch] {source} returned 403 Forbidden - source disabled for this session"
                )
                error_msg = "Source temporarily disabled due to 403 Forbidden error"
            else:
                logger.error(f"[ParallelSearch] Error searching {source}: {e}")

            return SourceSearchResult(
                source=source,
                query=query,
                results=[],
                results_count=0,
                search_time=search_time,
                error=error_msg,
            )

    def deduplicate_results(
        self,
        new_results: List[SearchResult],
        existing_identifiers: Set[Tuple[str, str]] = None,
    ) -> Tuple[List[SearchResult], Dict[str, int]]:
        """
        基于DOI和其他字段去重

        Args:
            new_results: 新的搜索结果
            existing_identifiers: 已存在的标识符集合

        Returns:
            (去重后的结果列表, 去重统计)
        """
        if existing_identifiers is None:
            existing_identifiers = set()
        else:
            # 复制一份，避免修改原集合
            existing_identifiers = existing_identifiers.copy()

        logger.info(
            f"[Deduplication] Starting with {len(new_results)} new results")
        logger.info(
            f"[Deduplication] Existing identifiers count: {len(existing_identifiers)}"
        )
        if len(existing_identifiers) > 0 and len(existing_identifiers) < 10:
            # Log first few identifiers for debugging
            sample_ids = list(existing_identifiers)[:5]
            logger.info(
                f"[Deduplication] Sample existing identifiers: {sample_ids}")

        deduplicated = []
        stats = {
            "total": len(new_results),
            "by_doi": 0,
            "by_pmid": 0,
            "by_nctid": 0,
            "by_title_author": 0,
            "kept": 0,
        }

        for idx, result in enumerate(new_results):
            is_duplicate = False
            duplicate_reason = None

            # 1. 优先检查DOI
            if result.doi:
                if ("doi", result.doi.lower()) in existing_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"DOI: {result.doi}"
                    stats["by_doi"] += 1

            # 2. 检查PMID
            if not is_duplicate and result.pmid:
                if ("pmid", result.pmid) in existing_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"PMID: {result.pmid}"
                    stats["by_pmid"] += 1

            # 3. 检查NCT ID（临床试验）
            if not is_duplicate and hasattr(result, "nctid") and result.nctid:
                if ("nctid", result.nctid) in existing_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"NCTID: {result.nctid}"
                    stats["by_nctid"] += 1

            # 4. 检查标题和作者组合
            if not is_duplicate and not result.doi and not result.pmid:
                first_author = result.authors[0] if result.authors else ""
                title_normalized = result.title.lower().strip()
                identifier = f"{title_normalized}_{first_author.lower().strip()}"

                if ("title_author", identifier) in existing_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"Title+Author: {result.title[:50]}..."
                    stats["by_title_author"] += 1

            # Log first few duplicates for debugging
            if is_duplicate and stats["total"] - stats["kept"] < 3:
                logger.info(
                    f"[Deduplication] Filtered out duplicate #{idx}: {duplicate_reason}"
                )

            # 如果不是重复，添加到结果中
            if not is_duplicate:
                deduplicated.append(result)
                stats["kept"] += 1

                # 更新标识符集合
                if result.doi:
                    existing_identifiers.add(("doi", result.doi.lower()))
                if result.pmid:
                    existing_identifiers.add(("pmid", result.pmid))
                if hasattr(result, "nctid") and result.nctid:
                    existing_identifiers.add(("nctid", result.nctid))
                if not result.doi and not result.pmid:
                    first_author = result.authors[0] if result.authors else ""
                    title_normalized = result.title.lower().strip()
                    identifier = f"{title_normalized}_{first_author.lower().strip()}"
                    existing_identifiers.add(("title_author", identifier))

        return deduplicated, stats
