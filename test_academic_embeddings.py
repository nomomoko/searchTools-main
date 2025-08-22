#!/usr/bin/env python3
"""
学术Embedding和混合检索系统测试

测试新的学术优化功能：
1. SPECTER2/SciBERT embedding
2. ColBERT重排序
3. 学术特征提取
4. 混合检索系统
5. 性能基准测试
"""

import os
import sys
import time
import asyncio
import logging
from typing import List, Dict

# 添加src路径
sys.path.insert(0, 'src')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_academic_embeddings():
    """测试学术embedding功能"""
    print("\n🧠 测试学术Embedding功能")
    print("=" * 60)
    
    try:
        from searchtools.academic_embeddings import create_academic_embedder
        
        # 测试论文数据
        test_papers = [
            {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers."
            },
            {
                "title": "Attention Is All You Need",
                "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism."
            },
            {
                "title": "COVID-19 vaccine effectiveness against severe disease",
                "abstract": "We evaluated the effectiveness of COVID-19 vaccines against severe disease outcomes including hospitalization and death in a large population-based study."
            }
        ]
        
        # 测试不同的embedding模型
        models_to_test = ["specter2", "scibert"]  # BGE-M3需要额外安装
        
        for model_name in models_to_test:
            print(f"\n📊 测试 {model_name.upper()} 模型:")
            
            try:
                # 创建embedder
                embedder = create_academic_embedder(model_name=model_name)
                
                # 编码论文
                start_time = time.time()
                embeddings = embedder.encode_papers(test_papers)
                encoding_time = time.time() - start_time
                
                print(f"✅ 编码完成: {len(embeddings)} 篇论文")
                print(f"⏱️  编码时间: {encoding_time:.3f}秒")
                print(f"📐 向量维度: {embeddings[0].shape}")
                
                # 计算相似度
                sim_12 = embedder.compute_similarity(embeddings[0], embeddings[1])
                sim_13 = embedder.compute_similarity(embeddings[0], embeddings[2])
                sim_23 = embedder.compute_similarity(embeddings[1], embeddings[2])
                
                print(f"🔗 BERT vs Attention: {sim_12:.3f}")
                print(f"🔗 BERT vs COVID: {sim_13:.3f}")
                print(f"🔗 Attention vs COVID: {sim_23:.3f}")
                
                # 获取统计信息
                stats = embedder.get_stats()
                print(f"📈 统计: {stats}")
                
            except Exception as e:
                print(f"❌ {model_name} 测试失败: {e}")
                if "transformers" in str(e):
                    print("💡 提示: 安装transformers库: pip install transformers torch")
                elif "FlagEmbedding" in str(e):
                    print("💡 提示: 安装FlagEmbedding库: pip install FlagEmbedding")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("💡 请确保已安装必要的依赖包")

def test_colbert_reranker():
    """测试ColBERT重排序功能"""
    print("\n🎯 测试ColBERT重排序功能")
    print("=" * 60)
    
    try:
        from searchtools.colbert_reranker import create_colbert_reranker
        
        # 测试查询和文档
        query = "machine learning for drug discovery"
        
        documents = [
            {
                "title": "Deep Learning for Drug Discovery: A Comprehensive Review",
                "abstract": "This review covers the application of deep learning methods in pharmaceutical research, including molecular property prediction and drug-target interaction modeling.",
                "citations": 150,
                "journal": "Nature Reviews Drug Discovery"
            },
            {
                "title": "COVID-19 Vaccine Development Timeline",
                "abstract": "We present a timeline of COVID-19 vaccine development from initial virus sequencing to emergency use authorization.",
                "citations": 80,
                "journal": "Science"
            },
            {
                "title": "Machine Learning Applications in Computational Biology",
                "abstract": "Machine learning has revolutionized computational biology, enabling new approaches to protein structure prediction, genomics, and systems biology.",
                "citations": 200,
                "journal": "Cell"
            },
            {
                "title": "Artificial Intelligence in Healthcare: Current Applications",
                "abstract": "AI technologies are being deployed across healthcare, from diagnostic imaging to clinical decision support systems.",
                "citations": 120,
                "journal": "NEJM"
            }
        ]
        
        try:
            # 创建重排序器
            reranker = create_colbert_reranker(academic_mode=True)
            
            # 执行重排序
            start_time = time.time()
            results = reranker.rerank(query, documents, top_k=4)
            rerank_time = time.time() - start_time
            
            print(f"✅ 重排序完成: {len(results)} 个结果")
            print(f"⏱️  重排序时间: {rerank_time:.3f}秒")
            
            # 显示结果
            print("\n📋 重排序结果:")
            for i, (orig_idx, score, doc) in enumerate(results, 1):
                print(f"{i}. [{score:.3f}] {doc['title'][:60]}...")
                print(f"   期刊: {doc['journal']}, 引用: {doc['citations']}")
            
            # 获取统计信息
            stats = reranker.get_stats()
            print(f"\n📈 统计: {stats}")
            
        except Exception as e:
            print(f"❌ ColBERT测试失败: {e}")
            if "colbert" in str(e).lower():
                print("💡 提示: ColBERT库未安装，使用transformers实现")
            elif "transformers" in str(e):
                print("💡 提示: 安装transformers库: pip install transformers torch")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")

def test_academic_features():
    """测试学术特征提取功能"""
    print("\n🔬 测试学术特征提取功能")
    print("=" * 60)
    
    try:
        from searchtools.academic_features import extract_academic_features
        
        # 测试论文
        test_paper = {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
            "authors": "Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova",
            "journal": "NAACL",
            "year": 2019,
            "citations": 50000,
            "doi": "10.18653/v1/N19-1423",
            "keywords": "natural language processing, transformers, pre-training"
        }
        
        # 提取特征
        start_time = time.time()
        features = extract_academic_features(test_paper)
        extraction_time = time.time() - start_time
        
        print(f"✅ 特征提取完成，耗时: {extraction_time:.3f}秒")
        
        # 显示特征
        print("\n📊 学术特征:")
        print(f"📖 基础特征:")
        print(f"   引用数: {features.citation_count}")
        print(f"   发表年份: {features.publication_year}")
        print(f"   期刊影响因子: {features.journal_impact_factor:.3f}")
        print(f"   标题长度: {features.title_length}")
        print(f"   摘要长度: {features.abstract_length}")
        
        print(f"\n🏆 权威性特征:")
        print(f"   作者声誉: {features.author_reputation:.3f}")
        print(f"   期刊声誉: {features.venue_prestige:.3f}")
        print(f"   机构排名: {features.institutional_ranking:.3f}")
        
        print(f"\n🌐 网络特征:")
        print(f"   引用速度: {features.citation_velocity:.3f}")
        print(f"   共引强度: {features.co_citation_strength:.3f}")
        print(f"   文献耦合: {features.bibliographic_coupling:.3f}")
        
        print(f"\n⏰ 时间特征:")
        print(f"   时效性分数: {features.recency_score:.3f}")
        print(f"   时间相关性: {features.temporal_relevance:.3f}")
        
        print(f"\n✨ 质量特征:")
        print(f"   完整性分数: {features.completeness_score:.3f}")
        print(f"   方法学分数: {features.methodology_score:.3f}")
        print(f"   可重现性分数: {features.reproducibility_score:.3f}")
        
        print(f"\n🎯 领域特征:")
        print(f"   领域专一性: {features.field_specificity:.3f}")
        print(f"   跨学科性: {features.interdisciplinary_score:.3f}")
        print(f"   新颖性分数: {features.novelty_score:.3f}")
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
    except Exception as e:
        print(f"❌ 特征提取失败: {e}")

def test_hybrid_retrieval():
    """测试混合检索系统"""
    print("\n🚀 测试混合检索系统")
    print("=" * 60)
    
    try:
        from searchtools.hybrid_retrieval import create_hybrid_system
        
        # 测试查询
        query = "COVID-19 vaccine effectiveness"
        
        # 测试文档集合
        documents = [
            {
                "title": "COVID-19 vaccine effectiveness against severe disease and death",
                "abstract": "We evaluated the real-world effectiveness of COVID-19 vaccines against severe disease outcomes in a large population-based study.",
                "authors": "Smith J, Johnson A, Brown K",
                "journal": "New England Journal of Medicine",
                "year": 2021,
                "citations": 500,
                "doi": "10.1056/NEJMoa2021436"
            },
            {
                "title": "Machine Learning for Drug Discovery",
                "abstract": "This review covers machine learning applications in pharmaceutical research and drug development.",
                "authors": "Chen L, Wang M",
                "journal": "Nature Reviews Drug Discovery",
                "year": 2020,
                "citations": 300,
                "doi": "10.1038/s41573-020-0073-5"
            },
            {
                "title": "SARS-CoV-2 variants and vaccine breakthrough infections",
                "abstract": "Analysis of vaccine breakthrough infections caused by different SARS-CoV-2 variants of concern.",
                "authors": "Davis R, Miller S, Wilson T",
                "journal": "Science",
                "year": 2022,
                "citations": 200,
                "doi": "10.1126/science.abm1234"
            },
            {
                "title": "Artificial Intelligence in Healthcare",
                "abstract": "Overview of AI applications in healthcare including diagnostic imaging and clinical decision support.",
                "authors": "Lee H, Kim J",
                "journal": "Nature Medicine",
                "year": 2021,
                "citations": 150,
                "doi": "10.1038/s41591-021-01234-x"
            }
        ]
        
        try:
            # 创建混合检索系统
            hybrid_system = create_hybrid_system(
                embedding_model="specter2",
                enable_colbert=True,
                enable_academic_features=True
            )
            
            # 执行混合检索
            start_time = time.time()
            results = hybrid_system.retrieve_and_rank(query, documents, top_k=4)
            retrieval_time = time.time() - start_time
            
            print(f"✅ 混合检索完成: {len(results)} 个结果")
            print(f"⏱️  检索时间: {retrieval_time:.3f}秒")
            
            # 显示结果
            print("\n🏆 混合检索结果:")
            for i, (orig_idx, score, doc) in enumerate(results, 1):
                print(f"{i}. [{score:.3f}] {doc['title']}")
                print(f"   作者: {doc['authors']}")
                print(f"   期刊: {doc['journal']} ({doc['year']})")
                print(f"   引用: {doc['citations']}")
                print()
            
            # 获取统计信息
            stats = hybrid_system.get_stats()
            print(f"📈 系统统计:")
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for k, v in value.items():
                        print(f"     {k}: {v}")
                else:
                    print(f"   {key}: {value}")
            
        except Exception as e:
            print(f"❌ 混合检索测试失败: {e}")
            import traceback
            traceback.print_exc()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")

async def test_integrated_search():
    """测试集成的搜索系统"""
    print("\n🌟 测试集成搜索系统")
    print("=" * 60)
    
    try:
        from searchtools.async_parallel_search_manager import AsyncParallelSearchManager
        
        # 创建搜索管理器（启用混合检索）
        search_manager = AsyncParallelSearchManager(
            enable_rerank=True,
            enable_hybrid=True
        )
        
        # 测试查询
        test_query = "COVID-19 vaccine"
        
        print(f"🔍 搜索查询: {test_query}")
        print("⚠️  注意: 这将进行真实的网络搜索，可能需要较长时间")
        
        # 执行搜索
        start_time = time.time()
        results, stats = await search_manager.search_all_sources_with_deduplication(test_query)
        search_time = time.time() - start_time
        
        print(f"✅ 搜索完成: {len(results)} 个结果")
        print(f"⏱️  总耗时: {search_time:.2f}秒")
        
        # 显示统计信息
        print(f"\n📊 搜索统计:")
        print(f"   原始结果: {stats.get('total_raw_results', 0)}")
        print(f"   去重后: {len(results)}")
        print(f"   重排序启用: {stats.get('rerank_enabled', False)}")
        print(f"   混合检索启用: {stats.get('hybrid_enabled', False)}")
        
        # 显示前5个结果
        print(f"\n🏆 前5个结果:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result.title}")
            print(f"   作者: {result.authors}")
            print(f"   来源: {result.source}")
            if hasattr(result, 'hybrid_score'):
                print(f"   混合分数: {result.hybrid_score:.3f}")
            elif hasattr(result, 'final_score'):
                print(f"   最终分数: {result.final_score:.3f}")
            print()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("🧪 学术Embedding和混合检索系统测试")
    print("=" * 80)
    
    # 基础组件测试
    test_academic_embeddings()
    test_colbert_reranker()
    test_academic_features()
    test_hybrid_retrieval()
    
    # 集成测试（可选，需要网络连接）
    print("\n" + "=" * 80)
    response = input("是否进行集成搜索测试？(需要网络连接，可能较慢) [y/N]: ")
    if response.lower() in ['y', 'yes']:
        asyncio.run(test_integrated_search())
    
    print("\n🎉 测试完成！")
    print("\n💡 安装建议:")
    print("   pip install transformers torch")
    print("   pip install FlagEmbedding  # 用于BGE-M3")
    print("   pip install colbert-ai     # 用于官方ColBERT")

if __name__ == "__main__":
    main()
