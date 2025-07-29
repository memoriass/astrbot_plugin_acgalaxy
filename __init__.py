"""
次元星辰 - AstrBot 插件

基于 NoneBot 插件 nonebot-plugin-ACGalaxy 开发的 AstrBot 版本
简单高效的漫展信息展示插件，收集展示漫展信息，支持检索、排序、获取定位信息
"""

__version__ = "1.0.0"
__author__ = "Assistant"
__description__ = "简单高效的漫展信息展示插件，收集展示漫展信息，支持检索、排序、获取定位信息"

from .main import ACGalaxyPlugin

__all__ = ["ACGalaxyPlugin"]
