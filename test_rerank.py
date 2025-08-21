#!/usr/bin/env python3
"""
Rerank算法测试脚本

测试内容：
1. 基本重排序功能
2. 不同排序策略对比
3. 评分算法验证
4. 性能测试
5. 实际搜索结果对比
"""

import sys
import os
import asyncio
import time
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 设置清洁的日志配置
from searchtools.log_config import setup_test_logging
setup_test_logging()

from searchtools.async_parallel_search_manager import AsyncParallelSearchManager
from searchtools.rerank_engine import RerankEngine, RerankConfig
from searchtools.models import SearchResult


def create_test_results():
    """创建测试用的搜索结果"""
    test_results = [
        SearchResult(
            title="COVID-19 vaccine effectiveness in preventing severe disease",
            authors="Smith J, Johnson M, Brown K",
            journal="Nature Medicine",
            year="2023",
            citations=150,
            doi="10.1038/s41591-023-02345-6",
            pmid="37123456",
            published_date="2023-06-15",
            abstract="This comprehensive study evaluates the effectiveness of COVID-19 vaccines in preventing severe disease and hospitalization across multiple healthcare systems. We analyzed data from over 100,000 patients...",
            source="PubMed"
        ),
        SearchResult(
            title="Machine learning approaches for drug discovery",
            authors="Chen L, Wang X, Liu Y",
            journal="Cell",
            year="2024",
            citations=45,
            doi="10.1016/j.cell.2024.01.012",
            pmid="38234567",
            published_date="2024-01-20",
            abstract="Recent advances in machine learning have revolutionized drug discovery processes. This review discusses various ML approaches including deep learning, reinforcement learning...",
            source="Europe PMC"
        ),
        SearchResult(
            title="COVID-19 pandemic response strategies",
            authors="Davis R, Miller S",
            journal="The Lancet",
            year="2022",
            citations=300,
            doi="10.1016/S0140-6736(22)01234-5",
            pmid="35345678",
            published_date="2022-03-10",
            abstract="Analysis of global COVID-19 pandemic response strategies and their effectiveness in different countries. We examine policy interventions, vaccination campaigns...",
            source="Semantic Scholar"
        ),
        SearchResult(
            title="Novel coronavirus vaccine development",
            authors="Anderson P, Thompson K, Wilson J",
            journal="Science",
            year="2021",
            citations=500,
            doi="10.1126/science.abcd1234",
            pmid="34456789",
            published_date="2021-12-01",
            abstract="Development of novel coronavirus vaccines using mRNA technology. This study presents the design, testing, and clinical trial results of a new vaccine candidate...",
            source="PubMed"
        ),
        SearchResult(
            title="COVID-19 treatment protocols in ICU",
            authors="Garcia M, Rodriguez A",
            journal="Critical Care Medicine",
            year="2023",
            citations=80,
            doi="10.1097/CCM.0000000000005678",
            pmid="37567890",
            published_date="2023-09-05",
            abstract="Intensive care unit treatment protocols for COVID-19 patients. We present updated guidelines based on recent clinical evidence and outcomes data...",
            source="Europe PMC"
        )
    ]
    return test_results


def test_basic_rerank():
    """测试基本重排序功能"""
    print("🧪 测试基本重排序功能")
    print("=" * 60)
    
    # 创建测试数据
    test_results = create_test_results()
    query = "COVID-19 vaccine"
    
    # 创建rerank引擎
    rerank_engine = RerankEngine()
    
    print(f"原始结果顺序:")
    for i, result in enumerate(test_results, 1):
        print(f"  {i}. {result.title[:50]}... (引用: {result.citations})")
    
    # 执行重排序
    reranked_results = rerank_engine.rerank_results(test_results, query)
    
    print(f"\n重排序后结果:")
    for i, result in enumerate(reranked_results, 1):
        print(f"  {i}. {result.title[:50]}... (最终评分: {result.final_score:.3f})")
        print(f"     相关性: {result.relevance_score:.2f}, 权威性: {result.authority_score:.2f}, "
              f"时效性: {result.recency_score:.2f}, 质量: {result.quality_score:.2f}")
    
    return reranked_results


def test_different_strategies():
    """测试不同排序策略"""
    print("\n🎯 测试不同排序策略")
    print("=" * 60)
    
    test_results = create_test_results()
    query = "COVID-19 vaccine"
    
    strategies = {
        "相关性优先": RerankConfig(relevance_weight=0.60, authority_weight=0.20, recency_weight=0.15, quality_weight=0.05),
        "权威性优先": RerankConfig(relevance_weight=0.25, authority_weight=0.55, recency_weight=0.10, quality_weight=0.10),
        "时效性优先": RerankConfig(relevance_weight=0.20, authority_weight=0.20, recency_weight=0.50, quality_weight=0.10),
        "平衡策略": RerankConfig(relevance_weight=0.40, authority_weight=0.30, recency_weight=0.20, quality_weight=0.10)
    }
    
    for strategy_name, config in strategies.items():
        print(f"\n📊 {strategy_name}策略:")
        rerank_engine = RerankEngine(config)
        reranked = rerank_engine.rerank_results(test_results.copy(), query)
        
        for i, result in enumerate(reranked[:3], 1):  # 只显示前3个
            print(f"  {i}. {result.title[:40]}... (评分: {result.final_score:.3f})")


def test_scoring_components():
    """测试评分组件"""
    print("\n🔍 测试评分组件")
    print("=" * 60)
    
    rerank_engine = RerankEngine()
    test_result = SearchResult(
        title="COVID-19 vaccine effectiveness study",
        authors="Smith J, Johnson M",
        journal="Nature Medicine",
        year="2023",
        citations=150,
        doi="10.1038/s41591-023-02345-6",
        published_date="2023-06-15",
        abstract="This study evaluates COVID-19 vaccine effectiveness in preventing severe disease and hospitalization.",
        source="PubMed"
    )
    
    query = "COVID-19 vaccine effectiveness"
    keywords = rerank_engine._extract_keywords(query)
    
    # 测试各个评分组件
    relevance_score = rerank_engine._calculate_relevance_score(test_result, query, keywords)
    authority_score = rerank_engine._calculate_authority_score(test_result)
    recency_score = rerank_engine._calculate_recency_score(test_result)
    quality_score = rerank_engine._calculate_quality_score(test_result)
    
    print(f"查询: '{query}'")
    print(f"关键词: {keywords}")
    print(f"相关性评分: {relevance_score:.3f}")
    print(f"权威性评分: {authority_score:.3f}")
    print(f"时效性评分: {recency_score:.3f}")
    print(f"质量评分: {quality_score:.3f}")
    
    # 计算最终评分
    config = rerank_engine.config
    final_score = (
        relevance_score * config.relevance_weight +
        authority_score * config.authority_weight +
        recency_score * config.recency_weight +
        quality_score * config.quality_weight
    )
    print(f"最终评分: {final_score:.3f}")


async def test_integration_with_search_manager():
    """测试与搜索管理器的集成"""
    print("\n🔗 测试与搜索管理器的集成")
    print("=" * 60)
    
    # 创建启用rerank的搜索管理器
    search_manager = AsyncParallelSearchManager(enable_rerank=True)
    
    # 执行实际搜索
    query = "COVID-19 vaccine"
    print(f"执行搜索: '{query}'")
    
    try:
        # 使用新的搜索和去重方法
        results, stats = await search_manager.search_all_sources_with_deduplication(query)
        
        print(f"搜索完成:")
        print(f"  总结果数: {len(results)}")
        print(f"  重排序启用: {stats.get('rerank_enabled', False)}")
        
        # 显示前5个结果
        print(f"\n前5个结果:")
        for i, result in enumerate(results[:5], 1):
            print(f"  {i}. {result.title[:50]}...")
            if hasattr(result, 'final_score') and result.final_score > 0:
                print(f"     最终评分: {result.final_score:.3f}")
            print(f"     来源: {result.source}")
        
    except Exception as e:
        print(f"搜索过程中出错: {e}")


def test_performance():
    """测试性能"""
    print("\n⚡ 测试性能")
    print("=" * 60)
    
    # 创建大量测试数据
    test_results = create_test_results() * 20  # 100个结果
    query = "COVID-19 vaccine"
    
    rerank_engine = RerankEngine()
    
    # 测试重排序性能
    start_time = time.time()
    reranked_results = rerank_engine.rerank_results(test_results, query)
    end_time = time.time()
    
    print(f"重排序 {len(test_results)} 个结果耗时: {(end_time - start_time)*1000:.2f} ms")
    print(f"平均每个结果: {(end_time - start_time)*1000/len(test_results):.2f} ms")
    
    # 验证结果完整性
    assert len(reranked_results) == len(test_results), "结果数量不匹配"
    print("✅ 性能测试通过")


def main():
    """主测试函数"""
    print("🚀 Rerank算法测试开始")
    print("=" * 80)
    
    # 基本功能测试
    test_basic_rerank()
    
    # 不同策略测试
    test_different_strategies()
    
    # 评分组件测试
    test_scoring_components()
    
    # 性能测试
    test_performance()
    
    # 集成测试
    print("\n开始集成测试...")
    asyncio.run(test_integration_with_search_manager())
    
    print("\n🎉 所有测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
