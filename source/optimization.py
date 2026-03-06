"""
性能优化模块
提供延迟加载、并行导入等功能
"""

import sys
import time
from threading import Thread
from typing import Optional, Callable, Any


class LazyLoader:
    """延迟加载器 - 仅在首次使用时导入模块"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name: str):
        if self._module is None:
            # 首次访问时导入
            self._module = __import__(self.module_name, fromlist=[name])
        return getattr(self._module, name)
    
    def __dir__(self):
        if self._module is None:
            self._module = __import__(self.module_name, fromlist=[''])
        return dir(self._module)


class ParallelImporter:
    """并行导入器 - 在后台线程中导入多个模块"""
    
    def __init__(self):
        self.results = {}
        self.errors = {}
        self.loaded_count = 0
        self.total_count = 0
    
    def import_module(self, module_path: str, alias: Optional[str] = None):
        """添加模块到导入队列"""
        if alias is None:
            alias = module_path.split('.')[-1]
        
        def do_import():
            try:
                start = time.time()
                module = __import__(module_path, fromlist=[''])
                elapsed = time.time() - start
                self.results[alias] = {
                    'module': module,
                    'time': elapsed
                }
                self.loaded_count += 1
            except Exception as e:
                self.errors[alias] = str(e)
        
        thread = Thread(target=do_import, daemon=True)
        thread.start()
        self.total_count += 1
    
    def wait_all(self, timeout: float = 30.0) -> bool:
        """等待所有导入完成"""
        start = time.time()
        while self.loaded_count + len(self.errors) < self.total_count:
            if time.time() - start > timeout:
                return False
            time.sleep(0.01)
        return True
    
    def get_module(self, alias: str):
        """获取已导入的模块"""
        if alias in self.results:
            return self.results[alias]['module']
        raise ImportError(f"Module '{alias}' not loaded: {self.errors.get(alias, 'Unknown error')}")
    
    def print_stats(self):
        """打印导入统计信息"""
        print(f"\n=== 导入统计 ===")
        print(f"总模块数：{self.total_count}")
        print(f"成功：{self.loaded_count}")
        print(f"失败：{len(self.errors)}")
        
        if self.results:
            print(f"\n导入时间:")
            sorted_results = sorted(self.results.items(), key=lambda x: x[1]['time'], reverse=True)
            for name, data in sorted_results:
                print(f"  {name}: {data['time']*1000:.1f}ms")
        
        if self.errors:
            print(f"\n错误:")
            for name, error in self.errors.items():
                print(f"  {name}: {error}")


# 全局优化配置
class OptimizedImports:
    """优化导入管理类"""
    
    _initialized = False
    _importer = None
    
    @classmethod
    def initialize(cls):
        """初始化并行导入"""
        if cls._initialized:
            return
        
        cls._importer = ParallelImporter()
        
        # 预加载常用模块（在后台）
        cls._importer.import_module('numpy', 'np')
        cls._importer.import_module('cv2', 'cv2')
        
        # PySide6 核心模块
        cls._importer.import_module('PySide6.QtWidgets', 'QtWidgets')
        cls._importer.import_module('PySide6.QtCore', 'QtCore')
        cls._importer.import_module('PySide6.QtGui', 'QtGui')
        
        cls._initialized = True
    
    @classmethod
    def wait_loading(cls, timeout: float = 10.0):
        """等待所有模块加载完成"""
        if cls._importer:
            return cls._importer.wait_all(timeout)
        return True
    
    @classmethod
    def get_numpy(cls):
        """获取 numpy 模块"""
        if cls._importer and 'np' in cls._importer.results:
            return cls._importer.get_module('np')
        import numpy as np
        return np
    
    @classmethod
    def get_cv2(cls):
        """获取 cv2 模块"""
        if cls._importer and 'cv2' in cls._importer.results:
            return cls._importer.get_module('cv2')
        import cv2
        return cv2
    
    @classmethod
    def get_qt_widgets(cls):
        """获取 Qt Widgets"""
        if cls._importer and 'QtWidgets' in cls._importer.results:
            return cls._importer.get_module('QtWidgets')
        from PySide6 import QtWidgets
        return QtWidgets


def timed_import(func: Callable) -> Callable:
    """装饰器：统计函数导入时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[导入时间] {func.__name__}: {elapsed*1000:.1f}ms")
        return result
    return wrapper


# 便捷函数
def lazy_import(module_name: str) -> LazyLoader:
    """创建延迟加载器"""
    return LazyLoader(module_name)


def parallel_import(*modules):
    """并行导入多个模块"""
    importer = ParallelImporter()
    for module in modules:
        if isinstance(module, str):
            importer.import_module(module)
        elif isinstance(module, tuple):
            importer.import_module(module[0], module[1])
    
    importer.wait_all()
    return {name: data['module'] for name, data in importer.results.items()}
