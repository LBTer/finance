from pydantic import BaseModel
from typing import Optional

class DashboardStats(BaseModel):
    """仪表盘统计数据模式"""
    total_sales: float
    total_orders: int
    
    # 按阶段统计订单数量
    stage_1_orders: int  # 第一阶段：初次创建，信息补充阶段
    stage_2_orders: int  # 第二阶段：待后勤审核
    stage_3_orders: int  # 第三阶段：后勤审核通过，信息补充阶段
    stage_4_orders: int  # 第四阶段：待最终审核
    stage_5_orders: int  # 第五阶段：超级/高级用户审核通过
    
    # 按订单类型统计
    alibaba_orders: int     # 阿里订单数量
    domestic_orders: int    # 国内订单数量
    exhibition_orders: int  # 展会订单数量
    
    # 审核统计
    pending_logistics_review: int  # 待后勤审核数量（第二阶段）
    pending_final_review: int      # 待最终审核数量（第四阶段）
    completed_orders: int          # 已完成订单数量（第五阶段）

class UserStats(BaseModel):
    """用户统计数据模式"""
    total_users: int
    active_users: int
    
    # 按角色统计
    normal_users: int
    senior_users: int
    admin_users: int
    
    # 按职能统计（仅普通用户）
    sales_users: int
    logistics_users: int
    sales_logistics_users: int

class OrderTypeStats(BaseModel):
    """订单类型统计模式"""
    order_type: str
    count: int
    total_amount: float
    avg_amount: float

class StageStats(BaseModel):
    """阶段统计模式"""
    stage: str
    count: int
    percentage: float 