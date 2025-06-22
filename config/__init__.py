"""
配置管理包

提供统一的配置管理功能，包括：
- 配置加载和验证
- 环境变量管理
- 配置工具和示例
"""

from .config_manager import ConfigManager, config

__all__ = ['ConfigManager', 'config']
__version__ = '1.0.0' 