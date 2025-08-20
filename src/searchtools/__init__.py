"""
Medical research search tools package.

This package provides unified search capabilities across multiple medical and biomedical databases.
"""

# Core components
from .http_client import SearchHTTPClient
from .search_config import (
    SearchToolsConfig,
    SearchAPIConfig,
    get_config,
    get_api_config,
)

# 使用异步版本的 ParallelSearchManager
try:
    from .async_parallel_search_manager import (
        AsyncParallelSearchManager as ParallelSearchManager, )

    print("[Tools] Using async version of ParallelSearchManager")
except ImportError:
    # 如果异步版本导入失败，回退到原版本
    from .parallel_search_manager import ParallelSearchManager

    print("[Tools] Using original version of ParallelSearchManager")

# Search tools
from .search_tools_decorator import (
    europe_pmc_pubmed_search,
    biorxiv_search,
    medrxiv_search,
    clinical_trials_search,
    semantic_scholar_search,
    pubmed_search,
)

__all__ = [
    # Core components
    "SearchHTTPClient",
    "SearchToolsConfig",
    "SearchAPIConfig",
    "get_config",
    "get_api_config",
    "ParallelSearchManager",
    # Search tools
    "europe_pmc_pubmed_search",
    "biorxiv_search",
    "medrxiv_search",
    "clinical_trials_search",
    "semantic_scholar_search",
    "pubmed_search",
]
