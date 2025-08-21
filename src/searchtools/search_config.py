"""
Unified configuration for search tools.
Provides centralized configuration for all search APIs.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv()
except ImportError:
    print("python-dotenv isn't installed, .env won't be loaded in runtime.")


class SearchAPIConfig(BaseModel):
    """Configuration for individual search APIs"""

    # Enable/disable flag
    enabled: bool = Field(default=True,
                          description="Whether this search source is enabled")

    # HTTP settings
    timeout: float = Field(default=30.0,
                           description="Request timeout in seconds")
    connect_timeout: float = Field(default=5.0,
                                   description="Connection timeout in seconds")
    max_retries: int = Field(default=3,
                             description="Maximum number of retries")

    # Results settings
    max_results: int = Field(default=10,
                             description="Maximum results per search")
    page_size: int = Field(default=10,
                           description="Results per page for paginated APIs")

    # Preprint filtering settings (for BioRxiv/MedRxiv)
    use_advanced_filter: bool = Field(default=True,
                                     description="Use advanced filtering for preprints")
    filter_days_back: int = Field(default=30,
                                 description="Filter papers from last N days")
    min_relevance_score: float = Field(default=0.5,
                                      description="Minimum relevance score for filtering")

    # Rate limiting
    rate_limit_delay: float = Field(
        default=0.2, description="Delay between requests in seconds")

    # API specific settings
    user_agent: str = Field(
        default="MedDeepResearch/1.0 (Medical Literature Search Tool)",
        description="User agent string",
    )


class SearchToolsConfig(BaseModel):
    """Global configuration for all search tools"""

    # Global settings
    max_concurrent_requests: int = Field(
        default=5, description="Maximum concurrent API requests")
    enable_caching: bool = Field(default=True,
                                 description="Enable result caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    # Logging
    log_requests: bool = Field(default=True,
                               description="Log all API requests")
    log_responses: bool = Field(
        default=False, description="Log API responses (can be verbose)")

    # API Keys
    semantic_scholar_api_key: Optional[str] = Field(
        default=None, description="Semantic Scholar API key")

    # Individual API configurations
    europe_pmc: SearchAPIConfig = Field(
        default_factory=lambda: SearchAPIConfig(
            enabled=True,  # Keep enabled - fast and reliable
            max_results=10,
            timeout=30.0,
        ))

    semantic_scholar: SearchAPIConfig = Field(
        default_factory=lambda: SearchAPIConfig(
            enabled=True, max_results=10, timeout=10.0))

    biorxiv: SearchAPIConfig = Field(default_factory=lambda: SearchAPIConfig(
        enabled=True,
        max_results=50,  # BioRxiv returns many results
        timeout=30.0,
    ))

    medrxiv: SearchAPIConfig = Field(default_factory=lambda: SearchAPIConfig(
        enabled=True,
        max_results=50,  # MedRxiv returns many results
        timeout=30.0,
    ))

    clinical_trials: SearchAPIConfig = Field(
        default_factory=lambda: SearchAPIConfig(
            enabled=True,  # 重新启用，使用改进的稳定搜索策略
            max_results=10,  # 适中的结果数量
            timeout=30.0,  # 合理的超时时间
            max_retries=2,  # 适度的重试次数
            rate_limit_delay=1.0,  # 保守的速率限制
        ))

    pubmed: SearchAPIConfig = Field(default_factory=lambda: SearchAPIConfig(
        enabled=True,  # 重新启用，使用Europe PMC作为稳定后备
        max_results=5,  # 保持较小的结果数量
        timeout=30.0,  # 合理的超时时间
        max_retries=2,  # 适度的重试次数
        rate_limit_delay=0.5,  # NCBI速率限制延迟
    ))

    @classmethod
    def from_env(cls) -> "SearchToolsConfig":
        """Create config from environment variables"""
        config = cls()

        # Override with environment variables if they exist
        # Example: SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS=10
        if max_concurrent := os.getenv("SEARCH_TOOLS_MAX_CONCURRENT_REQUESTS"):
            config.max_concurrent_requests = int(max_concurrent)

        # API Keys
        if semantic_api_key := os.getenv("SEMANTIC_SCHOLAR_API_KEY"):
            config.semantic_scholar_api_key = semantic_api_key

        # Per-API overrides
        # Example: SEARCH_TOOLS_PUBMED_MAX_RESULTS=20
        for api_name in [
                "europe_pmc",
                "semantic_scholar",
                "biorxiv",
                "medrxiv",
                "clinical_trials",
                "pubmed",
        ]:
            api_config = getattr(config, api_name)

            # Enabled flag
            if enabled := os.getenv(
                    f"SEARCH_TOOLS_{api_name.upper()}_ENABLED"):
                api_config.enabled = enabled.lower() == "true"

            # Max results
            if max_results := os.getenv(
                    f"SEARCH_TOOLS_{api_name.upper()}_MAX_RESULTS"):
                api_config.max_results = int(max_results)

            # Timeout
            if timeout := os.getenv(
                    f"SEARCH_TOOLS_{api_name.upper()}_TIMEOUT"):
                api_config.timeout = float(timeout)

        return config

    def get_api_config(self, api_name: str) -> SearchAPIConfig:
        """Get configuration for a specific API"""
        return getattr(self,
                       api_name.lower().replace("-", "_"), SearchAPIConfig())


# Global configuration instance
search_config = SearchToolsConfig.from_env()


# Convenience functions
def get_config() -> SearchToolsConfig:
    """Get the global search tools configuration"""
    return search_config


def get_api_config(api_name: str) -> SearchAPIConfig:
    """Get configuration for a specific API"""
    return search_config.get_api_config(api_name)
