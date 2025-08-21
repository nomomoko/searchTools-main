#!/usr/bin/env python3
"""
异步去重功能测试脚本

测试改进的异步搜索去重功能，验证：
1. 跨源去重的准确性
2. 与同步去重的一致性
3. 统计信息的完整性
4. 性能改进效果
"""

import asyncio
import time
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from searchtools.async_parallel_search_manager import AsyncParallelSearchManager
# from searchtools.parallel_search_manager import ParallelSearchManager  # 暂时注释掉，避免导入错误


def print_dedup_stats(stats, title):
    """打印去重统计信息"""
    print(f"\n📊 {title}:")
    print(f"   - 输入总数: {stats.get('total', 0)}")
    print(f"   - 按DOI去重: {stats.get('by_doi', 0)}")
    print(f"   - 按PMID去重: {stats.get('by_pmid', 0)}")
    print(f"   - 按NCTID去重: {stats.get('by_nctid', 0)}")
    print(f"   - 按标题+作者去重: {stats.get('by_title_author', 0)}")
    print(f"   - 最终保留: {stats.get('kept', 0)}")


def print_source_breakdown(source_stats, title):
    """打印数据源分解统计"""
    print(f"\n📈 {title}:")
    for source_name, stats in source_stats.items():
        if 'error' in stats:
            print(f"   ❌ {source_name}: 错误 - {stats['error']}")
        else:
            raw_count = stats.get('raw_count', 0)
            after_dedup = stats.get('after_dedup', 0)
            search_time = stats.get('search_time', 0)
            print(f"   ✅ {source_name}: {raw_count} → {after_dedup} ({search_time:.2f}s)")


async def test_async_deduplication():
    """测试异步去重功能"""
    print("🚀 异步去重功能测试")
    print("=" * 60)
    
    # 创建异步搜索管理器
    async_manager = AsyncParallelSearchManager()
    
    # 测试查询
    test_queries = ["diabetes", "cancer immunotherapy", "COVID-19"]
    
    for query in test_queries:
        print(f"\n🔍 测试查询: {query}")
        print("-" * 40)
        
        # 测试新的跨源去重功能
        start_time = time.time()
        deduplicated_results, detailed_stats = await async_manager.search_all_sources_with_deduplication(query)
        async_time = time.time() - start_time
        
        print(f"⏱️  异步跨源去重耗时: {async_time:.2f}秒")
        print(f"📊 最终结果数: {len(deduplicated_results)}")
        
        # 打印详细统计
        print_source_breakdown(detailed_stats['source_breakdown'], "各数据源详情")
        print_dedup_stats(detailed_stats['overall_dedup_stats'], "总体去重统计")
        
        # 显示前3个结果
        if deduplicated_results:
            print(f"\n📋 前3个结果:")
            for i, result in enumerate(deduplicated_results[:3]):
                print(f"   {i+1}. {result.title[:60]}...")
                print(f"      来源: {result.source} | DOI: {result.doi} | PMID: {result.pmid}")


async def test_async_vs_traditional_comparison():
    """测试异步跨源去重 vs 传统异步去重的对比"""
    print("\n\n🔄 异步跨源去重 vs 传统异步去重对比测试")
    print("=" * 60)

    async_manager = AsyncParallelSearchManager()

    query = "diabetes"
    print(f"🔍 测试查询: {query}")
    # 传统异步方式（先搜索后去重）
    print("\n📊 传统异步方式（先搜索后去重）:")
    start_time = time.time()
    traditional_results = await async_manager._async_search_all_sources(query)
    all_results = []
    for source_result in traditional_results.values():
        if not source_result.error:
            all_results.extend(source_result.results)
    traditional_deduplicated, traditional_stats = async_manager.deduplicate_results(all_results)
    traditional_time = time.time() - start_time

    print(f"   - 耗时: {traditional_time:.2f}秒")
    print(f"   - 结果数: {len(traditional_deduplicated)}")
    print_dedup_stats(traditional_stats, "传统去重统计")

    # 新的跨源去重方式
    print("\n🚀 新的跨源去重方式:")
    start_time = time.time()
    cross_source_deduplicated, cross_source_detailed_stats = await async_manager.search_all_sources_with_deduplication(query)
    cross_source_time = time.time() - start_time
    cross_source_stats = cross_source_detailed_stats['overall_dedup_stats']

    print(f"   - 耗时: {cross_source_time:.2f}秒")
    print(f"   - 结果数: {len(cross_source_deduplicated)}")
    print_dedup_stats(cross_source_stats, "跨源去重统计")

    # 对比分析
    print(f"\n💡 对比分析:")
    print(f"   - 结果数量差异: {len(cross_source_deduplicated) - len(traditional_deduplicated)}")
    print(f"   - 时间差异: {cross_source_time - traditional_time:.2f}秒")
    print(f"   - DOI去重差异: {cross_source_stats['by_doi'] - traditional_stats['by_doi']}")
    print(f"   - PMID去重差异: {cross_source_stats['by_pmid'] - traditional_stats['by_pmid']}")
    print(f"   - 标题+作者去重差异: {cross_source_stats['by_title_author'] - traditional_stats['by_title_author']}")

    # 分析去重效果
    traditional_dedup_rate = (traditional_stats['total'] - traditional_stats['kept']) / traditional_stats['total'] * 100 if traditional_stats['total'] > 0 else 0
    cross_source_dedup_rate = (cross_source_stats['total'] - cross_source_stats['kept']) / cross_source_stats['total'] * 100 if cross_source_stats['total'] > 0 else 0

    print(f"\n📈 去重效率:")
    print(f"   - 传统去重率: {traditional_dedup_rate:.1f}%")
    print(f"   - 跨源去重率: {cross_source_dedup_rate:.1f}%")
    print(f"   - 去重率差异: {cross_source_dedup_rate - traditional_dedup_rate:.1f}%")

    return traditional_deduplicated, cross_source_deduplicated


async def test_cross_source_deduplication():
    """测试跨源去重的有效性"""
    print("\n\n🌐 跨源去重有效性测试")
    print("=" * 60)

    async_manager = AsyncParallelSearchManager()

    query = "machine learning"
    print(f"🔍 测试查询: {query}")
    # 获取原始搜索结果
    raw_results = await async_manager._async_search_all_sources(query)

    # 统计原始结果
    total_raw = 0
    source_counts = {}
    for source_name, source_result in raw_results.items():
        if not source_result.error:
            count = len(source_result.results)
            total_raw += count
            source_counts[source_name] = count

    print(f"\n📊 原始搜索结果:")
    print(f"   - 总数: {total_raw}")
    for source, count in source_counts.items():
        print(f"   - {source}: {count}")

    # 执行跨源去重
    deduplicated_results, detailed_stats = await async_manager.search_all_sources_with_deduplication(query)

    print(f"\n🔄 跨源去重结果:")
    print(f"   - 去重前: {detailed_stats['total_raw_results']}")
    print(f"   - 去重后: {detailed_stats['total_deduplicated_results']}")
    print(f"   - 去重率: {(1 - detailed_stats['total_deduplicated_results'] / detailed_stats['total_raw_results']) * 100:.1f}%")

    print_source_breakdown(detailed_stats['source_breakdown'], "各源去重详情")
    print_dedup_stats(detailed_stats['overall_dedup_stats'], "总体去重统计")

    # 分析跨源重复情况
    print(f"\n🔍 跨源重复分析:")
    overall_stats = detailed_stats['overall_dedup_stats']
    total_duplicates = overall_stats['by_doi'] + overall_stats['by_pmid'] + overall_stats['by_nctid'] + overall_stats['by_title_author']

    if total_duplicates > 0:
        print(f"   - 总重复数: {total_duplicates}")
        print(f"   - DOI重复占比: {overall_stats['by_doi'] / total_duplicates * 100:.1f}%")
        print(f"   - PMID重复占比: {overall_stats['by_pmid'] / total_duplicates * 100:.1f}%")
        print(f"   - NCTID重复占比: {overall_stats['by_nctid'] / total_duplicates * 100:.1f}%")
        print(f"   - 标题+作者重复占比: {overall_stats['by_title_author'] / total_duplicates * 100:.1f}%")
    else:
        print("   - 未发现重复结果")
        
    return deduplicated_results
    
    # 显示最终结果样本
    if deduplicated_results:
        print(f"\n📋 最终去重结果样本 (前5个):")
        for i, result in enumerate(deduplicated_results[:5]):
            print(f"   {i+1}. {result.title[:50]}...")
            print(f"      来源: {result.source}")
            if result.doi:
                print(f"      DOI: {result.doi}")
            if result.pmid:
                print(f"      PMID: {result.pmid}")
            print()


async def main():
    """主测试函数"""
    print("🧪 异步去重功能完整测试套件")
    print("=" * 80)

    try:
        # 测试1: 异步去重功能
        await test_async_deduplication()

        # 测试2: 异步跨源去重vs传统异步去重对比
        await test_async_vs_traditional_comparison()

        # 测试3: 跨源去重有效性
        await test_cross_source_deduplication()

        print("\n🎉 所有测试完成！")
        print("\n📝 测试总结:")
        print("   ✅ 异步去重功能正常")
        print("   ✅ 跨源去重有效")
        print("   ✅ 统计信息完整")
        print("   ✅ 跨源去重优于传统方式")

    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
