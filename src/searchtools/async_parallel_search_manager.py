"""
异步版本的并行搜索管理器
内部使用异步并发，外部保持同步接口
"""

import asyncio
import time
import logging
from typing import List, Dict, Set, Tuple, Any

# 导入异步搜索包装器
from .searchAPIchoose.async_europe_pmc import AsyncEuropePMCAPIWrapper
from .searchAPIchoose.async_biorxiv import AsyncBioRxivAPIWrapper
from .searchAPIchoose.async_medrxiv import AsyncMedRxivAPIWrapper
from .searchAPIchoose.async_clinical_trials import AsyncClinicalTrialsAPIWrapper
from .searchAPIchoose.async_semantic import AsyncSemanticScholarWrapper
from .searchAPIchoose.async_pubmed import AsyncPubMedAPIWrapper

# 导入数据模型
from .models import SearchResult, SourceSearchResult

logger = logging.getLogger(__name__)


def _extract_first_author(authors: str) -> str:
    """
    提取第一作者姓名

    Args:
        authors: 作者字符串，可能是多种格式

    Returns:
        第一作者姓名，如果无法提取则返回空字符串
    """
    if not authors:
        return ""

    # 处理不同的作者分隔符
    separators = [";", ",", " and ", " & ", "\n"]
    first_author = authors

    for sep in separators:
        if sep in authors:
            first_author = authors.split(sep)[0].strip()
            break

    # 清理作者名字（移除常见的后缀）
    suffixes_to_remove = [" Jr.", " Sr.", " III", " II", " PhD", " MD", " Dr."]
    for suffix in suffixes_to_remove:
        if first_author.endswith(suffix):
            first_author = first_author[:-len(suffix)].strip()

    return first_author


def _normalize_title(title: str) -> str:
    """
    标准化标题用于去重比较

    Args:
        title: 原始标题

    Returns:
        标准化后的标题
    """
    if not title:
        return ""

    # 转换为小写并移除多余空格
    normalized = title.lower().strip()

    # 移除常见的标点符号
    import re
    normalized = re.sub(r'[^\w\s]', ' ', normalized)

    # 移除多余的空格
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    return normalized


class AsyncParallelSearchManager:
    """异步版本的多源并行搜索管理器"""

    def __init__(self):
        from .search_config import get_config

        config = get_config()

        # 初始化所有异步搜索源
        self.async_sources = {}

        # Europe PMC
        api_config = config.get_api_config("europe_pmc")
        if api_config.enabled:
            self.async_sources["epmc"] = AsyncEuropePMCAPIWrapper(
                page_size=api_config.max_results)
            logger.info("[AsyncParallelSearch] Europe PMC enabled")

        # BioRxiv
        api_config = config.get_api_config("biorxiv")
        if api_config.enabled:
            self.async_sources["biorxiv"] = AsyncBioRxivAPIWrapper()
            logger.info("[AsyncParallelSearch] BioRxiv enabled")

        # MedRxiv
        api_config = config.get_api_config("medrxiv")
        if api_config.enabled:
            self.async_sources["medrxiv"] = AsyncMedRxivAPIWrapper()
            logger.info("[AsyncParallelSearch] MedRxiv enabled")

        # Clinical Trials
        api_config = config.get_api_config("clinical_trials")
        if api_config.enabled:
            self.async_sources[
                "clinical_trials"] = AsyncClinicalTrialsAPIWrapper()
            logger.info("[AsyncParallelSearch] Clinical Trials enabled")

        # Semantic Scholar
        api_config = config.get_api_config("semantic_scholar")
        # 获取 API key（如果有的话）
        semantic_api_key = getattr(config, "semantic_scholar_api_key",
                                   "") or ""
        if api_config.enabled and semantic_api_key:
            self.async_sources[
                "semantic_scholar"] = AsyncSemanticScholarWrapper(
                    api_key=semantic_api_key, limit=api_config.max_results)
            logger.info("[AsyncParallelSearch] Semantic Scholar enabled")
        elif api_config.enabled:
            logger.warning(
                "[AsyncParallelSearch] Semantic Scholar enabled but no API key found"
            )

        # PubMed
        api_config = config.get_api_config("pubmed")
        if api_config.enabled:
            self.async_sources["pubmed"] = AsyncPubMedAPIWrapper(
                top_k_results=api_config.max_results)
            logger.info("[AsyncParallelSearch] PubMed enabled")

    def search_all_sources(
            self,
            query: str,
            excluded_sources: List[str] = None,
            max_workers: int = None) -> Dict[str, SourceSearchResult]:
        """
        并行搜索所有源 - 同步接口（内部使用异步）

        Args:
            query: 搜索查询
            excluded_sources: 要排除的源列表
            max_workers: 这个参数在异步版本中被忽略

        Returns:
            Dict[source_name, SourceSearchResult]
        """
        # 使用 asyncio.run 运行异步版本
        return asyncio.run(
            self._async_search_all_sources(query, excluded_sources))

    async def _async_search_all_sources(self,
                                        query: str,
                                        excluded_sources: List[str] = None
                                        ) -> Dict[str, SourceSearchResult]:
        """
        异步并行搜索所有源

        Args:
            query: 搜索查询
            excluded_sources: 要排除的源列表

        Returns:
            Dict[source_name, SourceSearchResult]
        """
        excluded = set(excluded_sources or [])
        sources_to_search = {
            k: v
            for k, v in self.async_sources.items() if k not in excluded
        }

        # 创建所有搜索任务
        tasks = []
        for source_name, wrapper in sources_to_search.items():
            task = self._search_single_source_async(source_name, wrapper,
                                                    query)
            tasks.append((source_name, task))

        # 并发执行所有搜索
        results = {}
        search_results = await asyncio.gather(*[task for _, task in tasks],
                                              return_exceptions=True)

        # 处理结果
        for (source_name, _), result in zip(tasks, search_results):
            if isinstance(result, Exception):
                logger.error(
                    f"[AsyncParallelSearch] {source_name} failed: {result}")
                results[source_name] = SourceSearchResult(
                    source=source_name,
                    query=query,
                    results=[],
                    results_count=0,
                    error=str(result),
                )
            else:
                results[source_name] = result
                logger.info(
                    f"[AsyncParallelSearch] {source_name} completed: {result.results_count} results"
                )

        return results

    async def _search_single_source_async(self, source: str, wrapper: Any,
                                          query: str) -> SourceSearchResult:
        """异步搜索单个源"""
        start_time = time.time()

        try:
            # 调用异步搜索方法
            results = await wrapper.run(query)
            search_time = time.time() - start_time

            # 转换结果格式为SearchResult对象
            formatted_results = []
            for paper in results:
                # 构建SearchResult对象
                search_result = SearchResult(
                    title=paper.get("title", ""),
                    authors=paper.get("authors", ""),
                    journal=paper.get("journal", ""),
                    year=paper.get("year", ""),
                    citations=paper.get("citations", 0),
                    doi=paper.get("doi", ""),
                    pmid=paper.get("pmid", ""),
                    pmcid=paper.get("pmcid", ""),
                    published_date=paper.get("published_date", ""),
                    url=paper.get("url", ""),
                    abstract=paper.get("abstract", ""),
                    source=source,
                )

                # 添加源特定的字段
                if source == "clinical_trials":
                    search_result.nct_id = paper.get("nct_id", "")
                    search_result.status = paper.get("status", "")
                    search_result.conditions = paper.get("conditions", "")
                    search_result.interventions = paper.get("interventions", "")

                formatted_results.append(search_result)

            return SourceSearchResult(
                source=source,
                query=query,
                results=formatted_results,
                results_count=len(formatted_results),
                search_time=search_time,
            )

        except Exception as e:
            search_time = time.time() - start_time
            error_msg = str(e)

            # 处理特殊错误
            if "403" in error_msg or "Forbidden" in error_msg:
                logger.warning(
                    f"[AsyncParallelSearch] {source} returned 403 Forbidden")
                error_msg = "Source temporarily disabled due to 403 Forbidden error"
            else:
                logger.error(
                    f"[AsyncParallelSearch] Error searching {source}: {e}")

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
        跨源多层级去重（与同步版本完全一致）：
        1) DOI → 2) PMID → 3) NCTID（临床试验）→ 4) 标题+第一作者

        Args:
            new_results: 新的搜索结果（SearchResult对象列表）
            existing_identifiers: 已存在的标识符集合（跨源共享）

        Returns:
            (去重后的结果列表, 去重统计)
        """
        # 初始化已见标识集合
        if existing_identifiers is None:
            seen_identifiers: Set[Tuple[str, str]] = set()
        else:
            seen_identifiers = existing_identifiers.copy()

        logger.info(f"[AsyncDeduplication] Starting with {len(new_results)} new results")
        logger.info(f"[AsyncDeduplication] Existing identifiers count: {len(seen_identifiers)}")

        if len(seen_identifiers) > 0 and len(seen_identifiers) < 10:
            # Log first few identifiers for debugging
            sample_ids = list(seen_identifiers)[:5]
            logger.info(f"[AsyncDeduplication] Sample existing identifiers: {sample_ids}")

        deduplicated: List[SearchResult] = []
        stats: Dict[str, int] = {
            "total": len(new_results),
            "by_doi": 0,
            "by_pmid": 0,
            "by_nctid": 0,
            "by_title_author": 0,
            "kept": 0,
        }

        # 工具函数：提取第一作者（从字符串切分）
        def _extract_first_author(authors: str) -> str:
            if not authors:
                return ""
            # 常见分隔符：逗号、分号、and、&
            import re

            parts = re.split(r";|,|\band\b|&", authors, flags=re.IGNORECASE)
            first = parts[0].strip() if parts else ""
            return first

        # 工具函数：规范化标题
        def _normalize_title(title: str) -> str:
            return (title or "").lower().strip()

        for idx, result in enumerate(new_results):
            is_duplicate = False
            duplicate_reason = None

            # 1. 优先检查DOI（统一小写）
            if result.doi:
                doi_key = ("doi", result.doi.lower().strip())
                if doi_key in seen_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"DOI: {result.doi}"
                    stats["by_doi"] += 1

            # 2. 检查PMID
            if not is_duplicate and result.pmid:
                pmid_key = ("pmid", result.pmid.strip())
                if pmid_key in seen_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"PMID: {result.pmid}"
                    stats["by_pmid"] += 1

            # 3. 检查NCT ID（临床试验）- 兼容多种属性名
            nctid_value = getattr(result, "nct_id", "") or getattr(result, "nctid", "")
            if not is_duplicate and nctid_value:
                nctid_key = ("nctid", str(nctid_value).strip())
                if nctid_key in seen_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"NCTID: {nctid_value}"
                    stats["by_nctid"] += 1

            # 4. 检查标题和作者组合（在无DOI且无PMID的情况下作为兜底）
            if not is_duplicate and not result.doi and not result.pmid:
                first_author = _extract_first_author(result.authors)
                title_normalized = _normalize_title(result.title)
                identifier = f"{title_normalized}_{first_author.lower().strip()}"
                ta_key = ("title_author", identifier)

                if ta_key in seen_identifiers:
                    is_duplicate = True
                    duplicate_reason = f"Title+Author: {result.title[:50]}..."
                    stats["by_title_author"] += 1

            # Log first few duplicates for debugging
            if is_duplicate and stats["total"] - stats["kept"] < 3:
                logger.info(f"[AsyncDeduplication] Filtered out duplicate #{idx}: {duplicate_reason}")

            # 如果不是重复，添加到结果中
            if not is_duplicate:
                deduplicated.append(result)
                stats["kept"] += 1

                # 更新标识符集合（按强键优先）
                if result.doi:
                    seen_identifiers.add(("doi", result.doi.lower().strip()))
                if result.pmid:
                    seen_identifiers.add(("pmid", result.pmid.strip()))
                if nctid_value:
                    seen_identifiers.add(("nctid", str(nctid_value).strip()))
                if not result.doi and not result.pmid:
                    first_author = _extract_first_author(result.authors)
                    title_normalized = _normalize_title(result.title)
                    identifier = f"{title_normalized}_{first_author.lower().strip()}"
                    seen_identifiers.add(("title_author", identifier))

        logger.info(f"[AsyncDeduplication] Completed: kept {stats['kept']} out of {stats['total']} results")
        return deduplicated, stats

    async def search_all_sources_with_deduplication(
        self,
        query: str,
        excluded_sources: List[str] = None
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        执行跨源搜索并进行统一去重

        Args:
            query: 搜索查询
            excluded_sources: 要排除的源列表

        Returns:
            (去重后的结果列表, 详细统计信息)
        """
        # 执行异步搜索
        source_results = await self._async_search_all_sources(query, excluded_sources)

        # 收集所有结果并进行跨源去重
        all_results = []
        source_stats = {}
        seen_identifiers = set()

        # 按源处理结果，实现真正的跨源去重
        for source_name, source_result in source_results.items():
            if source_result.error:
                logger.warning(f"[AsyncCrossSourceDedup] {source_name} failed: {source_result.error}")
                source_stats[source_name] = {
                    "raw_count": 0,
                    "after_dedup": 0,
                    "error": source_result.error
                }
                continue

            # 对当前源的结果进行去重
            source_deduplicated, source_dedup_stats = self.deduplicate_results(
                source_result.results, seen_identifiers
            )

            # 更新seen_identifiers以影响后续源的去重
            for result in source_deduplicated:
                if result.doi:
                    seen_identifiers.add(("doi", result.doi.lower().strip()))
                if result.pmid:
                    seen_identifiers.add(("pmid", result.pmid.strip()))
                nctid_value = getattr(result, "nct_id", "") or getattr(result, "nctid", "")
                if nctid_value:
                    seen_identifiers.add(("nctid", str(nctid_value).strip()))
                if not result.doi and not result.pmid:
                    first_author = _extract_first_author(result.authors)
                    title_normalized = _normalize_title(result.title)
                    identifier = f"{title_normalized}_{first_author.lower().strip()}"
                    seen_identifiers.add(("title_author", identifier))

            all_results.extend(source_deduplicated)
            source_stats[source_name] = {
                "raw_count": source_result.results_count,
                "after_dedup": len(source_deduplicated),
                "dedup_stats": source_dedup_stats,
                "search_time": source_result.search_time
            }

            logger.info(f"[AsyncCrossSourceDedup] {source_name}: {source_result.results_count} → {len(source_deduplicated)} after dedup")

        # 计算总体统计信息
        total_stats = {
            "query": query,
            "total_sources": len(source_results),
            "successful_sources": len([s for s in source_stats.values() if "error" not in s]),
            "total_raw_results": sum(s.get("raw_count", 0) for s in source_stats.values()),
            "total_deduplicated_results": len(all_results),
            "source_breakdown": source_stats,
            "overall_dedup_stats": {
                "total": sum(s.get("dedup_stats", {}).get("total", 0) for s in source_stats.values()),
                "by_doi": sum(s.get("dedup_stats", {}).get("by_doi", 0) for s in source_stats.values()),
                "by_pmid": sum(s.get("dedup_stats", {}).get("by_pmid", 0) for s in source_stats.values()),
                "by_nctid": sum(s.get("dedup_stats", {}).get("by_nctid", 0) for s in source_stats.values()),
                "by_title_author": sum(s.get("dedup_stats", {}).get("by_title_author", 0) for s in source_stats.values()),
                "kept": len(all_results)
            }
        }

        logger.info(f"[AsyncCrossSourceDedup] Final results: {total_stats['total_raw_results']} → {len(all_results)} after cross-source deduplication")

        return all_results, total_stats

    def search_all_sources_with_deduplication_sync(
        self,
        query: str,
        excluded_sources: List[str] = None
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        同步版本的跨源搜索和去重（用于测试和兼容性）

        Args:
            query: 搜索查询
            excluded_sources: 要排除的源列表

        Returns:
            (去重后的结果列表, 详细统计信息)
        """
        # 使用asyncio.run执行异步版本
        return asyncio.run(self.search_all_sources_with_deduplication(query, excluded_sources))

    def _is_similar_title(self, title1: str, title2: str) -> bool:
        """简单的标题相似度检查"""
        # 移除标点符号并转换为小写
        import re

        clean1 = re.sub(r"[^\w\s]", "", title1.lower())
        clean2 = re.sub(r"[^\w\s]", "", title2.lower())

        # 简单的相似度检查
        return clean1 == clean2


# 为了兼容性，创建一个别名
ParallelSearchManager = AsyncParallelSearchManager

if __name__ == "__main__":
    """测试 AsyncParallelSearchManager 的异步搜索和去重功能"""

    # 修复导入问题 - 使用绝对导入
    import sys
    import os

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from src.searchtools.models import SearchResult

    async def test_async_search_and_deduplication():
        """测试改进的异步搜索和跨源去重功能"""
        print("🚀 测试改进的 AsyncParallelSearchManager 功能")
        print("=" * 60)

        # 创建搜索管理器实例
        search_manager = AsyncParallelSearchManager()

        # 显示启用的搜索源
        print(f"✅ 启用的搜索源数量: {len(search_manager.async_sources)}")
        for source_name in search_manager.async_sources.keys():
            print(f"   - {source_name}")

        if not search_manager.async_sources:
            print("❌ 没有启用的搜索源，请检查配置")
            return

        # 测试查询
        test_query = "diabetes"
        print(f"\n🔍 测试查询: {test_query}")

        try:
            # 测试新的跨源去重功能
            print("\n🚀 测试跨源去重功能:")
            start_time = time.time()

            deduplicated_results, detailed_stats = search_manager.search_all_sources_with_deduplication(test_query)
            search_time = time.time() - start_time

            print(f"✅ 跨源搜索和去重完成，耗时: {search_time:.2f}秒")

            # 显示详细统计信息
            print(f"\n📊 详细统计信息:")
            print(f"   - 查询: {detailed_stats['query']}")
            print(f"   - 总数据源: {detailed_stats['total_sources']}")
            print(f"   - 成功数据源: {detailed_stats['successful_sources']}")
            print(f"   - 原始结果总数: {detailed_stats['total_raw_results']}")
            print(f"   - 去重后结果数: {detailed_stats['total_deduplicated_results']}")

            print(f"\n📈 各数据源详情:")
            for source_name, source_stat in detailed_stats['source_breakdown'].items():
                if 'error' in source_stat:
                    print(f"   ❌ {source_name}: 错误 - {source_stat['error']}")
                else:
                    print(f"   ✅ {source_name}: {source_stat['raw_count']} → {source_stat['after_dedup']} "
                          f"({source_stat['search_time']:.2f}s)")

            print(f"\n🔄 总体去重统计:")
            overall_stats = detailed_stats['overall_dedup_stats']
            print(f"   - 输入总数: {overall_stats['total']}")
            print(f"   - 按DOI去重: {overall_stats['by_doi']}")
            print(f"   - 按PMID去重: {overall_stats['by_pmid']}")
            print(f"   - 按NCTID去重: {overall_stats['by_nctid']}")
            print(f"   - 按标题+作者去重: {overall_stats['by_title_author']}")
            print(f"   - 最终保留: {overall_stats['kept']}")

            # 显示跨源去重后的结果
            if deduplicated_results:
                print(f"\n📋 跨源去重后的前5个结果:")
                for i, result in enumerate(deduplicated_results[:5]):
                    print(f"   {i + 1}. {result.title}")
                    print(f"      作者: {result.authors}")
                    print(f"      期刊: {result.journal}")
                    print(f"      年份: {result.year}")
                    print(f"      DOI: {result.doi}")
                    print(f"      来源: {result.source}")
                    print()

            print("✅ 跨源去重测试完成！")

            # 对比测试：展示改进前后的差异
            print("\n🔄 对比测试 - 传统方式 vs 改进方式:")

            # 传统方式
            print("📊 传统方式（先搜索后去重）:")
            start_time = time.time()
            traditional_results = search_manager.search_all_sources(test_query)
            all_results = []
            for source_result in traditional_results.values():
                if not source_result.error:
                    all_results.extend(source_result.results)
            traditional_deduplicated, traditional_stats = search_manager.deduplicate_results(all_results)
            traditional_time = time.time() - start_time

            print(f"   - 耗时: {traditional_time:.2f}秒")
            print(f"   - 结果数: {len(traditional_deduplicated)}")
            print(f"   - 去重统计: DOI:{traditional_stats['by_doi']}, PMID:{traditional_stats['by_pmid']}, "
                  f"NCTID:{traditional_stats['by_nctid']}, Title+Author:{traditional_stats['by_title_author']}")

            print("🚀 改进方式（跨源去重）:")
            print(f"   - 耗时: {search_time:.2f}秒")
            print(f"   - 结果数: {len(deduplicated_results)}")
            print(f"   - 去重统计: DOI:{overall_stats['by_doi']}, PMID:{overall_stats['by_pmid']}, "
                  f"NCTID:{overall_stats['by_nctid']}, Title+Author:{overall_stats['by_title_author']}")

            print(f"\n💡 改进效果:")
            print(f"   - 结果数量差异: {len(deduplicated_results) - len(traditional_deduplicated)}")
            print(f"   - 时间差异: {search_time - traditional_time:.2f}秒")

            print("\n🎉 所有测试完成！")

        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            import traceback

            traceback.print_exc()

    # 运行测试
    try:
        asyncio.run(test_async_search_and_deduplication())
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        import traceback

        traceback.print_exc()
