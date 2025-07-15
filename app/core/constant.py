"""
负责放定义的常量
"""

from enum import Enum

class CustomerSource(str, Enum):
    ALI = "阿里"
    EXHIBITION = "展会"
    GROUND = "地推"
    SELF_DEVELOPMENT = "自主开发"
    