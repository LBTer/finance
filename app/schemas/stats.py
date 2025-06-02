from pydantic import BaseModel
from typing import Optional

class DashboardStats(BaseModel):
    """仪表盘统计数据模式"""
    total_sales: float
    approved_orders: int
    pending_orders: int
    rejected_orders: int 