"""
负责放定义的常量
"""

from enum import Enum

class CustomerSource(str, Enum):
    ALI = "阿里"
    EXHIBITION = "展会"
    GROUND = "地推"
    SELF_DEVELOPMENT = "自主开发"

class ProductCategory(str, Enum):
    FORGE_WHEEL = "锻造轮"
    CAST_WHEEL = "铸造轮"
    