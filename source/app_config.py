"""
应用配置管理模块
用于保存和加载用户设置
"""

import json
import os
from pathlib import Path


class AppConfig:
    """应用程序配置类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'language': 'zh_CN',  # 默认语言
        'window': {
            'width': 1200,
            'height': 800,
            'x': None,
            'y': None,
        },
        'serial': {
            'port': 'COM6',
            'baudrate': 115200,
            'timeout': 1.0,
        },
        'camera': {
            'index': 0,
            'width': 1920,
            'height': 1080,
        },
        'stage': {
            'step_size_idx': 1,
            'acceleration': 30.0,
        },
    }
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 递归更新配置
                    self._deep_update(self.config, saved_config)
                print(f"[Config] 已加载配置文件：{self.config_file}")
            except Exception as e:
                print(f"[Config] 加载配置失败：{e}，使用默认配置")
        else:
            print(f"[Config] 配置文件不存在，将创建：{self.config_file}")
    
    def save(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            config_dir = Path(self.config_file).parent
            if str(config_dir) != '.' and not config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[Config] 配置已保存：{self.config_file}")
        except Exception as e:
            print(f"[Config] 保存配置失败：{e}")
    
    def _deep_update(self, base_dict, update_dict):
        """递归更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key_path, default=None):
        """获取配置值
        
        Args:
            key_path: 点分隔的键路径，如 'window.width'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path, value):
        """设置配置值
        
        Args:
            key_path: 点分隔的键路径，如 'window.width'
            value: 配置值
        """
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    # 便捷方法
    @property
    def language(self):
        return self.config['language']
    
    @language.setter
    def language(self, value):
        self.config['language'] = value
    
    @property
    def serial_port(self):
        return self.config['serial']['port']
    
    @serial_port.setter
    def serial_port(self, value):
        self.config['serial']['port'] = value
    
    @property
    def serial_baudrate(self):
        return self.config['serial']['baudrate']
    
    @property
    def window_size(self):
        return (self.config['window']['width'], self.config['window']['height'])
    
    def update_serial_config(self, port, baudrate):
        """更新串口配置"""
        self.config['serial']['port'] = port
        self.config['serial']['baudrate'] = baudrate
    
    def update_window_config(self, width, height, x=None, y=None):
        """更新窗口配置"""
        self.config['window']['width'] = width
        self.config['window']['height'] = height
        if x is not None:
            self.config['window']['x'] = x
        if y is not None:
            self.config['window']['y'] = y


# 全局配置实例
_global_config = None


def get_config():
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = AppConfig()
    return _global_config


def save_config():
    """保存全局配置"""
    if _global_config:
        _global_config.save()
