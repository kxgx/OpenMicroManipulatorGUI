"""
日志管理器模块
提供完整的日志记录功能，支持多级别日志和日志回调
"""

import logging
import sys
import time
from datetime import datetime
from typing import Optional, Callable
import threading


class LogLevel:
    """日志级别定义"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogManager:
    """
    日志管理器类
    提供统一的日志记录接口，支持控制台输出和回调函数
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger('OpenMicroManipulator')
        self.logger.setLevel(logging.DEBUG)  # 设置最低级别为 DEBUG
        
        # 清除已有的 handlers
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上级别
        
        # 日志格式
        formatter = logging.Formatter(
            '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 日志回调函数列表
        self._callbacks = []
        self._callback_lock = threading.Lock()
    
    def add_callback(self, callback: Callable[[str, str, str], None]):
        """
        添加日志回调函数
        
        Args:
            callback: 回调函数，接收 (timestamp, level, message) 三个参数
        """
        with self._callback_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, str, str], None]):
        """移除日志回调函数"""
        with self._callback_lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _notify_callbacks(self, timestamp: str, level: str, message: str):
        """通知所有回调函数"""
        with self._callback_lock:
            for callback in self._callbacks:
                try:
                    callback(timestamp, level, message)
                except Exception as e:
                    print(f"[LogManager] 回调函数执行失败：{e}")
    
    def debug(self, message: str):
        """记录 DEBUG 级别日志"""
        self.logger.debug(message)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self._notify_callbacks(timestamp, 'DEBUG', message)
    
    def info(self, message: str):
        """记录 INFO 级别日志"""
        self.logger.info(message)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self._notify_callbacks(timestamp, 'INFO', message)
    
    def warning(self, message: str):
        """记录 WARNING 级别日志"""
        self.logger.warning(message)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self._notify_callbacks(timestamp, 'WARNING', message)
    
    def error(self, message: str):
        """记录 ERROR 级别日志"""
        self.logger.error(message)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self._notify_callbacks(timestamp, 'ERROR', message)
    
    def critical(self, message: str):
        """记录 CRITICAL 级别日志"""
        self.logger.critical(message)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self._notify_callbacks(timestamp, 'CRITICAL', message)
    
    def comm(self, message: str, direction: str = 'TX'):
        """
        记录通信日志
        
        Args:
            message: 通信消息
            direction: 方向，'TX' 发送 或 'RX' 接收
        """
        log_message = f"{direction}: {message}"
        self.logger.debug(log_message)
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        self._notify_callbacks(timestamp, 'COMM', log_message)
    
    def set_level(self, level: int):
        """
        设置日志级别
        
        Args:
            level: 日志级别 (logging.DEBUG, logging.INFO, etc.)
        """
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)


# 全局日志管理器实例
log_manager = LogManager()


# 便捷的日志函数
def debug(message: str):
    """记录 DEBUG 日志"""
    log_manager.debug(message)


def info(message: str):
    """记录 INFO 日志"""
    log_manager.info(message)


def warning(message: str):
    """记录 WARNING 日志"""
    log_manager.warning(message)


def error(message: str):
    """记录 ERROR 日志"""
    log_manager.error(message)


def critical(message: str):
    """记录 CRITICAL 日志"""
    log_manager.critical(message)


def comm(message: str, direction: str = 'TX'):
    """记录通信日志"""
    log_manager.comm(message, direction)


def add_callback(callback: Callable[[str, str, str], None]):
    """添加日志回调"""
    log_manager.add_callback(callback)


def remove_callback(callback: Callable[[str, str, str], None]):
    """移除日志回调"""
    log_manager.remove_callback(callback)
