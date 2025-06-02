from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.models.user import User
from app.models.sales_record import SalesRecord, SalesStatus
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
        - approved_orders: 已审核订单数量
        - pending_orders: 待审核订单数量
        - rejected_orders: 被拒绝订单数量
    """
    # 获取当前月份的第一天和最后一天
    now = datetime.now(timezone.utc)
    first_day = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    
    # 计算下个月的第一天，然后减去1秒得到当月最后一天
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
    last_day = next_month - timedelta(seconds=1)
    
    # 查询当月销售总额
    total_sales_query = select(
        func.sum(
            (SalesRecord.unit_price * SalesRecord.quantity) + 
            SalesRecord.shipping_fee - 
            SalesRecord.refund_amount
        ).label("total_sales")
    ).where(
        SalesRecord.created_at.between(first_day, last_day),
        SalesRecord.status == SalesStatus.APPROVED
    )
    
    if current_user.is_superuser is False:
        # 非管理员只能看到自己的销售记录
        total_sales_query = total_sales_query.where(
            SalesRecord.user_id == current_user.id
        )
    
    # 执行查询获取当月销售总额
    total_sales_result = await db.execute(total_sales_query)
    total_sales = total_sales_result.scalar() or 0
    
    # 查询各状态订单数量
    status_counts_query = select(
        SalesRecord.status,
        func.count(SalesRecord.id).label("count")
    ).group_by(
        SalesRecord.status
    )
    
    if current_user.is_superuser is False:
        # 非管理员只能看到自己的销售记录
        status_counts_query = status_counts_query.where(
            SalesRecord.user_id == current_user.id
        )
    
    # 执行查询获取各状态订单数量
    status_counts_result = await db.execute(status_counts_query)
    status_counts = {status.value: count for status, count in status_counts_result.all()}
    
    # 构建返回结果
    return DashboardStats(
        total_sales=float(total_sales),
        approved_orders=status_counts.get(SalesStatus.APPROVED.value, 0),
        pending_orders=status_counts.get(SalesStatus.PENDING.value, 0),
        rejected_orders=status_counts.get(SalesStatus.REJECTED.value, 0)
    ) 