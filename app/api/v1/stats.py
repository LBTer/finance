from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.models.user import User
from app.models.sales_record import SalesRecord, OrderStage, OrderSource
from app.models.fees import ShippingFees
from app.models.procurement import Procurement
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
        - total_sales: 本月销售总额（美元）
        - total_orders: 历史总订单数量
        - stage_X_orders: 各阶段订单数量
        - 订单来源统计
        - 审核统计
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
        # 非超级管理员只能看到自己的销售记录
        base_query = base_query.where(SalesRecord.user_id == current_user.id)
    
    # 1. 获取各阶段订单数量
    stage_counts = {}
    for stage in OrderStage:
        stage_query = base_query.where(SalesRecord.stage == stage.value)
        result = await db.execute(stage_query)
        stage_counts[stage.value] = result.scalar() or 0
    
    # 2. 获取订单来源统计
    source_counts = {}
    for source in OrderSource:
        source_query = base_query.where(SalesRecord.order_source == source.value)
        result = await db.execute(source_query)
        source_counts[source.value] = result.scalar() or 0
    
    # 3. 历史总订单数量
    total_orders_result = await db.execute(base_query)
    total_orders = total_orders_result.scalar() or 0
    
    # 4. 计算本月销售总额（仅最终阶段订单）
    monthly_sales_query = select(
        func.sum(SalesRecord.total_price).label("total_sales")
    ).where(
        SalesRecord.created_at >= first_day,
        SalesRecord.created_at < next_month,
        SalesRecord.stage == OrderStage.STAGE_5.value
    )
    
    if not current_user.is_superuser:
        monthly_sales_query = monthly_sales_query.where(SalesRecord.user_id == current_user.id)
    
    monthly_sales_result = await db.execute(monthly_sales_query)
    total_sales = monthly_sales_result.scalar() or 0.0
    
    # 5. 审核统计
    pending_logistics_review = stage_counts.get(OrderStage.STAGE_2.value, 0)
    pending_final_review = stage_counts.get(OrderStage.STAGE_4.value, 0)
    completed_orders = stage_counts.get(OrderStage.STAGE_5.value, 0)
    
    # 构建返回结果
    return DashboardStats(
        total_sales=float(total_sales),
        total_orders=total_orders,
        stage_1_orders=stage_counts.get(OrderStage.STAGE_1.value, 0),
        stage_2_orders=stage_counts.get(OrderStage.STAGE_2.value, 0),
        stage_3_orders=stage_counts.get(OrderStage.STAGE_3.value, 0),
        stage_4_orders=stage_counts.get(OrderStage.STAGE_4.value, 0),
        stage_5_orders=stage_counts.get(OrderStage.STAGE_5.value, 0),
        alibaba_orders=source_counts.get(OrderSource.ALIBABA.value, 0),
        domestic_orders=source_counts.get(OrderSource.DOMESTIC.value, 0),
        exhibition_orders=source_counts.get(OrderSource.EXHIBITION.value, 0),
        pending_logistics_review=pending_logistics_review,
        pending_final_review=pending_final_review,
        completed_orders=completed_orders
    ) 