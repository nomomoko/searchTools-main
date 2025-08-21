#!/usr/bin/env python3
"""
Rerank算法测试脚本 v2.0

测试内容：
1. 基本重排序功能
2. 高级算法测试（BM25, TF-IDF, 语义相似度）
3. 机器学习特征测试
4. 不同排序策略对比
5. 性能和缓存测试
6. API集成测试
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
from searchtools.advanced_algorithms import AdvancedRerankAlgorithm
from searchtools.ml_features import AdvancedFeatureExtractor


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


def test_advanced_algorithms():
    """测试高级算法"""
    print("\n🧠 测试高级算法")
    print("=" * 60)

    # 创建测试数据
    test_results = create_test_results()
    query = "COVID-19 vaccine effectiveness"

    # 测试高级算法
    advanced_algo = AdvancedRerankAlgorithm()

    # 准备文档
    documents = [f"{r.title} {r.abstract}" for r in test_results]
    advanced_algo.prepare_documents(documents)
    avg_doc_length = sum(len(doc.split()) for doc in documents) / len(documents)

    print(f"查询: '{query}'")
    print(f"文档数量: {len(documents)}")
    print(f"平均文档长度: {avg_doc_length:.1f} 词")

    # 测试每个算法
    for i, result in enumerate(test_results[:3]):
        document = f"{result.title} {result.abstract}"
        scores = advanced_algo.calculate_advanced_score(query, document, documents, avg_doc_length)

        print(f"\n文档 {i+1}: {result.title[:50]}...")
        for alg_name, score in scores.items():
            print(f"  {alg_name}: {score:.4f}")


def test_ml_features():
    """测试机器学习特征"""
    print("\n🤖 测试机器学习特征")
    print("=" * 60)

    feature_extractor = AdvancedFeatureExtractor()

    # 测试文档
    document = """
    COVID-19 vaccine effectiveness in preventing severe disease and hospitalization.
    This comprehensive study evaluates the effectiveness of COVID-19 vaccines across multiple healthcare systems.
    We analyzed data from over 100,000 patients and found significant protection against severe outcomes.
    The results demonstrate high vaccine effectiveness with important implications for public health policy.
    """

    query = "COVID-19 vaccine effectiveness"

    # 提取特征
    features = feature_extractor.extract_all_features(document, query)

    print(f"查询: '{query}'")
    print(f"文档长度: {len(document)} 字符")

    print(f"\n📊 统计特征:")
    for key, value in features.statistical_features.items():
        print(f"  {key}: {value:.4f}")

    print(f"\n🔤 语言学特征:")
    for key, value in features.linguistic_features.items():
        print(f"  {key}: {value:.4f}")

    print(f"\n📍 位置特征:")
    for key, value in features.positional_features.items():
        print(f"  {key}: {value:.4f}")

    print(f"\n🧠 语义特征:")
    for key, value in features.semantic_features.items():
        print(f"  {key}: {value:.4f}")

    print(f"\n🎯 综合评分: {features.combined_score:.4f}")


def test_performance_and_caching():
    """测试性能和缓存"""
    print("\n⚡ 测试性能和缓存")
    print("=" * 60)

    # 创建启用缓存的rerank引擎
    config = RerankConfig(enable_caching=True, cache_size=100)
    rerank_engine = RerankEngine(config)

    test_results = create_test_results() * 10  # 50个结果
    query = "COVID-19 vaccine"

    # 第一次运行（无缓存）
    start_time = time.time()
    reranked1 = rerank_engine.rerank_results(test_results.copy(), query)
    time1 = time.time() - start_time

    # 第二次运行（有缓存）
    start_time = time.time()
    reranked2 = rerank_engine.rerank_results(test_results.copy(), query)
    time2 = time.time() - start_time

    # 获取性能指标
    metrics = rerank_engine.get_performance_metrics()

    print(f"第一次运行时间: {time1*1000:.2f} ms")
    print(f"第二次运行时间: {time2*1000:.2f} ms")
    print(f"性能提升: {((time1-time2)/time1*100):.1f}%")

    print(f"\n📈 性能指标:")
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")


def main():
    """主测试函数"""
    print("🚀 Rerank算法测试开始 v2.0")
    print("=" * 80)

    # 基本功能测试
    test_basic_rerank()

    # 高级算法测试
    test_advanced_algorithms()

    # 机器学习特征测试
    test_ml_features()

    # 不同策略测试
    test_different_strategies()

    # 评分组件测试
    test_scoring_components()

    # 性能和缓存测试
    test_performance_and_caching()

    # 原有性能测试
    test_performance()

    # 集成测试
    print("\n开始集成测试...")
    asyncio.run(test_integration_with_search_manager())

    print("\n🎉 所有测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
