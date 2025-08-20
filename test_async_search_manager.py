#!/usr/bin/env python3
"""
测试 AsyncParallelSearchManager 的异步搜索和去重功能
独立运行，避免相对导入问题
"""

import asyncio
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.searchtools.async_parallel_search_manager import AsyncParallelSearchManager


async def test_async_search_and_deduplication():
    """测试异步搜索和去重功能"""
    print("🚀 测试 AsyncParallelSearchManager 异步搜索和去重功能")
    print("=" * 60)

    try:
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

        # 执行异步搜索
        print("\n⏳ 开始异步搜索...")
        start_time = time.time()

        results = await search_manager._async_search_all_sources(test_query)

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
        from src.searchtools.models import SearchResult

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
        print(f"     - 总重复数: {duplicate_stats['total']}")
        print(f"     - 按DOI重复: {duplicate_stats['by_doi']}")
        print(f"     - 按标题重复: {duplicate_stats['by_title']}")

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


if __name__ == "__main__":
    # 运行测试
    try:
        asyncio.run(test_async_search_and_deduplication())
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        import traceback

        traceback.print_exc()
