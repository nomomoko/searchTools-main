"""
Async HTTP client for search operations.
Provides async interface with connection pooling, timeout control, and retry logic.
"""

import logging
from typing import Any, Dict, Optional, Union

import httpx
from httpx import AsyncClient, Response
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class AsyncSearchHTTPClient:
    """
    异步 HTTP 客户端，用于搜索操作。
    支持连接池复用、超时控制、重试逻辑等。
    """

    def __init__(
        self,
        timeout: Optional[float] = 30.0,
        connect_timeout: Optional[float] = 10.0,
        max_retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
        limits: Optional[httpx.Limits] = None,
    ):
        """
        初始化异步 HTTP 客户端。

        Args:
            timeout: 请求总超时时间（秒）
            connect_timeout: 连接超时时间（秒）
            max_retries: 最大重试次数
            headers: 默认请求头
            limits: 连接池限制
        """
        self.timeout = httpx.Timeout(
            timeout=timeout,  # 设置默认超时
            connect=connect_timeout,
            read=timeout,
            write=timeout,
            pool=timeout,
        )
        self.max_retries = max_retries
        self.headers = headers or {}

        # 连接池限制
        self.limits = limits or httpx.Limits(max_connections=100,
                                             max_keepalive_connections=20,
                                             keepalive_expiry=30.0)

        # 客户端实例
        self._client: Optional[AsyncClient] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            limits=self.limits,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        """
        发送异步 GET 请求。

        Args:
            url: 请求 URL
            params: 查询参数
            headers: 请求头（会与默认请求头合并）
            **kwargs: 其他 httpx 支持的参数

        Returns:
            httpx.Response 对象

        Raises:
            httpx.HTTPError: HTTP 请求错误
            asyncio.TimeoutError: 请求超时
        """
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use async context manager.")

        # 合并请求头
        request_headers = {**self.headers, **(headers or {})}

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
            reraise=True,
        )
        async def _make_request():
            response = await self._client.get(url,
                                              params=params,
                                              headers=request_headers,
                                              **kwargs)
            # 4xx 错误不重试
            if 400 <= response.status_code < 500:
                logger.error(
                    f"Client error {response.status_code} for URL: {url}"
                )
                response.raise_for_status()
            response.raise_for_status()
            return response

        return await _make_request()

    async def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Response:
        """
        发送异步 POST 请求。

        Args:
            url: 请求 URL
            data: 表单数据
            json: JSON 数据
            headers: 请求头
            **kwargs: 其他 httpx 支持的参数

        Returns:
            httpx.Response 对象
        """
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use async context manager.")

        request_headers = {**self.headers, **(headers or {})}

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
            reraise=True,
        )
        async def _make_request():
            response = await self._client.post(url,
                                               data=data,
                                               json=json,
                                               headers=request_headers,
                                               **kwargs)
            # 4xx 错误不重试
            if 400 <= response.status_code < 500:
                logger.error(
                    f"Client error {response.status_code} for URL: {url}"
                )
                response.raise_for_status()
            response.raise_for_status()
            return response

        return await _make_request()

    def is_healthy(self) -> bool:
        """检查客户端是否健康"""
        return self._client is not None and not self._client.is_closed
