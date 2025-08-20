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

            # 转换结果格式
            formatted_results = []
            for paper in results:
                # 构建统一的结果格式
                result = {
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", ""),
                    "journal": paper.get("journal", ""),
                    "year": paper.get("year", ""),
                    "citations": paper.get("citations", 0),
                    "doi": paper.get("doi", ""),
                    "pmid": paper.get("pmid", ""),
                    "pmcid": paper.get("pmcid", ""),
                    "published_date": paper.get("published_date", ""),
                    "url": paper.get("url", ""),
                    "abstract": paper.get("abstract", ""),
                    "source": source,
                }

                # 添加源特定的字段
                if source == "clinical_trials":
                    result["nct_id"] = paper.get("nct_id", "")
                    result["status"] = paper.get("status", "")
                    result["conditions"] = paper.get("conditions", "")
                    result["interventions"] = paper.get("interventions", "")

                formatted_results.append(result)

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
        跨源多层级去重（与同步版规则对齐）：
        1) DOI → 2) PMID → 3) NCTID（临床试验）→ 4) 标题+第一作者

        Args:
            new_results: 新的搜索结果
            existing_identifiers: 已存在的标识符集合（跨源共享，键不包含 source）

        Returns:
            (去重后的结果列表, 去重统计)
        """
        # 初始化已见标识集合
        if existing_identifiers is None:
            seen_identifiers: Set[Tuple[str, str]] = set()
        else:
            seen_identifiers = existing_identifiers.copy()

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

        for result in new_results:
            is_duplicate = False

            # 1. DOI（统一小写）
            if result.doi:
                doi_key = ("doi", result.doi.lower().strip())
                if doi_key in seen_identifiers:
                    stats["by_doi"] += 1
                    is_duplicate = True
                else:
                    pass

            # 2. PMID
            if (not is_duplicate) and result.pmid:
                pmid_key = ("pmid", result.pmid.strip())
                if pmid_key in seen_identifiers:
                    stats["by_pmid"] += 1
                    is_duplicate = True

            # 3. NCTID（临床试验）—— 兼容属性名 nct_id / nctid
            nctid_value = getattr(result, "nct_id", "") or getattr(result, "nctid", "")
            if (not is_duplicate) and nctid_value:
                nctid_key = ("nctid", str(nctid_value).strip())
                if nctid_key in seen_identifiers:
                    stats["by_nctid"] += 1
                    is_duplicate = True

            # 4. 标题 + 第一作者（在无 DOI 且无 PMID 的情况下作为兜底）
            if (not is_duplicate) and (not result.doi) and (not result.pmid):
                first_author = _extract_first_author(result.authors)
                title_norm = _normalize_title(result.title)
                ta_key = ("title_author", f"{title_norm}_{first_author.lower().strip()}")
                if ta_key in seen_identifiers:
                    stats["by_title_author"] += 1
                    is_duplicate = True

            if not is_duplicate:
                # 保留结果
                deduplicated.append(result)
                stats["kept"] += 1

                # 写入已见集合（按强键优先）
                if result.doi:
                    seen_identifiers.add(("doi", result.doi.lower().strip()))
                if result.pmid:
                    seen_identifiers.add(("pmid", result.pmid.strip()))
                if nctid_value:
                    seen_identifiers.add(("nctid", str(nctid_value).strip()))
                if (not result.doi) and (not result.pmid):
                    first_author = _extract_first_author(result.authors)
                    title_norm = _normalize_title(result.title)
                    seen_identifiers.add(("title_author", f"{title_norm}_{first_author.lower().strip()}"))

        return deduplicated, stats

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
        """测试异步搜索和去重功能"""
        print("🚀 测试 AsyncParallelSearchManager 异步搜索和去重功能")
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
        test_query = "cancer immunotherapy"
        print(f"\n🔍 测试查询: {test_query}")

        try:
            # 执行异步搜索
            print("\n⏳ 开始异步搜索...")
            start_time = time.time()

            results = await search_manager._async_search_all_sources(test_query
                                                                     )

            search_time = time.time() - start_time
            print(f"✅ 搜索完成，耗时: {search_time:.2f}秒")

            # 显示搜索结果统计
            print("\n📊 搜索结果统计:")
            total_results = 0
            for source_name, source_result in results.items():
                if hasattr(source_result, "error") and source_result.error:
                    print(f"   {source_name}: ❌ {source_result.error}")
                else:
                    result_count = getattr(source_result, "results_count", 0)
                    search_time = getattr(source_result, "search_time", 0)
                    total_results += result_count
                    print(
                        f"   {source_name}: ✅ {result_count} 个结果 (耗时: {search_time:.2f}s)"
                    )

            print(f"\n   总计: {total_results} 个结果")

            # 收集所有结果进行去重
            print("\n🔄 开始去重处理...")

            # 转换为 SearchResult 对象列表
            all_results = []
            for source_name, source_result in results.items():
                if hasattr(source_result, "error") and source_result.error:
                    continue

                for result_data in getattr(source_result, "results", []):
                    search_result = SearchResult(
                        title=result_data.get("title", ""),
                        authors=result_data.get("authors", ""),
                        journal=result_data.get("journal", ""),
                        year=result_data.get("year", ""),
                        citations=result_data.get("citations", 0),
                        doi=result_data.get("doi", ""),
                        pmid=result_data.get("pmid", ""),
                        pmcid=result_data.get("pmcid", ""),
                        published_date=result_data.get("published_date", ""),
                        url=result_data.get("url", ""),
                        abstract=result_data.get("abstract", ""),
                        source=source_name,
                    )
                    all_results.append(search_result)

            print(f"   去重前结果数量: {len(all_results)}")

            # 执行去重
            deduplicated_results, duplicate_stats = search_manager.deduplicate_results(
                all_results)

            print(f"   去重后结果数量: {len(deduplicated_results)}")
            print("   重复结果统计:")
            print(f"     - 输入总数: {duplicate_stats['total']}")
            print(f"     - 按DOI重复: {duplicate_stats['by_doi']}")
            print(f"     - 按PMID重复: {duplicate_stats['by_pmid']}")
            print(f"     - 按NCTID重复: {duplicate_stats['by_nctid']}")
            print(f"     - 按标题+作者重复: {duplicate_stats['by_title_author']}")
            print(f"     - 保留数量: {duplicate_stats['kept']}")

            # 显示去重后的前几个结果
            if deduplicated_results:
                print("\n📋 去重后的前3个结果:")
                for i, result in enumerate(deduplicated_results[:3]):
                    print(f"   {i + 1}. {result.title}")
                    print(f"      作者: {result.authors}")
                    print(f"      期刊: {result.journal}")
                    print(f"      年份: {result.year}")
                    print(f"      DOI: {result.doi}")
                    print(f"      来源: {result.source}")
                    print()

            print("✅ 测试完成！")

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
