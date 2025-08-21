"""
Unified HTTP client for all search tools.
Provides both sync and async interfaces with consistent configuration.
"""

import httpx
import os
from typing import Optional, Dict, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class SearchHTTPClient:
    """统一的 HTTP 客户端，支持同步和异步请求"""

    def __init__(
        self,
        timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        user_agent: Optional[str] = None,
    ):
        """
        初始化 HTTP 客户端

        Args:
            timeout: 请求超时时间（秒）
            connect_timeout: 连接超时时间（秒）
            max_retries: 最大重试次数
            headers: 默认请求头
            user_agent: User-Agent 字符串
        """
        # Import config here to avoid circular imports
        from .search_config import get_config

        get_config()

        # Use provided values or defaults from config
        timeout = timeout or 30.0
        connect_timeout = connect_timeout or 5.0
        max_retries = max_retries or 3

        self.timeout = httpx.Timeout(connect=connect_timeout,
                                     read=timeout,
                                     write=5.0,
                                     pool=5.0)

        self.limits = httpx.Limits(max_connections=100,
                                   max_keepalive_connections=20,
                                   keepalive_expiry=30.0)

        self.headers = headers or {}
        if user_agent:
            self.headers["User-Agent"] = user_agent
        elif "User-Agent" not in self.headers:
            self.headers["User-Agent"] = (
                "MedDeepResearch/1.0 (Medical Literature Search Tool)")

        self.max_retries = max_retries

        # Transport with retry logic
        self.transport = httpx.HTTPTransport(retries=max_retries)

    def get_sync_client(self) -> httpx.Client:
        """获取同步客户端"""
        return httpx.Client(
            timeout=self.timeout,
            limits=self.limits,
            headers=self.headers,
            transport=self.transport,
            follow_redirects=True,
        )

    def get_async_client(self) -> httpx.AsyncClient:
        """获取异步客户端"""
        return httpx.AsyncClient(
            timeout=self.timeout,
            limits=self.limits,
            headers=self.headers,
            transport=httpx.AsyncHTTPTransport(retries=self.max_retries),
            follow_redirects=True,
        )

    def get(self,
            url: str,
            params: Optional[Dict[str, Any]] = None,
            **kwargs) -> httpx.Response:
        """
        同步 GET 请求

        Args:
            url: 请求URL
            params: 查询参数
            **kwargs: 其他 httpx 参数

        Returns:
            httpx.Response 对象
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
            reraise=True,
        )
        def _make_request():
            with self.get_sync_client() as client:
                response = client.get(url, params=params, **kwargs)
                # 4xx 错误不重试
                if 400 <= response.status_code < 500:
                    logger.error(
                        f"HTTP error occurred: {response.status_code} - {response.text}"
                    )
                    response.raise_for_status()
                response.raise_for_status()
                return response

        return _make_request()

    def post(self,
             url: str,
             json: Optional[Dict[str, Any]] = None,
             **kwargs) -> httpx.Response:
        """
        同步 POST 请求

        Args:
            url: 请求URL
            json: JSON数据
            **kwargs: 其他 httpx 参数

        Returns:
            httpx.Response 对象
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
            reraise=True,
        )
        def _make_request():
            with self.get_sync_client() as client:
                response = client.post(url, json=json, **kwargs)
                # 4xx 错误不重试
                if 400 <= response.status_code < 500:
                    logger.error(
                        f"HTTP error occurred: {response.status_code} - {response.text}"
                    )
                    response.raise_for_status()
                response.raise_for_status()
                return response

        return _make_request()


# 默认客户端实例
default_client = SearchHTTPClient()
