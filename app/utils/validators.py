import re
from typing import Optional
from datetime import datetime
from pydantic import validator


class Validators:
    """自定义验证器集合"""
    
    @staticmethod
    def validate_order_number(value: str) -> str:
        """
        验证订单号格式
        格式要求：SR + 年月日 + 4位序号，例如：SR2024031700001
        """
        pattern = r'^SR\d{8}\d{5}$'
        if not re.match(pattern, value):
            raise ValueError("订单号格式不正确，应为'SR' + 年月日 + 5位序号")
        return value
    
    @staticmethod
    def validate_amount(value: float) -> float:
        """
        验证金额是否合法
        """
        if value < 0:
            raise ValueError("金额不能为负数")
        return round(value, 2)
    
    @staticmethod
    def validate_quantity(value: int) -> int:
        """
        验证数量是否合法
        """
        if value <= 0:
            raise ValueError("数量必须大于0")
        return value
    
    @staticmethod
    def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> bool:
        """
        验证日期范围是否合法
        """
        if start_date and end_date and start_date > end_date:
            raise ValueError("开始日期不能大于结束日期")
        return True
    
    @staticmethod
    def validate_phone_number(value: str) -> str:
        """
        验证手机号格式
        """
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, value):
            raise ValueError("手机号格式不正确")
        return value
    
    @staticmethod
    def validate_email(value: str) -> str:
        """
        验证邮箱格式
        """
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(pattern, value):
            raise ValueError("邮箱格式不正确")
        return value 