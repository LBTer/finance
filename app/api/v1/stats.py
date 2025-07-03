from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.models.user import User
from app.models.sales_record import SalesRecord, OrderStage
from app.schemas.stats import DashboardStats

router = APIRouter(prefix="/stats", tags=["统计数据"])

@router.get("", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> DashboardStats:
    """
    获取仪表盘统计数据
    
    返回:
        - total_sales: 本月销售总额
        - total_orders: 历史总最终阶段订单数量
        - stage_5_orders: 本月最终阶段订单数量
        - pending_orders: 未完成订单数量
        - 其他字段设为0（保持schema兼容性）
    """
    # 获取当前月份的第一天
    now = datetime.now(timezone.utc)
    first_day = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    
    # 计算下个月的第一天
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    
    # 基础查询条件
    base_query = select(func.count(SalesRecord.id))
    if not current_user.is_superuser:
        # 非管理员只能看到自己的销售记录
        base_query = base_query.where(SalesRecord.user_id == current_user.id)
    
    # 1. 历史总最终阶段订单数量
    total_completed_query = base_query.where(
        SalesRecord.stage == OrderStage.STAGE_5.value
    )
    total_completed_result = await db.execute(total_completed_query)
    total_completed_orders = total_completed_result.scalar() or 0
    
    # 2. 本月最终阶段订单数量
    monthly_completed_query = base_query.where(
        SalesRecord.stage == OrderStage.STAGE_5.value,
        SalesRecord.created_at >= first_day,
        SalesRecord.created_at < next_month
    )
    monthly_completed_result = await db.execute(monthly_completed_query)
    monthly_completed_orders = monthly_completed_result.scalar() or 0
    
    # 3. 未完成订单数量（所有非最终阶段的订单）
    pending_query = base_query.where(
        SalesRecord.stage != OrderStage.STAGE_5.value
    )
    pending_result = await db.execute(pending_query)
    pending_orders = pending_result.scalar() or 0
    
    # 计算本月销售总额（仅最终阶段订单）
    total_sales_query = select(
        func.sum(
            SalesRecord.total_price + 
            SalesRecord.domestic_shipping_fee + 
            SalesRecord.overseas_shipping_fee - 
            SalesRecord.refund_amount - 
            SalesRecord.tax_refund
        ).label("total_sales")
    ).where(
        SalesRecord.created_at >= first_day,
        SalesRecord.created_at < next_month,
        SalesRecord.stage == OrderStage.STAGE_5.value
    )
    
    total_sales_result = await db.execute(total_sales_query)
    total_sales = total_sales_result.scalar() or 0
    
    # 构建返回结果（使用新的DashboardStats结构）
    return DashboardStats(
        total_sales=float(total_sales),
        total_orders=total_completed_orders,
        stage_1_orders=0,
        stage_2_orders=0,
        stage_3_orders=0,
        stage_4_orders=0,
        stage_5_orders=monthly_completed_orders,
        alibaba_orders=0,
        domestic_orders=0,
        exhibition_orders=0,
        pending_logistics_review=0,
        pending_final_review=0,
        completed_orders=pending_orders
    ) 