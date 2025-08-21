"""
日志配置模块 - 提供清洁的日志输出
"""

import logging
import sys
from typing import Optional


class CleanFormatter(logging.Formatter):
    """
    清洁的日志格式化器，减少冗余信息
    """
    
    def __init__(self):
        # 简化的日志格式
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def format(self, record):
        # 过滤掉一些冗余的日志信息
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            
            # 简化HTTP请求日志
            if 'HTTP Request:' in msg and '200 OK' in msg:
                # 将成功的HTTP请求改为DEBUG级别
                record.levelno = logging.DEBUG
                record.levelname = 'DEBUG'
            
            # 简化403错误信息
            if '403 Forbidden' in msg and 'expected' in msg.lower():
                record.levelno = logging.DEBUG
                record.levelname = 'DEBUG'
        
        return super().format(record)


def setup_clean_logging(level: str = "INFO", quiet_mode: bool = False):
    """
    设置清洁的日志配置
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        quiet_mode: 安静模式，只显示WARNING及以上级别
    """
    # 设置日志级别
    if quiet_mode:
        log_level = logging.WARNING
    else:
        log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(CleanFormatter())
    
    # 添加处理器到根日志器
    root_logger.addHandler(console_handler)
    
    # 设置特定模块的日志级别
    _configure_module_loggers(quiet_mode)


def _configure_module_loggers(quiet_mode: bool = False):
    """
    配置特定模块的日志级别
    """
    # HTTP相关的日志设置为WARNING级别，减少噪音
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    if quiet_mode:
        # 安静模式下，将我们自己的模块也设置为WARNING
        logging.getLogger('searchtools').setLevel(logging.WARNING)
    else:
        # 正常模式下，保持INFO级别
        logging.getLogger('searchtools').setLevel(logging.INFO)
        
        # 但是将一些特定的子模块设置为WARNING，减少噪音
        logging.getLogger('searchtools.http_client').setLevel(logging.WARNING)
        logging.getLogger('searchtools.async_http_client').setLevel(logging.WARNING)
        logging.getLogger('searchtools.proxy_manager').setLevel(logging.WARNING)


def setup_test_logging():
    """
    设置测试专用的日志配置 - 更清洁的输出
    """
    setup_clean_logging(level="INFO", quiet_mode=False)
    
    # 进一步简化测试输出
    logging.getLogger('httpx').setLevel(logging.ERROR)
    logging.getLogger('searchtools.http_client').setLevel(logging.ERROR)
    logging.getLogger('searchtools.async_http_client').setLevel(logging.ERROR)
    logging.getLogger('searchtools.proxy_manager').setLevel(logging.ERROR)


def setup_production_logging():
    """
    设置生产环境的日志配置 - 只显示重要信息
    """
    setup_clean_logging(level="WARNING", quiet_mode=True)


def setup_debug_logging():
    """
    设置调试模式的日志配置 - 显示所有信息
    """
    setup_clean_logging(level="DEBUG", quiet_mode=False)
    
    # 调试模式下显示HTTP请求
    logging.getLogger('httpx').setLevel(logging.INFO)


# 默认设置
def setup_default_logging():
    """
    设置默认的日志配置
    """
    setup_clean_logging(level="INFO", quiet_mode=False)


# 自动设置
if __name__ != "__main__":
    # 当模块被导入时，自动设置默认日志配置
    setup_default_logging()
