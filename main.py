from dotenv import load_dotenv
load_dotenv()

import sys
import os
# 添加 src 路径到搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
#!/usr/bin/env python3
"""
SearchTools 主程序
提供异步搜索和去重功能，适合 FastAPI 后端调用
"""

import asyncio
import json

from searchtools.async_parallel_search_manager import \
    AsyncParallelSearchManager 
from searchtools.models import SearchResult


async def search_and_deduplicate(query: str = "diabetes"):
    """
    执行异步搜索和去重

    Args:
        query (str): 搜索查询词，默认使用 "diabetes"

    Returns:
        tuple: (去重后的结果列表, 重复统计信息)
    """
    # 创建搜索管理器
    search_manager = AsyncParallelSearchManager()

    # 执行异步搜索
    results = await search_manager._async_search_all_sources(query)

    # 收集所有结果
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

    # 执行去重
    deduplicated_results, duplicate_stats = search_manager.deduplicate_results(
        all_results)

    return deduplicated_results, duplicate_stats


async def main():
    """主函数 - 测试搜索和去重功能"""
    print("🔍 开始搜索: diabetes")

    # 执行搜索和去重
    results, stats = await search_and_deduplicate("breast cancer")

    # 输出结果统计
    print(f"📊 搜索结果: {len(results)} 个去重后的结果")
    print(f"🔄 重复统计: {stats}")

    # 输出去重后的原始结果（适合 FastAPI 返回）
    print("\n📋 去重后的结果:")
    for result in results:
        print(
            json.dumps(
                {
                    "title": result.title,
                    "authors": result.authors,
                    "journal": result.journal,
                    "year": result.year,
                    "citations": result.citations,
                    "doi": result.doi,
                    "pmid": result.pmid,
                    "pmcid": result.pmcid,
                    "published_date": result.published_date,
                    "url": result.url,
                    "abstract": result.abstract,
                    "source": result.source,
                },
                ensure_ascii=False,
                indent=2,
            ))


if __name__ == "__main__":
    asyncio.run(main())
