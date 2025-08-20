#!/usr/bin/env python3
"""
Test script to test Semantic Scholar search functionality
"""

from src.searchtools import semantic_scholar_search


def test_semantic_scholar_search():
    """Test Semantic Scholar search"""
    print("Testing Semantic Scholar search...")

    # Test query
    query = "cancer immunotherapy"
    print(f"Search query: {query}")

    try:
        # Perform search using invoke method for tool
        results = semantic_scholar_search.invoke({"query": query, "limit": 3})
        print("\nSearch results:")
        print("=" * 50)
        print(results)
        print("=" * 50)

        if "Error" in results:
            print("❌ Search failed with error")
            return False
        elif "No papers found" in results:
            print("⚠️  No papers found (this might be normal)")
            return True
        else:
            print("✅ Search completed successfully")
            return True

    except Exception as e:
        print(f"❌ Search failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = test_semantic_scholar_search()
    print(f"\nSearch test {'PASSED' if success else 'FAILED'}")
