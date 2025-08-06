import logging
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, UTC

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.core.permissions import Action, check_sales_record_permissions, get_sales_record
from app.models.user import User, UserRole
from app.models.sales_record import OrderSource, SalesRecord, OrderStage, OrderType
from app.models.attachment import Attachment, AttachmentType
from app.models.audit_log import AuditAction, AuditResourceType
from app.models.fees import ShippingFees
from app.models.procurement import Procurement
from app.schemas.sales_record import (
    SalesRecordCreate,
    SalesRecordUpdate,
    SalesRecordResponse
)
from app.utils.logger import get_logger
from app.services.audit_service import AuditService

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
    
    - **order_number**: 要检查的订单编号
    
    返回:
    - **available**: 是否可用 (true/false)
    - **message**: 提示信息
    """
    logger.info(f"检查订单编号可用性 - order_number: {order_number}, user_id: {current_user.id}")
    
    existing_record = await db.execute(
        select(SalesRecord).where(SalesRecord.order_number == order_number)
    )
    
    if existing_record.scalar_one_or_none():
        logger.debug(f"订单编号已存在 - {order_number}")
        return {
            "available": False,
            "message": f"订单编号 '{order_number}' 已存在"
        }
    else:
        logger.debug(f"订单编号可用 - {order_number}")
        return {
            "available": True,
            "message": f"订单编号 '{order_number}' 可用"
        }

@router.post("", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.CREATE)
async def create_sales_record(
    *,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    # 表单字段
    order_number: str = Form(...),
    order_type: str = Form(...),
    order_source: str = Form(...),
    product_name: str = Form(...),
    quantity: int = Form(...),
    unit_price: float = Form(...),
    total_price: float = Form(...),
    remarks: Optional[str] = Form(None),
    attachment_type: str = Form(AttachmentType.SALES.value),
    files: Optional[List[UploadFile]] = File(None)
) -> SalesRecord:
    """
    创建销售记录
    
    - **order_number**: 订单编号（唯一标识）
    - **order_type**: 订单类型 (overseas/domestic)
    - **order_source**: 订单来源 (alibaba/domestic/exhibition)
    - **product_name**: 产品名称
    - **quantity**: 数量
    - **unit_price**: 单价（美元）
    - **total_price**: 总价（美元）
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
        logger.warning(f"订单编号重复 - order_number: {order_number}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"订单编号 '{order_number}' 已存在，请使用不同的订单编号"
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
        'exchange_rate': 7.0,  # 默认汇率
        'factory_price': 0.0,  # 默认出厂价格
        'refund_amount': 0.0,  # 默认退款金额
        'tax_refund': 0.0,     # 默认退税金额
        'profit': 0.0,         # 默认利润
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
                joinedload(SalesRecord.attachments),
                joinedload(SalesRecord.shipping_fees),
                joinedload(SalesRecord.procurement)
            )
            .where(SalesRecord.id == record.id)
        )
        final_record = result.unique().scalar_one()
        
        logger.info(f"销售记录创建完成 - id: {final_record.id}, 附件数量: {len(final_record.attachments)}")
        
        # 记录审计日志
        try:
            audit_details = {
                "order_number": final_record.order_number,
                "order_type": final_record.order_type,
                "order_source": final_record.order_source,
                "product_name": final_record.product_name,
                "quantity": final_record.quantity,
                "unit_price": final_record.unit_price,
                "total_price": final_record.total_price,
                "attachments_count": len(final_record.attachments)
            }
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.CREATE,
                resource_type=AuditResourceType.SALES_RECORD,
                resource_id=final_record.id,
                description=f"创建销售记录: {final_record.order_number}",
                details=audit_details,
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
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
    search: str = None
) -> List[SalesRecord]:
    """
    获取销售记录列表（带分页）
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数
    - **stage**: 按阶段筛选 (stage_1/stage_2/stage_3/stage_4/stage_5)
    - **order_type**: 按订单类型筛选 (alibaba/domestic/exhibition)
    - **search**: 搜索订单号或产品名称
    """
    logger.info(f"获取销售记录列表 - user_id: {current_user.id} ({current_user.role}), skip: {skip}, limit: {limit}")
    logger.debug(f"筛选条件 - stage: {stage}, order_type: {order_type}, search: {search}")
    
    query = select(SalesRecord).options(
        joinedload(SalesRecord.user),
        joinedload(SalesRecord.logistics_approved_by),
        joinedload(SalesRecord.final_approved_by),
        joinedload(SalesRecord.attachments),
        joinedload(SalesRecord.shipping_fees),
        joinedload(SalesRecord.procurement)
    )
    
    # 权限控制：所有用户都可以看到所有记录
    logger.debug(f"用户 {current_user.id} ({current_user.role}) 查看所有记录")
    
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
    
    # 搜索
    if search:
        query = query.where(
            or_(
                SalesRecord.order_number.contains(search),
                SalesRecord.product_name.contains(search)
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
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
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
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> SalesRecord:
    """
    更新销售记录基本信息
    
    根据审核逻辑，只有在特定阶段和特定权限下才能更新记录：
    - 阶段一：只有创建记录的本人可以修改
    - 阶段二：谁也不能修改
    - 阶段三：具有后勤职能的人可以修改数据
    - 阶段四：谁也不能修改
    - 阶段五：不能修改
    
    注意：阶段变更请使用专门的提交/审核/撤回接口
    """
    logger.info(f"更新销售记录 - record_id: {record_id}, user_id: {current_user.id}")
    
    # 查询记录
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
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
    
    logger.info(f"记录当前阶段: {record.stage}")
    
    # 确保在此处已加载完所有必要属性
    _ = record.order_number  # 预先加载order_number属性，避免后续延迟加载
    
    # 更新记录基本信息
    update_data = record_in.model_dump(exclude_unset=True)
    
    # 不允许通过更新接口修改阶段
    if 'stage' in update_data:
        logger.warning(f"尝试通过更新接口修改阶段 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能通过更新接口修改阶段，请使用专门的提交/审核/撤回接口"
        )
    
    logger.debug(f"准备更新的字段: {update_data}")
    
    # 处理factory_price为None的情况，确保数据库约束不被违反
    if 'factory_price' in update_data and update_data['factory_price'] is None:
        logger.debug("factory_price为None，跳过更新该字段")
        update_data.pop('factory_price')
    
    try:
        for field, value in update_data.items():
            logger.debug(f"设置字段 {field}: {getattr(record, field, '未设置')} -> {value}")
            setattr(record, field, value)
        
        await db.commit()
        await db.refresh(record)
        
        # 重新预加载所有需要的关系以避免懒加载
        result = await db.execute(
            select(SalesRecord)
            .options(
                joinedload(SalesRecord.user),
                joinedload(SalesRecord.logistics_approved_by),
                joinedload(SalesRecord.final_approved_by),
                joinedload(SalesRecord.attachments),
                joinedload(SalesRecord.shipping_fees),
                joinedload(SalesRecord.procurement)
            )
            .where(SalesRecord.id == record_id)
        )
        record = result.unique().scalar_one()
        
        logger.info(f"销售记录更新成功 - record_id: {record_id}")
        
        # 记录审计日志
        try:
            audit_details = {
                "updated_fields": list(update_data.keys()),
                "changes": update_data,
                "order_number": record.order_number
            }
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.UPDATE,
                resource_type=AuditResourceType.SALES_RECORD,
                resource_id=record_id,
                description=f"更新销售记录: {record.order_number}",
                details=audit_details,
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
        return record
        
    except Exception as e:
        await db.rollback()
        logger.error(f"更新销售记录失败 - record_id: {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新记录失败: {str(e)}"
        )

@router.delete("/{record_id}")
@check_sales_record_permissions(Action.DELETE, get_sales_record)
async def delete_sales_record(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
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
        
        # 记录审计日志
        try:
            audit_details = {
                "order_number": order_number,
                "deleted_attachments_count": len(attachments_to_delete)
            }
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.DELETE,
                resource_type=AuditResourceType.SALES_RECORD,
                resource_id=record_id,
                description=f"删除销售记录: {order_number}",
                details=audit_details,
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
        return {"message": "记录及相关附件已删除"}
    except Exception as e:
        logger.error(f"删除记录失败 - id: {record_id}: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除记录失败: {str(e)}"
        )

@router.post("/{record_id}/submit", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.SUBMIT, get_sales_record)
async def submit_sales_record(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> SalesRecord:
    """
    提交销售记录到下一阶段
    
    - 阶段一 -> 阶段二：销售人员提交自己的记录进行初步审核
    - 阶段三 -> 阶段四：后勤人员提交记录进行最终审核
    """
    logger.info(f"提交销售记录到下一阶段 - record_id: {record_id}, user_id: {current_user.id}")
    
    # 查询记录
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    current_stage = record.stage
    
    try:
        if current_stage == OrderStage.STAGE_1.value:
            # 阶段一 -> 阶段二：销售人员提交待初步审核
            if record.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只能提交自己创建的销售记录"
                )
            record.stage = OrderStage.STAGE_2.value
            logger.info(f"销售记录从阶段一提交到阶段二 - record_id: {record_id}")
            
        elif current_stage == OrderStage.STAGE_3.value:
            # 阶段三 -> 阶段四：后勤人员提交待最终审核
            if not current_user.has_logistics_function():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有具有后勤职能的用户可以提交此阶段的记录"
                )
            record.stage = OrderStage.STAGE_4.value
            logger.info(f"销售记录从阶段三提交到阶段四 - record_id: {record_id}")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"记录当前处于阶段 {current_stage}，无法提交到下一阶段"
            )
        
        await db.commit()
        await db.refresh(record)
        
        # 重新预加载所有需要的关系以避免懒加载
        result = await db.execute(
            select(SalesRecord)
            .options(
                joinedload(SalesRecord.user),
                joinedload(SalesRecord.logistics_approved_by),
                joinedload(SalesRecord.final_approved_by),
                joinedload(SalesRecord.attachments),
                joinedload(SalesRecord.shipping_fees),
                joinedload(SalesRecord.procurement)
            )
            .where(SalesRecord.id == record_id)
        )
        record = result.unique().scalar_one()
        
        logger.info(f"销售记录提交成功 - record_id: {record_id}, new_stage: {record.stage}")
        
        # 记录审计日志
        try:
            audit_details = {
                "order_number": record.order_number,
                "previous_stage": current_stage,
                "new_stage": record.stage,
                "stage_transition": f"{current_stage} -> {record.stage}"
            }
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.SUBMIT,
                resource_type=AuditResourceType.SALES_RECORD,
                resource_id=record_id,
                description=f"提交销售记录: {record.order_number} (阶段 {current_stage} -> {record.stage})",
                details=audit_details,
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
        return record
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"提交销售记录失败 - record_id: {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交记录失败: {str(e)}"
        )

@router.post("/{record_id}/approve", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.APPROVE, get_sales_record)
async def approve_sales_record(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> SalesRecord:
    """
    审核通过销售记录
    
    - 阶段二 -> 阶段三：后勤人员初步审核通过
    - 阶段四 -> 阶段五：高级用户/超级管理员最终审核通过
    """
    logger.info(f"审核销售记录 - record_id: {record_id}, user_id: {current_user.id}")
    
    # 查询记录
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    current_stage = record.stage
    
    try:
        if current_stage == OrderStage.STAGE_2.value:
            # 阶段二 -> 阶段三：后勤人员初步审核通过
            if not current_user.has_logistics_function():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有具有后勤职能的用户可以进行初步审核"
                )
            record.stage = OrderStage.STAGE_3.value
            record.logistics_approved_by_id = current_user.id
            record.logistics_approved_at = datetime.now(UTC)
            logger.info(f"后勤人员初步审核通过 - record_id: {record_id}, approved_by: {current_user.id}")
            
        elif current_stage == OrderStage.STAGE_4.value:
            # 阶段四 -> 阶段五：高级用户/超级管理员最终审核通过
            if not current_user.can_approve_final():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有高级用户或超级管理员可以进行最终审核"
                )
            record.stage = OrderStage.STAGE_5.value
            record.final_approved_by_id = current_user.id
            record.final_approved_at = datetime.now(UTC)
            logger.info(f"最终审核通过 - record_id: {record_id}, approved_by: {current_user.id}")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"记录当前处于阶段 {current_stage}，无法进行审核操作"
            )
        
        await db.commit()
        await db.refresh(record)
        
        # 重新预加载所有需要的关系以避免懒加载
        result = await db.execute(
            select(SalesRecord)
            .options(
                joinedload(SalesRecord.user),
                joinedload(SalesRecord.logistics_approved_by),
                joinedload(SalesRecord.final_approved_by),
                joinedload(SalesRecord.attachments),
                joinedload(SalesRecord.shipping_fees),
                joinedload(SalesRecord.procurement)
            )
            .where(SalesRecord.id == record_id)
        )
        record = result.unique().scalar_one()
        
        logger.info(f"销售记录审核成功 - record_id: {record_id}, new_stage: {record.stage}")
        
        # 记录审计日志
        try:
            audit_details = {
                "order_number": record.order_number,
                "previous_stage": current_stage,
                "new_stage": record.stage,
                "approval_type": "logistics" if current_stage == OrderStage.STAGE_2.value else "final",
                "stage_transition": f"{current_stage} -> {record.stage}"
            }
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.APPROVE,
                resource_type=AuditResourceType.SALES_RECORD,
                resource_id=record_id,
                description=f"审核通过销售记录: {record.order_number} (阶段 {current_stage} -> {record.stage})",
                details=audit_details,
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
        return record
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"审核销售记录失败 - record_id: {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"审核记录失败: {str(e)}"
        )

@router.post("/{record_id}/withdraw", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.WITHDRAW, get_sales_record)
async def withdraw_sales_record(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> SalesRecord:
    """
    撤回销售记录到指定阶段
    
    - 阶段二 -> 阶段一：创建记录的本人可以撤回
    - 阶段三 -> 阶段一：后勤职能的人可以撤回
    - 阶段四 -> 阶段三：后勤职能的人可以撤回
    - 阶段五 -> 阶段三：只有高级用户/超级用户可以撤回
    """
    logger.info(f"撤回销售记录 - record_id: {record_id}, user_id: {current_user.id}")
    
    # 查询记录
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记录不存在"
        )
    
    current_stage = record.stage
    
    try:
        if current_stage == OrderStage.STAGE_2.value:
            # 阶段二 -> 阶段一：创建记录的本人可以撤回
            if record.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有创建记录的本人可以撤回阶段二的记录"
                )
            record.stage = OrderStage.STAGE_1.value
            logger.info(f"销售记录从阶段二撤回到阶段一 - record_id: {record_id}")
            
        elif current_stage == OrderStage.STAGE_3.value:
            # 阶段三 -> 阶段一：后勤职能的人可以撤回
            if not current_user.has_logistics_function():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有具有后勤职能的用户可以撤回阶段三的记录"
                )
            record.stage = OrderStage.STAGE_1.value
            # 清除后勤审核信息
            record.logistics_approved_by_id = None
            record.logistics_approved_at = None
            logger.info(f"销售记录从阶段三撤回到阶段一 - record_id: {record_id}")
            
        elif current_stage == OrderStage.STAGE_4.value:
            # 阶段四 -> 阶段三：后勤职能的人可以撤回
            if not current_user.has_logistics_function():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有具有后勤职能的用户可以撤回阶段四的记录"
                )
            record.stage = OrderStage.STAGE_3.value
            logger.info(f"销售记录从阶段四撤回到阶段三 - record_id: {record_id}")
            
        elif current_stage == OrderStage.STAGE_5.value:
            # 阶段五 -> 阶段三：只有高级用户/超级用户可以撤回
            if not current_user.can_approve_final():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="只有高级用户或超级管理员可以撤回阶段五的记录"
                )
            record.stage = OrderStage.STAGE_3.value
            # 清除最终审核信息
            record.final_approved_by_id = None
            record.final_approved_at = None
            logger.info(f"销售记录从阶段五撤回到阶段三 - record_id: {record_id}")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"记录当前处于阶段 {current_stage}，无法进行撤回操作"
            )
        
        await db.commit()
        await db.refresh(record)
        
        # 重新预加载所有需要的关系以避免懒加载
        result = await db.execute(
            select(SalesRecord)
            .options(
                joinedload(SalesRecord.user),
                joinedload(SalesRecord.logistics_approved_by),
                joinedload(SalesRecord.final_approved_by),
                joinedload(SalesRecord.attachments),
                joinedload(SalesRecord.shipping_fees),
                joinedload(SalesRecord.procurement)
            )
            .where(SalesRecord.id == record_id)
        )
        record = result.unique().scalar_one()
        
        logger.info(f"销售记录撤回成功 - record_id: {record_id}, new_stage: {record.stage}")
        
        # 记录审计日志
        try:
            audit_details = {
                "order_number": record.order_number,
                "previous_stage": current_stage,
                "new_stage": record.stage,
                "stage_transition": f"{current_stage} -> {record.stage}",
                "cleared_approvals": []
            }
            
            # 记录清除的审核信息
            if current_stage == OrderStage.STAGE_3.value:
                audit_details["cleared_approvals"].append("logistics_approval")
            elif current_stage == OrderStage.STAGE_5.value:
                audit_details["cleared_approvals"].append("final_approval")
            
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.WITHDRAW,
                resource_type=AuditResourceType.SALES_RECORD,
                resource_id=record_id,
                description=f"撤回销售记录: {record.order_number} (阶段 {current_stage} -> {record.stage})",
                details=audit_details,
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
        return record
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"撤回销售记录失败 - record_id: {record_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤回记录失败: {str(e)}"
        )

@router.post("/{record_id}/void", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.VOID, get_sales_record)
async def void_sales_record(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> SalesRecord:
    """
    作废销售记录
    
    - **record_id**: 销售记录ID
    
    作废后的记录将被标记为作废状态，但不会被删除
    """
    logger.info(f"作废销售记录 - record_id: {record_id}, user_id: {current_user.id}")
    
    # 获取销售记录
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        logger.warning(f"销售记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售记录不存在"
        )
    
    # 检查是否已经作废
    if hasattr(record, 'is_voided') and record.is_voided:
        logger.warning(f"销售记录已经作废 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="销售记录已经作废"
        )
    
    # 设置作废状态
    if hasattr(record, 'is_voided'):
        record.is_voided = True
    record.updated_at = datetime.now(UTC)
    
    # 同时作废关联的运费记录
    if record.shipping_fees:
        for shipping_fee in record.shipping_fees:
            shipping_fee.is_voided = True
            shipping_fee.updated_at = datetime.now(UTC)
    
    # 同时作废关联的采购记录
    if record.procurement:
        for procurement in record.procurement:
            procurement.is_voided = True
            procurement.updated_at = datetime.now(UTC)
    
    await db.commit()
    await db.refresh(record)
    
    # 重新查询以获取完整的关联数据
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
        )
        .where(SalesRecord.id == record_id)
    )
    final_record = result.unique().scalar_one()
    
    # 记录审计日志
    try:
        # 统计关联记录数量
        shipping_fees_count = len(final_record.shipping_fees) if final_record.shipping_fees else 0
        procurement_count = len(final_record.procurement) if final_record.procurement else 0
        
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            resource_type=AuditResourceType.SALES_RECORD,
            resource_id=record_id,
            description="作废销售记录及关联记录",
            details={
                "record_id": record_id,
                "order_number": final_record.order_number,
                "action": "void",
                "previous_voided_status": False,
                "new_voided_status": True,
                "affected_shipping_fees": shipping_fees_count,
                "affected_procurement": procurement_count
            },
            request=request
        )
    except Exception as audit_error:
        logger.warning(f"记录审计日志失败: {audit_error}")
    
    logger.info(f"销售记录及关联记录作废成功 - record_id: {record_id}, 运费记录: {len(final_record.shipping_fees) if final_record.shipping_fees else 0}条, 采购记录: {len(final_record.procurement) if final_record.procurement else 0}条")
    return final_record

@router.post("/{record_id}/unvoid", response_model=SalesRecordResponse)
@check_sales_record_permissions(Action.UNVOID, get_sales_record)
async def unvoid_sales_record(
    record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> SalesRecord:
    """
    取消作废销售记录
    
    - **record_id**: 销售记录ID
    
    取消作废后的记录将恢复正常状态
    """
    logger.info(f"取消作废销售记录 - record_id: {record_id}, user_id: {current_user.id}")
    
    # 获取销售记录
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
        )
        .where(SalesRecord.id == record_id)
    )
    record = result.unique().scalar_one_or_none()
    
    if not record:
        logger.warning(f"销售记录不存在 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售记录不存在"
        )
    
    # 检查是否已经取消作废
    if not hasattr(record, 'is_voided') or not record.is_voided:
        logger.warning(f"销售记录未作废，无需取消 - record_id: {record_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="销售记录未作废，无需取消"
        )
    
    # 取消作废状态
    record.is_voided = False
    record.updated_at = datetime.now(UTC)
    
    # 同时取消作废关联的运费记录
    if record.shipping_fees:
        for shipping_fee in record.shipping_fees:
            shipping_fee.is_voided = False
            shipping_fee.updated_at = datetime.now(UTC)
    
    # 同时取消作废关联的采购记录
    if record.procurement:
        for procurement in record.procurement:
            procurement.is_voided = False
            procurement.updated_at = datetime.now(UTC)
    
    await db.commit()
    await db.refresh(record)
    
    # 重新查询以获取完整的关联数据
    result = await db.execute(
        select(SalesRecord)
        .options(
            joinedload(SalesRecord.user),
            joinedload(SalesRecord.logistics_approved_by),
            joinedload(SalesRecord.final_approved_by),
            joinedload(SalesRecord.attachments),
            joinedload(SalesRecord.shipping_fees),
            joinedload(SalesRecord.procurement)
        )
        .where(SalesRecord.id == record_id)
    )
    final_record = result.unique().scalar_one()
    
    # 记录审计日志
    try:
        # 统计关联记录数量
        shipping_fees_count = len(final_record.shipping_fees) if final_record.shipping_fees else 0
        procurement_count = len(final_record.procurement) if final_record.procurement else 0
        
        await AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action=AuditAction.UPDATE,
            resource_type=AuditResourceType.SALES_RECORD,
            resource_id=record_id,
            description="取消作废销售记录及关联记录",
            details={
                "record_id": record_id,
                "order_number": final_record.order_number,
                "action": "unvoid",
                "previous_voided_status": True,
                "new_voided_status": False,
                "affected_shipping_fees": shipping_fees_count,
                "affected_procurement": procurement_count
            },
            request=request
        )
    except Exception as audit_error:
        logger.warning(f"记录审计日志失败: {audit_error}")
    
    logger.info(f"销售记录及关联记录取消作废成功 - record_id: {record_id}, 运费记录: {len(final_record.shipping_fees) if final_record.shipping_fees else 0}条, 采购记录: {len(final_record.procurement) if final_record.procurement else 0}条")
    return final_record