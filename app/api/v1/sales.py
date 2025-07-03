import logging
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, UTC

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.core.permissions import Action, check_sales_record_permissions, get_sales_record
from app.models.user import User, UserRole
from app.models.sales_record import OrderSource, SalesRecord, OrderStage, OrderType
from app.models.attachment import Attachment, AttachmentType
from app.schemas.sales_record import (
    SalesRecordCreate,
    SalesRecordUpdate,
    SalesRecordResponse
)
from app.utils.logger import get_logger

# 导入附件处理函数
from app.api.v1.attachments import validate_and_save_attachments

# 获取当前模块的logger
logger = get_logger(__name__)

router = APIRouter(prefix="/sales", tags=["销售记录"])

@router.get("/check-order-number/{order_number}")
@check_sales_record_permissions(Action.CREATE)
async def check_order_number(
    order_number: str,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    检查订单号是否可用
    
    - **order_number**: 要检查的订单号
    
    返回:
    - **available**: 是否可用 (true/false)
    - **message**: 提示信息
    """
    logger.info(f"检查订单号可用性 - order_number: {order_number}, user_id: {current_user.id}")
    
    existing_record = await db.execute(
        select(SalesRecord).where(SalesRecord.order_number == order_number)
    )
    
    if existing_record.scalar_one_or_none():
        logger.debug(f"订单号已存在 - {order_number}")
        return {
            "available": False,
            "message": f"订单号 '{order_number}' 已存在"
        }
    else:
        logger.debug(f"订单号可用 - {order_number}")
        return {
            "available": True,
            "message": f"订单号 '{order_number}' 可用"
        }

@router.post("", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.CREATE)
async def create_sales_record(
    *,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    # 表单字段
    order_number: str = Form(...),
    order_type: str = Form(...),
    order_source: str = Form(...),
    product_name: str = Form(...),
    quantity: int = Form(...),
    unit_price: float = Form(...),
    total_price: float = Form(...),
    exchange_rate: float = Form(7.0000),
    domestic_shipping_fee: float = Form(0),
    overseas_shipping_fee: float = Form(0),
    refund_amount: float = Form(0),
    tax_refund: float = Form(0),
    profit: float = Form(0),
    category: Optional[str] = Form(None),
    logistics_company: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    attachment_type: str = Form(AttachmentType.SALES.value),
    files: Optional[List[UploadFile]] = File(None)
) -> SalesRecord:
    """
    创建销售记录 (美金订单)
    
    - **order_number**: 订单号（唯一标识）
    - **order_type**: 订单类型 (overseas/domestic)
    - **order_source**: 订单来源 (alibaba/domestic/exhibition)
    - **product_name**: 产品名称
    - **category**: 类别（可选）
    - **quantity**: 数量
    - **unit_price**: 单价（美元）
    - **total_price**: 总价（美元）
    - **domestic_shipping_fee**: 运费-陆内（人民币）
    - **overseas_shipping_fee**: 运费-海运（人民币）
    - **logistics_company**: 物流公司（可选）
    - **refund_amount**: 退款金额（人民币）
    - **tax_refund**: 退税金额（人民币）
    - **profit**: 利润（人民币）
    - **remarks**: 备注（可选）
    - **attachment_type**: 附件类型 (sales/logistics)
    - **files**: 附件文件列表（可选）
    """
    logger.info(f"创建销售记录 - user_id: {current_user.id}, order_number: {order_number}, order_type: {order_type}")
    
    # 验证订单类型
    if order_type not in [OrderType.OVERSEAS.value, OrderType.DOMESTIC.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的订单类型: {order_type}"
        )
    # 验证订单来源
    if order_source not in [OrderSource.ALIBABA.value, OrderSource.DOMESTIC.value, OrderSource.EXHIBITION.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的订单来源: {order_source}"
        )
    
    # 检查订单号是否已存在
    existing_record = await db.execute(
        select(SalesRecord).where(SalesRecord.order_number == order_number)
    )
    if existing_record.scalar_one_or_none():
        logger.warning(f"订单号重复 - order_number: {order_number}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单号 '{order_number}' 已存在，请使用不同的订单号"
        )
    
    # 构建记录数据
    record_data = {
        'order_number': order_number,
        'order_type': order_type,
        'order_source': order_source,
        'product_name': product_name,
        'quantity': quantity,
        'unit_price': unit_price,
        'total_price': total_price,
        'exchange_rate': exchange_rate,
        'domestic_shipping_fee': domestic_shipping_fee,
        'overseas_shipping_fee': overseas_shipping_fee,
        'refund_amount': refund_amount,
        'tax_refund': tax_refund,
        'profit': profit,
        'category': category,
        'logistics_company': logistics_company,
        'remarks': remarks,
        'user_id': current_user.id,
        'stage': OrderStage.STAGE_1.value
    }
    
    logger.debug(f"创建数据: {record_data}")
    
    if files:
        logger.info(f"包含附件 - 文件数量: {len(files)}, 附件类型: {attachment_type}")
    
    # 创建新记录
    record = SalesRecord(**record_data)
    db.add(record)
    
    try:
        # 先提交销售记录以获取ID
        await db.commit()
        await db.refresh(record)
        
        logger.info(f"销售记录创建成功 - id: {record.id}, order_number: {record.order_number}")
        
        # 如果有附件，处理附件上传
        if files:
            logger.info(f"开始处理附件 - record_id: {record.id}")
            attachments = await validate_and_save_attachments(files, record.id, attachment_type, db, current_user.id)
            
            # 提交附件记录
            await db.commit()
            for attachment in attachments:
                await db.refresh(attachment)
            
            logger.info(f"附件处理完成 - record_id: {record.id}, 附件数量: {len(attachments)}")
        
        # 重新查询以获取关联数据
        result = await db.execute(
            select(SalesRecord)
            .options(
                joinedload(SalesRecord.user),
                joinedload(SalesRecord.logistics_approved_by),
                joinedload(SalesRecord.final_approved_by),
                joinedload(SalesRecord.attachments)
            )
            .where(SalesRecord.id == record.id)
        )
        final_record = result.unique().scalar_one()
        
        logger.info(f"销售记录创建完成 - id: {final_record.id}, 附件数量: {len(final_record.attachments)}")
        return final_record
    
    except Exception as e:
        logger.error(f"创建销售记录失败: {str(e)}", exc_info=True)
        await db.rollback()
        
        # 如果销售记录已创建但附件处理失败，需要清理可能已保存的文件
        if hasattr(record, 'id') and files:
            try:
                # 查询可能已创建的附件记录
                result = await db.execute(
                    select(Attachment).where(Attachment.sales_record_id == record.id)
                )
                created_attachments = result.scalars().all()
                
                # 清理已保存的文件
                for attachment in created_attachments:
                    try:
                        # 检查文件是否被其他记录引用
                        result = await db.execute(
                            select(Attachment).where(Attachment.stored_filename == attachment.stored_filename)
                        )
                        if not result.scalar_one_or_none():
                            from app.utils.file_handler import file_handler
                            file_handler.delete_file(attachment.stored_filename)
                            logger.info(f"清理：删除未被引用的文件 - {attachment.stored_filename}")
                    except Exception as cleanup_error:
                        logger.warning(f"清理文件时出错: {cleanup_error}")
            except Exception as query_error:
                logger.warning(f"查询附件记录时出错: {query_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建销售记录失败: {str(e)}"
        )

@router.get("", response_model=List[SalesRecordResponse])
@check_sales_record_permissions(Action.READ)
async def get_sales_records(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    stage: str = None,
    order_type: str = None,
    search: str = None,
    category: str = None
) -> List[SalesRecord]:
    """
    获取销售记录列表（带分页）
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **stage**: 按阶段筛选 (stage_1/stage_2/stage_3/stage_4/stage_5)
    - **order_type**: 按订单类型筛选 (alibaba/domestic/exhibition)
    - **search**: 搜索订单号或产品名称
    - **category**: 按类别筛选
    """
    logger.info(f"获取销售记录列表 - user_id: {current_user.id} ({current_user.role}), skip: {skip}, limit: {limit}")
    logger.debug(f"筛选条件 - stage: {stage}, order_type: {order_type}, search: {search}, category: {category}")
    
    query = select(SalesRecord).options(
        joinedload(SalesRecord.user),
        joinedload(SalesRecord.logistics_approved_by),
        joinedload(SalesRecord.final_approved_by),
        joinedload(SalesRecord.attachments)
    )
    
    # 根据用户角色过滤
    if current_user.role == UserRole.NORMAL.value:
        query = query.where(SalesRecord.user_id == current_user.id)
        logger.debug("普通用户权限 - 只显示自己的记录")
    
    # 阶段过滤
    if stage:
        # 验证阶段值
        valid_stages = [OrderStage.STAGE_1.value, OrderStage.STAGE_2.value, OrderStage.STAGE_3.value, 
                       OrderStage.STAGE_4.value, OrderStage.STAGE_5.value]
        if stage not in valid_stages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的阶段: {stage}"
            )
        query = query.where(SalesRecord.stage == stage)
        logger.debug(f"阶段筛选 - {stage}")
    
    # 订单类型过滤
    if order_type:
        # 验证订单类型值
        valid_types = [OrderType.OVERSEAS.value, OrderType.DOMESTIC.value]
        if order_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的订单类型: {order_type}"
            )
        query = query.where(SalesRecord.order_type == order_type)
        logger.debug(f"订单类型筛选 - {order_type}")
    
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
    
    # 按ID倒序排序（最新记录在前）
    query = query.order_by(SalesRecord.id.desc())
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    records = result.unique().scalars().all()
    
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
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        logger.warning(f"查询的记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    logger.info(f"记录查询成功 - id: {record.id}, order_number: {record.order_number}, stage: {record.stage}")
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
    
    支持5阶段审核流程：
    - 第一阶段：初次创建，信息补充阶段
    - 第二阶段：待后勤审核  
    - 第三阶段：后勤审核通过，信息补充阶段
    - 第四阶段：待最终审核
    - 第五阶段：超级/高级用户审核通过
    """
    logger.info(f"开始更新销售记录 - record_id: {record_id}, current_user: {current_user.id} ({current_user.role})")
    logger.debug(f"更新数据: {record_in.model_dump(exclude_unset=True)}")
    
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        logger.warning(f"记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    # 记录更新前的状态
    original_stage = record.stage
    logger.info(f"记录更新前阶段: {original_stage}")
    
    # 确保在此处已加载完所有必要属性
    _ = record.order_number  # 预先加载order_number属性，避免后续延迟加载
    
    # 更新记录
    update_data = record_in.model_dump(exclude_unset=True)
    logger.debug(f"准备更新的字段: {update_data}")
    
    for field, value in update_data.items():
        logger.debug(f"设置字段 {field}: {getattr(record, field, '未设置')} -> {value}")
        setattr(record, field, value)
    
    # 处理阶段变更和审核逻辑
    new_stage = getattr(record_in, 'stage', None)
    if new_stage and new_stage != original_stage:
        logger.info(f"阶段变更: {original_stage} -> {new_stage}")
        
        # 验证阶段变更的合法性和权限
        if new_stage == OrderStage.STAGE_2.value:
            # 第一阶段 -> 第二阶段：销售人员提交审核
            if original_stage != OrderStage.STAGE_1.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能从第一阶段提交到第二阶段"
                )
            if not current_user.has_sales_function():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有销售人员可以提交审核"
                )
            logger.info("销售人员提交到第二阶段审核")
            
        elif new_stage == OrderStage.STAGE_3.value:
            # 第二阶段 -> 第三阶段：后勤人员审核通过
            if original_stage != OrderStage.STAGE_2.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能从第二阶段审核到第三阶段"
                )
            if not current_user.has_logistics_function():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有后勤人员可以进行后勤审核"
                )
            # 设置后勤审核信息
            record.logistics_approved_by_id = current_user.id
            record.logistics_approved_at = datetime.now(UTC)
            logger.info(f"后勤人员审核通过 - approved_by: {current_user.id}")
            
        elif new_stage == OrderStage.STAGE_4.value:
            # 第三阶段 -> 第四阶段：后勤人员提交最终审核
            if original_stage != OrderStage.STAGE_3.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能从第三阶段提交到第四阶段"
                )
            if not current_user.has_logistics_function():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有后勤人员可以提交最终审核"
                )
            logger.info("后勤人员提交到第四阶段最终审核")
            
        elif new_stage == OrderStage.STAGE_5.value:
            # 第四阶段 -> 第五阶段：超级/高级用户最终审核通过
            if original_stage != OrderStage.STAGE_4.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能从第四阶段审核到第五阶段"
                )
            if not current_user.can_approve_final():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有超级用户或高级用户可以进行最终审核"
                )
            # 设置最终审核信息
            record.final_approved_by_id = current_user.id
            record.final_approved_at = datetime.now(UTC)
            logger.info(f"最终审核通过 - approved_by: {current_user.id}")
            
        elif new_stage == OrderStage.STAGE_1.value:
            # 退回到第一阶段：允许多种情况
            if original_stage == OrderStage.STAGE_2.value:
                # 销售人员可以将自己的第二阶段订单退回第一阶段
                if record.user_id != current_user.id and not current_user.has_logistics_function():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="只有订单创建者或后勤人员可以退回订单"
                    )
            elif original_stage == OrderStage.STAGE_3.value or original_stage == OrderStage.STAGE_4.value:
                # 后勤人员可以将第三、四阶段退回第一阶段
                if not current_user.has_logistics_function():
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="只有后勤人员可以退回此阶段的订单"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无法从当前阶段退回到第一阶段"
                )
            # 清除审核信息（如果退回到第一阶段）
            record.logistics_approved_by_id = None
            record.logistics_approved_at = None
            record.final_approved_by_id = None
            record.final_approved_at = None
            logger.info("订单退回到第一阶段，清除审核信息")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的阶段变更: {original_stage} -> {new_stage}"
            )
    
    try:
        logger.info("开始提交数据库事务...")
        await db.commit()
        logger.info("数据库事务提交成功")
        
        await db.refresh(record)
        logger.info("记录刷新完成")
        
        # 记录最终状态
        logger.info(f"更新后阶段: {record.stage}")
        
        # 重新查询以确保关联数据被正确加载
        result = await db.execute(
            select(SalesRecord)
            .options(
                joinedload(SalesRecord.user),
                joinedload(SalesRecord.logistics_approved_by),
                joinedload(SalesRecord.final_approved_by),
                joinedload(SalesRecord.attachments)
            )
            .where(SalesRecord.id == record.id)
        )
        final_record = result.unique().scalar_one()
        
        logger.info(f"最终查询结果 - stage: {final_record.stage}")
        if final_record.logistics_approved_by:
            logger.info(f"后勤审核人: {final_record.logistics_approved_by.full_name}")
        if final_record.final_approved_by:
            logger.info(f"最终审核人: {final_record.final_approved_by.full_name}")
        
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
    删除销售记录（同时删除相关附件文件）
    """
    logger.info(f"删除销售记录 - record_id: {record_id}, user_id: {current_user.id}")
    
    # 查询记录及其附件
    result = await db.execute(
        select(SalesRecord)
        .options(joinedload(SalesRecord.attachments))
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        logger.warning(f"要删除的记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    # 确保加载所有属性，避免懒加载问题
    _ = record.order_number
    order_number = record.order_number
    
    # 收集需要删除的附件文件信息
    attachments_to_delete = []
    if record.attachments:
        for attachment in record.attachments:
            attachments_to_delete.append({
                'id': attachment.id,
                'stored_filename': attachment.stored_filename,
                'original_filename': attachment.original_filename
            })
        logger.info(f"记录包含 {len(attachments_to_delete)} 个附件需要清理")
    
    logger.info(f"准备删除记录 - id: {record_id}, order_number: {order_number}")
    
    try:
        # 删除销售记录（会自动删除附件表记录）
        await db.delete(record)
        await db.commit()
        logger.info(f"销售记录删除成功 - id: {record_id}, order_number: {order_number}")
        
        # 删除物理文件
        if attachments_to_delete:
            from app.utils.file_handler import file_handler
            
            for attachment_info in attachments_to_delete:
                try:
                    # 检查文件是否被其他记录引用（防止误删共享文件）
                    result = await db.execute(
                        select(Attachment).where(Attachment.stored_filename == attachment_info['stored_filename'])
                    )
                    if not result.scalar_one_or_none():
                        # 文件没有被其他记录引用，可以安全删除
                        if file_handler.delete_file(attachment_info['stored_filename']):
                            logger.info(f"成功删除附件文件 - {attachment_info['stored_filename']} ({attachment_info['original_filename']})")
                        else:
                            logger.warning(f"删除附件文件失败 - {attachment_info['stored_filename']} ({attachment_info['original_filename']})")
                    else:
                        logger.info(f"附件文件被其他记录引用，跳过删除 - {attachment_info['stored_filename']}")
                except Exception as file_error:
                    logger.error(f"处理附件文件时出错 - {attachment_info['stored_filename']}: {file_error}")
        
        return {"message": "记录及相关附件已删除"}
    except Exception as e:
        logger.error(f"删除记录失败 - id: {record_id}: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除记录失败: {str(e)}"
        ) 