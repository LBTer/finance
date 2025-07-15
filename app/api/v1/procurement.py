import logging
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload
from datetime import datetime, UTC

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.core.permissions import Action, check_sales_record_permissions, get_sales_record
from app.models.user import User, UserRole
from app.models.procurement import Procurement
from app.models.sales_record import SalesRecord, OrderStage
from app.schemas.procurement import (
    ProcurementCreate,
    ProcurementUpdate,
    ProcurementResponse
)
from app.utils.logger import get_logger

# 获取当前模块的logger
logger = get_logger(__name__)

router = APIRouter(prefix="/procurement", tags=["采购管理"])

@router.get("", response_model=List[ProcurementResponse])
async def get_procurements(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    sales_record_id: Optional[int] = Query(None, description="订单ID筛选"),
    supplier: Optional[str] = Query(None, description="供应单位筛选"),
    procurement_item: Optional[str] = Query(None, description="采购事项筛选")
) -> List[Procurement]:
    """
    获取采购列表（分页显示）
    
    - **skip**: 跳过的记录数（用于分页）
    - **limit**: 返回的记录数（用于分页）
    - **sales_record_id**: 按订单ID筛选（可选）
    - **supplier**: 按供应单位筛选（可选）
    - **procurement_item**: 按采购事项筛选（可选）
    
    返回按创建时间倒序排列的采购记录列表
    """
    logger.info(f"获取采购列表 - user_id: {current_user.id}, skip: {skip}, limit: {limit}")
    
    # 构建查询
    query = select(Procurement).options(
        joinedload(Procurement.sales_record).joinedload(SalesRecord.user)
    )
    
    # 添加筛选条件
    if sales_record_id:
        query = query.where(Procurement.sales_record_id == sales_record_id)
    if supplier:
        query = query.where(Procurement.supplier.contains(supplier))
    if procurement_item:
        query = query.where(Procurement.procurement_item.contains(procurement_item))
    
    # 按创建时间倒序排列，分页
    query = query.order_by(desc(Procurement.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    procurement_list = result.unique().scalars().all()
    
    logger.debug(f"采购列表查询完成 - 返回记录数: {len(procurement_list)}")
    return procurement_list

@router.get("/{procurement_id}", response_model=ProcurementResponse)
async def get_procurement_by_id(
    procurement_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> Procurement:
    """
    根据ID获取采购详情
    
    - **procurement_id**: 采购记录ID
    """
    logger.info(f"获取采购详情 - procurement_id: {procurement_id}, user_id: {current_user.id}")
    
    result = await db.execute(
        select(Procurement)
        .options(
            joinedload(Procurement.sales_record).joinedload(SalesRecord.user)
        )
        .where(Procurement.id == procurement_id)
    )
    
    procurement = result.unique().scalar_one_or_none()
    if not procurement:
        logger.warning(f"采购记录不存在 - procurement_id: {procurement_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购记录不存在"
        )
    
    logger.debug(f"采购详情获取成功 - procurement_id: {procurement_id}")
    return procurement

@router.get("/sales-record/{sales_record_id}", response_model=List[ProcurementResponse])
async def get_procurement_by_sales_record(
    sales_record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> List[Procurement]:
    """
    根据销售记录ID获取采购列表
    
    - **sales_record_id**: 销售记录ID
    
    返回该销售记录的所有采购记录
    """
    logger.info(f"获取销售记录采购列表 - sales_record_id: {sales_record_id}, user_id: {current_user.id}")
    
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
    
    # 查询采购记录
    result = await db.execute(
        select(Procurement)
        .options(joinedload(Procurement.sales_record))
        .where(Procurement.sales_record_id == sales_record_id)
        .order_by(desc(Procurement.created_at))
    )
    
    procurements = result.unique().scalars().all()
    logger.info(f"找到 {len(procurements)} 条采购记录 - sales_record_id: {sales_record_id}")
    
    return procurements

@router.post("", response_model=ProcurementResponse)
async def create_procurement(
    *,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    procurement_in: ProcurementCreate
) -> Procurement:
    """
    创建采购记录
    
    - **sales_record_id**: 关联的订单ID
    - **supplier**: 供应单位
    - **procurement_item**: 采购事项
    - **quantity**: 数量
    - **amount**: 金额（人民币）
    - **payment_method**: 支付方式
    - **remarks**: 备注（可选）
    """
    logger.info(f"创建采购记录 - user_id: {current_user.id}, sales_record_id: {procurement_in.sales_record_id}")
    
    # 检查关联的销售记录是否存在
    sales_record_result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == procurement_in.sales_record_id)
    )
    sales_record = sales_record_result.scalar_one_or_none()
    
    if not sales_record:
        logger.warning(f"关联的销售记录不存在 - sales_record_id: {procurement_in.sales_record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关联的销售记录不存在"
        )
    
    # 检查销售记录是否已处于最终阶段（阶段四、五不允许创建采购记录）
    if sales_record.stage in [OrderStage.STAGE_4.value, OrderStage.STAGE_5.value]:
        logger.warning(f"销售记录已处于最终阶段，不可创建采购记录 - sales_record_id: {procurement_in.sales_record_id}, stage: {sales_record.stage}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="销售记录已处于最终阶段，不可创建采购记录"
        )
    
    # 创建采购记录
    procurement_data = procurement_in.model_dump()
    procurement = Procurement(**procurement_data)
    
    db.add(procurement)
    await db.commit()
    await db.refresh(procurement)
    
    # 重新查询以获取关联数据
    result = await db.execute(
        select(Procurement)
        .options(
            joinedload(Procurement.sales_record).joinedload(SalesRecord.user)
        )
        .where(Procurement.id == procurement.id)
    )
    final_procurement = result.unique().scalar_one()
    
    logger.info(f"采购记录创建成功 - procurement_id: {final_procurement.id}")
    return final_procurement

@router.put("/{procurement_id}", response_model=ProcurementResponse)
async def update_procurement(
    procurement_id: int,
    *,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    procurement_in: ProcurementUpdate
) -> Procurement:
    """
    更新采购记录
    
    - **procurement_id**: 采购记录ID
    - 其他字段为可选更新字段
    
    注意：如果关联的销售记录已处于最终阶段，则不可编辑
    """
    logger.info(f"更新采购记录 - procurement_id: {procurement_id}, user_id: {current_user.id}")
    
    # 获取采购记录
    result = await db.execute(
        select(Procurement)
        .options(joinedload(Procurement.sales_record))
        .where(Procurement.id == procurement_id)
    )
    procurement = result.unique().scalar_one_or_none()
    
    if not procurement:
        logger.warning(f"采购记录不存在 - procurement_id: {procurement_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购记录不存在"
        )
    
    # 检查关联的销售记录是否已处于最终阶段（阶段四、五不允许编辑采购记录）
    if procurement.sales_record.stage in [OrderStage.STAGE_4.value, OrderStage.STAGE_5.value]:
        logger.warning(f"关联的销售记录已处于最终阶段，不可编辑 - procurement_id: {procurement_id}, stage: {procurement.sales_record.stage}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的销售记录已处于最终阶段，不可编辑"
        )
    
    # 更新字段
    update_data = procurement_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(procurement, field, value)
    
    await db.commit()
    await db.refresh(procurement)
    
    # 重新查询以获取关联数据
    result = await db.execute(
        select(Procurement)
        .options(
            joinedload(Procurement.sales_record).joinedload(SalesRecord.user)
        )
        .where(Procurement.id == procurement.id)
    )
    final_procurement = result.unique().scalar_one()
    
    logger.info(f"采购记录更新成功 - procurement_id: {procurement_id}")
    return final_procurement

@router.delete("/{procurement_id}")
async def delete_procurement(
    procurement_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    删除采购记录
    
    - **procurement_id**: 采购记录ID
    
    注意：如果关联的销售记录已处于最终阶段，则不可删除
    """
    logger.info(f"删除采购记录 - procurement_id: {procurement_id}, user_id: {current_user.id}")
    
    # 获取采购记录
    result = await db.execute(
        select(Procurement)
        .options(joinedload(Procurement.sales_record))
        .where(Procurement.id == procurement_id)
    )
    procurement = result.unique().scalar_one_or_none()
    
    if not procurement:
        logger.warning(f"采购记录不存在 - procurement_id: {procurement_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购记录不存在"
        )
    
    # 检查关联的销售记录是否已处于最终阶段（阶段四、五不允许删除采购记录）
    if procurement.sales_record.stage in [OrderStage.STAGE_4.value, OrderStage.STAGE_5.value]:
        logger.warning(f"关联的销售记录已处于最终阶段，不可删除 - procurement_id: {procurement_id}, stage: {procurement.sales_record.stage}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="关联的销售记录已处于最终阶段，不可删除"
        )
    
    await db.delete(procurement)
    await db.commit()
    
    logger.info(f"采购记录删除成功 - procurement_id: {procurement_id}")
    return {"message": "采购记录删除成功"}

@router.get("/stats/summary")
async def get_procurement_stats(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    获取采购统计信息
    
    返回采购总数、总金额、总数量等统计数据
    """
    logger.info(f"获取采购统计信息 - user_id: {current_user.id}")
    
    # 统计采购总数、总金额和总数量
    result = await db.execute(
        select(
            func.count(Procurement.id).label("total_count"),
            func.coalesce(func.sum(Procurement.amount), 0).label("total_amount"),
            func.coalesce(func.sum(Procurement.quantity), 0).label("total_quantity")
        )
    )
    stats = result.first()
    
    logger.debug(f"采购统计信息获取完成 - 总数: {stats.total_count}, 总金额: {stats.total_amount}, 总数量: {stats.total_quantity}")
    
    return {
        "total_count": stats.total_count,
        "total_amount": float(stats.total_amount),
        "total_quantity": stats.total_quantity
    } 