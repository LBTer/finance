import logging
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload
from datetime import datetime, UTC

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.core.permissions import Action, check_sales_record_permissions, get_sales_record
from app.models.user import User, UserRole
from app.models.fees import ShippingFees
from app.models.sales_record import SalesRecord, OrderStage
from app.schemas.fees import (
    ShippingFeesCreate,
    ShippingFeesUpdate,
    ShippingFeesResponse
)
from app.utils.logger import get_logger

# 获取当前模块的logger
logger = get_logger(__name__)

router = APIRouter(prefix="/fees", tags=["运费管理"])

@router.get("", response_model=List[ShippingFeesResponse])
async def get_shipping_fees(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    sales_record_id: Optional[int] = Query(None, description="订单ID筛选"),
    logistics_type: Optional[str] = Query(None, description="物流类型筛选"),
    logistics_company: Optional[str] = Query(None, description="物流公司筛选")
) -> List[ShippingFees]:
    """
    获取运费列表（分页显示）
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（用于分页）
    - **sales_record_id**: 按订单ID筛选（可选）
    - **logistics_type**: 按物流类型筛选（可选）
    - **logistics_company**: 按物流公司筛选（可选）
    
    返回按创建时间倒序排列的运费记录列表
    """
    logger.info(f"获取运费列表 - user_id: {current_user.id}, skip: {skip}, limit: {limit}")
    
    # 构建查询
    query = select(ShippingFees).options(
        joinedload(ShippingFees.sales_record).joinedload(SalesRecord.user)
    )
    
    # 添加筛选条件
    if sales_record_id:
        query = query.where(ShippingFees.sales_record_id == sales_record_id)
    if logistics_type:
        query = query.where(ShippingFees.logistics_type == logistics_type)
    if logistics_company:
        query = query.where(ShippingFees.logistics_company.contains(logistics_company))
    
    # 按创建时间倒序排列，分页
    query = query.order_by(desc(ShippingFees.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    fees_list = result.unique().scalars().all()
    
    logger.debug(f"运费列表查询完成 - 返回记录数: {len(fees_list)}")
    return fees_list

@router.get("/{fee_id}", response_model=ShippingFeesResponse)
async def get_shipping_fee_by_id(
    fee_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ShippingFees:
    """
    根据ID获取运费详情
    
    - **fee_id**: 运费记录ID
    """
    logger.info(f"获取运费详情 - fee_id: {fee_id}, user_id: {current_user.id}")
    
    result = await db.execute(
        select(ShippingFees)
        .options(
            joinedload(ShippingFees.sales_record).joinedload(SalesRecord.user)
        )
        .where(ShippingFees.id == fee_id)
    )
    
    fee = result.unique().scalar_one_or_none()
    if not fee:
        logger.warning(f"运费记录不存在 - fee_id: {fee_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="运费记录不存在"
        )
    
    logger.debug(f"运费详情获取成功 - fee_id: {fee_id}")
    return fee

@router.get("/sales-record/{sales_record_id}", response_model=List[ShippingFeesResponse])
async def get_shipping_fees_by_sales_record(
    sales_record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> List[ShippingFees]:
    """
    根据销售记录ID获取运费列表
    
    - **sales_record_id**: 销售记录ID
    
    返回该销售记录的所有运费记录
    """
    logger.info(f"获取销售记录运费列表 - sales_record_id: {sales_record_id}, user_id: {current_user.id}")
    
    # 检查销售记录是否存在
    sales_record_result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == sales_record_id)
    )
    sales_record = sales_record_result.scalar_one_or_none()
    
    if not sales_record:
        logger.warning(f"销售记录不存在 - sales_record_id: {sales_record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售记录不存在"
        )
    
    # 查询运费记录
    result = await db.execute(
        select(ShippingFees)
        .options(joinedload(ShippingFees.sales_record))
        .where(ShippingFees.sales_record_id == sales_record_id)
        .order_by(desc(ShippingFees.created_at))
    )
    
    fees = result.unique().scalars().all()
    logger.info(f"找到 {len(fees)} 条运费记录 - sales_record_id: {sales_record_id}")
    
    return fees

@router.post("", response_model=ShippingFeesResponse)
async def create_shipping_fee(
    *,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    fee_in: ShippingFeesCreate
) -> ShippingFees:
    """
    创建运费记录
    
    - **sales_record_id**: 关联的订单ID
    - **shipping_fee**: 运费金额（人民币）
    - **logistics_type**: 物流类型
    - **payment_method**: 支付方式
    - **logistics_company**: 物流公司
    - **remarks**: 备注（可选）
    """
    logger.info(f"创建运费记录 - user_id: {current_user.id}, sales_record_id: {fee_in.sales_record_id}")
    
    # 检查关联的销售记录是否存在
    sales_record_result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == fee_in.sales_record_id)
    )
    sales_record = sales_record_result.scalar_one_or_none()
    
    if not sales_record:
        logger.warning(f"关联的销售记录不存在 - sales_record_id: {fee_in.sales_record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联的销售记录不存在"
        )
    
    # 检查销售记录是否已处于最终阶段（阶段四、五不允许创建运费记录）
    if sales_record.stage in [OrderStage.STAGE_4.value, OrderStage.STAGE_5.value]:
        logger.warning(f"销售记录已处于最终阶段，不可创建运费记录 - sales_record_id: {fee_in.sales_record_id}, stage: {sales_record.stage}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="销售记录已处于最终阶段，不可创建运费记录"
        )
    
    # 创建运费记录
    fee_data = fee_in.model_dump()
    fee = ShippingFees(**fee_data)
    
    db.add(fee)
    await db.commit()
    await db.refresh(fee)
    
    # 重新查询以获取关联数据
    result = await db.execute(
        select(ShippingFees)
        .options(
            joinedload(ShippingFees.sales_record).joinedload(SalesRecord.user)
        )
        .where(ShippingFees.id == fee.id)
    )
    final_fee = result.unique().scalar_one()
    
    logger.info(f"运费记录创建成功 - fee_id: {final_fee.id}")
    return final_fee

@router.put("/{fee_id}", response_model=ShippingFeesResponse)
async def update_shipping_fee(
    fee_id: int,
    *,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    fee_in: ShippingFeesUpdate
) -> ShippingFees:
    """
    更新运费记录
    
    - **fee_id**: 运费记录ID
    - 其他字段为可选更新字段
    
    注意：如果关联的销售记录已处于最终阶段，则不可编辑
    """
    logger.info(f"更新运费记录 - fee_id: {fee_id}, user_id: {current_user.id}")
    
    # 获取运费记录
    result = await db.execute(
        select(ShippingFees)
        .options(joinedload(ShippingFees.sales_record))
        .where(ShippingFees.id == fee_id)
    )
    fee = result.unique().scalar_one_or_none()
    
    if not fee:
        logger.warning(f"运费记录不存在 - fee_id: {fee_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="运费记录不存在"
        )
    
    # 检查关联的销售记录是否已处于最终阶段（阶段四、五不允许编辑运费记录）
    if fee.sales_record.stage in [OrderStage.STAGE_4.value, OrderStage.STAGE_5.value]:
        logger.warning(f"关联的销售记录已处于最终阶段，不可编辑 - fee_id: {fee_id}, stage: {fee.sales_record.stage}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的销售记录已处于最终阶段，不可编辑"
        )
    
    # 更新字段
    update_data = fee_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fee, field, value)
    
    await db.commit()
    await db.refresh(fee)
    
    # 重新查询以获取关联数据
    result = await db.execute(
        select(ShippingFees)
        .options(
            joinedload(ShippingFees.sales_record).joinedload(SalesRecord.user)
        )
        .where(ShippingFees.id == fee.id)
    )
    final_fee = result.unique().scalar_one()
    
    logger.info(f"运费记录更新成功 - fee_id: {fee_id}")
    return final_fee

@router.delete("/{fee_id}")
async def delete_shipping_fee(
    fee_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    删除运费记录
    
    - **fee_id**: 运费记录ID
    
    注意：如果关联的销售记录已处于最终阶段，则不可删除
    """
    logger.info(f"删除运费记录 - fee_id: {fee_id}, user_id: {current_user.id}")
    
    # 获取运费记录
    result = await db.execute(
        select(ShippingFees)
        .options(joinedload(ShippingFees.sales_record))
        .where(ShippingFees.id == fee_id)
    )
    fee = result.unique().scalar_one_or_none()
    
    if not fee:
        logger.warning(f"运费记录不存在 - fee_id: {fee_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="运费记录不存在"
        )
    
    # 检查关联的销售记录是否已处于最终阶段（阶段四、五不允许删除运费记录）
    if fee.sales_record.stage in [OrderStage.STAGE_4.value, OrderStage.STAGE_5.value]:
        logger.warning(f"关联的销售记录已处于最终阶段，不可删除 - fee_id: {fee_id}, stage: {fee.sales_record.stage}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的销售记录已处于最终阶段，不可删除"
        )
    
    await db.delete(fee)
    await db.commit()
    
    logger.info(f"运费记录删除成功 - fee_id: {fee_id}")
    return {"message": "运费记录删除成功"}

@router.get("/stats/summary")
async def get_shipping_fees_stats(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    获取运费统计信息
    
    返回运费总数、总金额等统计数据
    """
    logger.info(f"获取运费统计信息 - user_id: {current_user.id}")
    
    # 统计运费总数和总金额
    result = await db.execute(
        select(
            func.count(ShippingFees.id).label("total_count"),
            func.coalesce(func.sum(ShippingFees.shipping_fee), 0).label("total_amount")
        )
    )
    stats = result.first()
    
    logger.debug(f"运费统计信息获取完成 - 总数: {stats.total_count}, 总金额: {stats.total_amount}")
    
    return {
        "total_count": stats.total_count,
        "total_amount": float(stats.total_amount)
    } 