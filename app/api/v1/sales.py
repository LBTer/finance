from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, UTC

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.core.permissions import Action, check_sales_record_permissions, get_sales_record
from app.models.user import User, UserRole
from app.models.sales_record import SalesRecord, SalesStatus
from app.schemas.sales_record import (
    SalesRecordCreate,
    SalesRecordUpdate,
    SalesRecordResponse
)

router = APIRouter(prefix="/sales", tags=["销售记录"])

@router.post("", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.CREATE)
async def create_sales_record(
    *,
    db: AsyncSessionDep,
    record_in: SalesRecordCreate,
    current_user: Annotated[User, Depends(get_current_user)]
) -> SalesRecord:
    """
    创建销售记录
    """
    # 创建新记录
    record = SalesRecord(
        **record_in.model_dump(),
        user_id=current_user.id,
        status=SalesStatus.PENDING
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    # 重新查询以获取关联数据
    result = await db.execute(
        select(SalesRecord)
        .options(joinedload(SalesRecord.user))
        .where(SalesRecord.id == record.id)
    )
    return result.scalar_one()

@router.get("", response_model=List[SalesRecordResponse])
@check_sales_record_permissions(Action.READ)
async def get_sales_records(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: SalesStatus = None,
    search: str = None
) -> List[SalesRecord]:
    """
    获取销售记录列表（带分页）
    """
    query = select(SalesRecord).options(
        joinedload(SalesRecord.user),
        joinedload(SalesRecord.approved_by)
    )
    
    # 根据用户角色过滤
    if current_user.role == UserRole.NORMAL:
        query = query.where(SalesRecord.user_id == current_user.id)
    
    # 状态过滤
    if status:
        query = query.where(SalesRecord.status == status)
    
    # 搜索
    if search:
        query = query.where(
            or_(
                SalesRecord.order_number.contains(search),
                SalesRecord.product_name.contains(search)
            )
        )
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{record_id}", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.READ, get_sales_record)
async def get_sales_record_by_id(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> SalesRecord:
    """
    获取单个销售记录详情
    """
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.approved_by)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    return record

@router.put("/{record_id}", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.UPDATE, get_sales_record)
async def update_sales_record(
    record_id: int,
    record_in: SalesRecordUpdate,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> SalesRecord:
    """
    更新销售记录
    """
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.approved_by)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    # 更新记录
    for field, value in record_in.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    
    # 如果是审核操作
    if (record_in.status and 
        record_in.status != record.status and 
        current_user.role != UserRole.NORMAL):
        record.approved_by_id = current_user.id
        record.approved_at = datetime.now(UTC)
    
    await db.commit()
    await db.refresh(record)
    return record

@router.delete("/{record_id}")
@check_sales_record_permissions(Action.DELETE, get_sales_record)
async def delete_sales_record(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    删除销售记录
    """
    result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    await db.delete(record)
    await db.commit()
    
    return {"message": "记录已删除"} 