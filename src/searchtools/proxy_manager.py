"""
代理管理器 - 用于解决IP限制问题
"""

import os
import random
import logging
from typing import List, Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    代理管理器，用于轮换代理IP以避免403错误
    """
    
    def __init__(self):
        self.proxy_list = self._load_proxy_list()
        self.current_proxy_index = 0
        self.failed_proxies = set()
    
    def _load_proxy_list(self) -> List[str]:
        """
        从环境变量或配置文件加载代理列表
        """
        proxy_list = []
        
        # 从环境变量读取代理
        proxy_env = os.getenv("SEARCH_TOOLS_PROXY_LIST")
        if proxy_env:
            proxy_list = [p.strip() for p in proxy_env.split(",") if p.strip()]
        
        # 从配置文件读取代理（如果存在）
        try:
            proxy_file = os.path.join(os.path.dirname(__file__), "proxies.txt")
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    file_proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    proxy_list.extend(file_proxies)
        except Exception as e:
            logger.warning(f"[ProxyManager] Failed to load proxy file: {e}")
        
        # 添加一些免费的公共代理（仅用于测试）
        if not proxy_list:
            # 注意：这些是示例代理，实际使用时应该使用可靠的代理服务
            test_proxies = [
                "http://proxy1.example.com:8080",
                "http://proxy2.example.com:8080",
                # 实际部署时应该移除这些示例代理
            ]
            # proxy_list.extend(test_proxies)  # 暂时注释掉，避免使用无效代理
        
        if proxy_list:
            logger.info(f"[ProxyManager] Loaded {len(proxy_list)} proxies")
        else:
            logger.info("[ProxyManager] No proxies configured")
        
        return proxy_list
    
    def get_next_proxy(self) -> Optional[str]:
        """
        获取下一个可用的代理
        """
        if not self.proxy_list:
            return None
        
        # 过滤掉失败的代理
        available_proxies = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not available_proxies:
            # 如果所有代理都失败了，重置失败列表
            logger.warning("[ProxyManager] All proxies failed, resetting failed list")
            self.failed_proxies.clear()
            available_proxies = self.proxy_list
        
        # 轮换代理
        proxy = available_proxies[self.current_proxy_index % len(available_proxies)]
        self.current_proxy_index += 1
        
        return proxy
    
    def mark_proxy_failed(self, proxy: str):
        """
        标记代理为失败
        """
        self.failed_proxies.add(proxy)
        logger.warning(f"[ProxyManager] Marked proxy as failed: {proxy}")
    
    def get_random_proxy(self) -> Optional[str]:
        """
        获取随机代理
        """
        if not self.proxy_list:
            return None
        
        available_proxies = [p for p in self.proxy_list if p not in self.failed_proxies]
        
        if not available_proxies:
            self.failed_proxies.clear()
            available_proxies = self.proxy_list
        
        return random.choice(available_proxies)


class AntiBlockHTTPClient:
    """
    防封锁HTTP客户端，集成代理轮换和请求头轮换
    """
    
    def __init__(self, use_proxy: bool = False, timeout: float = 30.0):
        self.use_proxy = use_proxy
        self.timeout = timeout
        self.proxy_manager = ProxyManager() if use_proxy else None
        self.session_count = 0
        
        # 多种User-Agent轮换
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
        ]
    
    def _get_headers(self) -> Dict[str, str]:
        """
        获取轮换的请求头
        """
        user_agent = random.choice(self.user_agents)
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # 随机添加一些可选头部
        if random.random() > 0.5:
            headers["Referer"] = "https://www.google.com/"
        
        return headers
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """
        发送GET请求，自动处理代理和请求头轮换
        """
        headers = self._get_headers()
        
        # 合并用户提供的headers
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        # 设置超时
        kwargs.setdefault('timeout', self.timeout)
        
        # 如果启用代理，尝试使用代理
        if self.use_proxy and self.proxy_manager:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                kwargs['proxies'] = {"http://": proxy, "https://": proxy}
                logger.debug(f"[AntiBlockHTTPClient] Using proxy: {proxy}")
        
        try:
            # 增加会话计数
            self.session_count += 1
            
            # 每隔一定次数请求后，添加随机延迟
            if self.session_count % 5 == 0:
                import time
                delay = random.uniform(1, 3)
                logger.debug(f"[AntiBlockHTTPClient] Adding random delay: {delay:.2f}s")
                time.sleep(delay)
            
            response = httpx.get(url, params=params, **kwargs)
            
            # 如果成功，返回响应
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                logger.info(f"[AntiBlockHTTPClient] 403 (expected, will use fallback): {url}")
                # 如果使用代理且遇到403，标记当前代理为失败
                if self.use_proxy and self.proxy_manager and 'proxies' in kwargs:
                    current_proxy = list(kwargs['proxies'].values())[0]
                    self.proxy_manager.mark_proxy_failed(current_proxy)
            
            return response
            
        except Exception as e:
            logger.error(f"[AntiBlockHTTPClient] Request failed: {e}")
            # 如果使用代理且请求失败，标记代理为失败
            if self.use_proxy and self.proxy_manager and 'proxies' in kwargs:
                current_proxy = list(kwargs['proxies'].values())[0]
                self.proxy_manager.mark_proxy_failed(current_proxy)
            raise


# 全局实例
_anti_block_client = None

def get_anti_block_client(use_proxy: bool = False) -> AntiBlockHTTPClient:
    """
    获取防封锁HTTP客户端的全局实例
    """
    global _anti_block_client
    if _anti_block_client is None:
        # 检查环境变量是否启用代理
        use_proxy = use_proxy or os.getenv("SEARCH_TOOLS_USE_PROXY", "false").lower() == "true"
        _anti_block_client = AntiBlockHTTPClient(use_proxy=use_proxy)
    return _anti_block_client
