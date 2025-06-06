import logging
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
from app.utils.logger import get_logger

# 获取当前模块的logger
logger = get_logger(__name__)

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
    创建销售记录 (美金订单)
    
    - **order_number**: 订单号（唯一标识）
    - **product_name**: 产品名称
    - **category**: 类别（可选）
    - **quantity**: 数量
    - **unit_price**: 单价
    - **total_price**: 总价
    - **domestic_shipping_fee**: 运费（陆内）
    - **overseas_shipping_fee**: 运费（海运）
    - **logistics_company**: 物流公司（可选）
    - **refund_amount**: 退款金额
    - **tax_refund**: 退税金额
    - **profit**: 利润
    - **remarks**: 备注（可选）
    """
    logger.info(f"创建销售记录 - user_id: {current_user.id}, order_number: {record_in.order_number}")
    logger.debug(f"创建数据: {record_in.model_dump()}")
    
    # 创建新记录
    record = SalesRecord(
        **record_in.model_dump(),
        user_id=current_user.id,
        status=SalesStatus.PENDING
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    logger.info(f"销售记录创建成功 - id: {record.id}, order_number: {record.order_number}")
    
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
    search: str = None,
    category: str = None
) -> List[SalesRecord]:
    """
    获取销售记录列表（带分页）
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **status**: 按状态筛选 (pending/approved/rejected)
    - **search**: 搜索订单号或产品名称
    - **category**: 按类别筛选
    """
    logger.info(f"获取销售记录列表 - user_id: {current_user.id} ({current_user.role}), skip: {skip}, limit: {limit}")
    logger.debug(f"筛选条件 - status: {status}, search: {search}, category: {category}")
    
    query = select(SalesRecord).options(
        joinedload(SalesRecord.user),
        joinedload(SalesRecord.approved_by)
    )
    
    # 根据用户角色过滤
    if current_user.role == UserRole.NORMAL:
        query = query.where(SalesRecord.user_id == current_user.id)
        logger.debug("普通用户权限 - 只显示自己的记录")
    
    # 状态过滤
    if status:
        query = query.where(SalesRecord.status == status)
        logger.debug(f"状态筛选 - {status}")
    
    # 类别过滤
    if category:
        query = query.where(SalesRecord.category == category)
        logger.debug(f"类别筛选 - {category}")
    
    # 搜索
    if search:
        query = query.where(
            or_(
                SalesRecord.order_number.contains(search),
                SalesRecord.product_name.contains(search),
                SalesRecord.logistics_company.contains(search)
            )
        )
        logger.debug(f"搜索筛选 - {search}")
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    logger.info(f"查询完成 - 返回 {len(records)} 条记录")
    return records

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
    logger.info(f"获取销售记录详情 - record_id: {record_id}, user_id: {current_user.id}")
    
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
        logger.warning(f"查询的记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    logger.info(f"记录查询成功 - id: {record.id}, order_number: {record.order_number}, status: {record.status}")
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
    
    - **product_name**: 产品名称
    - **category**: 类别
    - **quantity**: 数量
    - **unit_price**: 单价
    - **total_price**: 总价
    - **domestic_shipping_fee**: 运费（陆内）
    - **overseas_shipping_fee**: 运费（海运）
    - **logistics_company**: 物流公司
    - **refund_amount**: 退款金额
    - **tax_refund**: 退税金额
    - **profit**: 利润
    - **remarks**: 备注
    - **status**: 状态 (pending/approved/rejected)
    """
    logger.info(f"开始更新销售记录 - record_id: {record_id}, current_user: {current_user.id} ({current_user.role})")
    logger.debug(f"更新数据: {record_in.model_dump(exclude_unset=True)}")
    
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
        logger.warning(f"记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    # 记录更新前的状态
    original_status = record.status
    original_approved_by_id = record.approved_by_id
    original_approved_at = record.approved_at
    
    logger.info(f"记录更新前状态 - status: {original_status}, approved_by_id: {original_approved_by_id}, approved_at: {original_approved_at}")
    
    # 确保在此处已加载完所有必要属性
    _ = record.order_number  # 预先加载order_number属性，避免后续延迟加载
    
    # 更新记录
    update_data = record_in.model_dump(exclude_unset=True)
    logger.debug(f"准备更新的字段: {update_data}")
    
    for field, value in update_data.items():
        logger.debug(f"设置字段 {field}: {getattr(record, field, '未设置')} -> {value}")
        setattr(record, field, value)
    
    # 记录状态变更信息
    new_status = getattr(record_in, 'status', None)
    logger.info(f"状态变更检查 - 原状态: {original_status}, 新状态: {new_status}")
    
    # 详细的审核条件检查
    logger.info("=== 审核条件检查 ===")
    logger.info(f"1. record_in.status 存在: {record_in.status is not None} (值: {record_in.status})")
    logger.info(f"2. 状态发生变化: {record_in.status != original_status} ({record_in.status} != {original_status})")
    logger.info(f"3. 原状态是待审核: {original_status == SalesStatus.PENDING} ({original_status} == {SalesStatus.PENDING})")
    logger.info(f"4. 新状态是审核状态: {record_in.status in [SalesStatus.APPROVED, SalesStatus.REJECTED] if record_in.status else False}")
    logger.info(f"5. 用户不是普通用户: {current_user.role != UserRole.NORMAL} ({current_user.role} != {UserRole.NORMAL})")
    
    # 如果是审核操作（状态从待审核变为已审核或已拒绝）
    audit_condition = (record_in.status and 
                      record_in.status != original_status and 
                      original_status == SalesStatus.PENDING and
                      record_in.status in [SalesStatus.APPROVED, SalesStatus.REJECTED] and
                      current_user.role != UserRole.NORMAL)
    
    logger.info(f"审核条件总结果: {audit_condition}")
    
    if audit_condition:
        logger.info(f"执行审核操作 - 设置审核人: {current_user.id}, 审核时间: {datetime.now(UTC)}")
        record.approved_by_id = current_user.id
        record.approved_at = datetime.now(UTC)
        logger.info(f"审核信息已设置 - approved_by_id: {record.approved_by_id}, approved_at: {record.approved_at}")
    else:
        logger.info("不满足审核条件，跳过审核信息设置")
    
    try:
        logger.info("开始提交数据库事务...")
        await db.commit()
        logger.info("数据库事务提交成功")
        
        await db.refresh(record)
        logger.info("记录刷新完成")
        
        # 记录最终状态
        logger.info(f"更新后状态 - status: {record.status}, approved_by_id: {record.approved_by_id}, approved_at: {record.approved_at}")
        
        # 重新查询以确保关联数据被正确加载
        result = await db.execute(
            select(SalesRecord)
            .options(
                joinedload(SalesRecord.user),
                joinedload(SalesRecord.approved_by)
            )
            .where(SalesRecord.id == record.id)
        )
        final_record = result.scalar_one()
        
        logger.info(f"最终查询结果 - status: {final_record.status}, approved_by_id: {final_record.approved_by_id}, approved_at: {final_record.approved_at}")
        logger.info(f"审核人信息: {final_record.approved_by.full_name if final_record.approved_by else 'None'}")
        
        return final_record
    except Exception as e:
        logger.error(f"更新记录失败: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新记录失败: {str(e)}"
        )

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
    logger.info(f"删除销售记录 - record_id: {record_id}, user_id: {current_user.id}")
    
    result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        logger.warning(f"要删除的记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    # 确保加载所有属性，避免懒加载问题
    _ = record.order_number
    order_number = record.order_number
    
    logger.info(f"准备删除记录 - id: {record_id}, order_number: {order_number}")
    
    try:
        await db.delete(record)
        await db.commit()
        logger.info(f"销售记录删除成功 - id: {record_id}, order_number: {order_number}")
        return {"message": "记录已删除"}
    except Exception as e:
        logger.error(f"删除记录失败 - id: {record_id}: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除记录失败: {str(e)}"
        ) 