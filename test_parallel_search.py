#!/usr/bin/env python3
"""
Test script to test parallel search manager with Semantic Scholar
"""

import sys
import os
# 添加 src 路径到搜索路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from searchtools import ParallelSearchManager


def test_parallel_search_with_semantic():
    """Test parallel search including Semantic Scholar"""
    print("Testing parallel search with Semantic Scholar...")

    # Initialize search manager
    search_manager = ParallelSearchManager()

    # Check available sources
    print(
        f"Available search sources: {list(search_manager.async_sources.keys())}"
    )

    # Test query
    query = "cancer immunotherapy"
    print(f"Search query: {query}")

    try:
        # Perform search on all sources
        results = search_manager.search_all_sources(query)

        print(
            f"\nSearch completed. Found results from {len(results)} sources:")

        for source_name, source_result in results.items():
            print(f"\n{source_name.upper()}:")
            print(f"  Results count: {source_result.results_count}")
            if source_result.error:
                print(f"  Error: {source_result.error}")
            else:
                print(f"  Success: {len(source_result.results)} papers found")

        # Check if Semantic Scholar worked
        if "semantic_scholar" in results:
            semantic_result = results["semantic_scholar"]
            if semantic_result.error:
                print(f"\n❌ Semantic Scholar failed: {semantic_result.error}")
                return False
            else:
                print(
                    f"\n✅ Semantic Scholar worked successfully: {semantic_result.results_count} results"
                )
                return True
        else:
            print("\n⚠️  Semantic Scholar not found in results")
            return False

    except Exception as e:
        print(f"❌ Search failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = test_parallel_search_with_semantic()
    print(f"\nParallel search test {'PASSED' if success else 'FAILED'}")
