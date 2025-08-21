#!/usr/bin/env python3
"""
测试API的rerank功能
"""

import sys
import os
import asyncio
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi.testclient import TestClient
from app import app

def test_search_with_rerank():
    """测试带有rerank功能的搜索API"""
    print("🧪 测试搜索API的Rerank功能")
    print("=" * 60)
    
    client = TestClient(app)
    
    # 测试不同的排序策略
    test_cases = [
        {
            "name": "默认相关性排序",
            "request": {
                "query": "COVID-19 vaccine",
                "max_results": 5,
                "enable_rerank": True,
                "sort_by": "relevance"
            }
        },
        {
            "name": "权威性优先排序",
            "request": {
                "query": "COVID-19 vaccine",
                "max_results": 5,
                "enable_rerank": True,
                "sort_by": "authority"
            }
        },
        {
            "name": "时效性优先排序",
            "request": {
                "query": "COVID-19 vaccine",
                "max_results": 5,
                "enable_rerank": True,
                "sort_by": "recency"
            }
        },
        {
            "name": "引用数排序",
            "request": {
                "query": "COVID-19 vaccine",
                "max_results": 5,
                "enable_rerank": True,
                "sort_by": "citations"
            }
        },
        {
            "name": "禁用Rerank",
            "request": {
                "query": "COVID-19 vaccine",
                "max_results": 5,
                "enable_rerank": False
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 {test_case['name']}:")
        
        try:
            response = client.post("/search", json=test_case["request"])
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"  ✅ 状态: 成功")
                print(f"  📈 结果数量: {data['total_results']}")
                print(f"  🔄 Rerank启用: {data.get('rerank', {}).get('enabled', False)}")
                print(f"  📋 排序策略: {data.get('rerank', {}).get('strategy', 'unknown')}")
                print(f"  ⏱️ 搜索时间: {data.get('performance', {}).get('total_time', 0)}秒")
                
                # 显示前3个结果
                if data['results']:
                    print(f"  📄 前3个结果:")
                    for i, result in enumerate(data['results'][:3], 1):
                        title = result['title'][:50] + "..." if len(result['title']) > 50 else result['title']
                        print(f"    {i}. {title}")
                        print(f"       来源: {result['source']}, 引用: {result.get('citations', 0)}")
                        
                        # 显示rerank评分（如果有）
                        scores = result.get('scores', {})
                        if scores and scores.get('final') is not None:
                            print(f"       最终评分: {scores['final']:.3f}")
                            print(f"       (相关性: {scores.get('relevance', 0):.2f}, "
                                  f"权威性: {scores.get('authority', 0):.2f}, "
                                  f"时效性: {scores.get('recency', 0):.2f}, "
                                  f"质量: {scores.get('quality', 0):.2f})")
                
            else:
                print(f"  ❌ 状态: 失败 ({response.status_code})")
                print(f"  错误: {response.text}")
                
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")


def test_search_comparison():
    """对比启用和禁用rerank的搜索结果"""
    print("\n🔍 对比启用/禁用Rerank的搜索结果")
    print("=" * 60)
    
    client = TestClient(app)
    query = "machine learning drug discovery"
    
    # 禁用rerank的搜索
    print("📋 禁用Rerank的结果:")
    response_no_rerank = client.post("/search", json={
        "query": query,
        "max_results": 5,
        "enable_rerank": False
    })
    
    # 启用rerank的搜索
    print("\n📋 启用Rerank的结果:")
    response_with_rerank = client.post("/search", json={
        "query": query,
        "max_results": 5,
        "enable_rerank": True,
        "sort_by": "relevance"
    })
    
    if response_no_rerank.status_code == 200 and response_with_rerank.status_code == 200:
        data_no_rerank = response_no_rerank.json()
        data_with_rerank = response_with_rerank.json()
        
        print(f"\n对比结果:")
        print(f"  无Rerank - 结果数: {data_no_rerank['total_results']}, 时间: {data_no_rerank.get('performance', {}).get('total_time', 0)}s")
        print(f"  有Rerank - 结果数: {data_with_rerank['total_results']}, 时间: {data_with_rerank.get('performance', {}).get('total_time', 0)}s")
        
        # 对比前3个结果的顺序
        print(f"\n📊 结果顺序对比:")
        for i in range(min(3, len(data_no_rerank['results']), len(data_with_rerank['results']))):
            title_no_rerank = data_no_rerank['results'][i]['title'][:40] + "..."
            title_with_rerank = data_with_rerank['results'][i]['title'][:40] + "..."
            
            print(f"  位置 {i+1}:")
            print(f"    无Rerank: {title_no_rerank}")
            final_score = data_with_rerank['results'][i].get('scores', {}).get('final', 'N/A')
            print(f"    有Rerank: {title_with_rerank} (评分: {final_score})")
            
            if title_no_rerank != title_with_rerank:
                print(f"    🔄 顺序发生变化")
            else:
                print(f"    ✅ 顺序相同")


def main():
    """主测试函数"""
    print("🚀 API Rerank功能测试开始")
    print("=" * 80)
    
    try:
        # 基本API测试
        test_search_with_rerank()
        
        # 对比测试
        test_search_comparison()
        
        print("\n🎉 API测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)


if __name__ == "__main__":
    main()
