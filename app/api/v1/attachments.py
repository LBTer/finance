import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.core.permissions import Action, check_sales_record_permissions, get_sales_record
from app.models.user import User
from app.models.sales_record import SalesRecord
from app.models.attachment import Attachment, AttachmentType
from app.models.audit_log import AuditAction, AuditResourceType
from app.schemas.attachment import AttachmentResponse, AttachmentCreate
from app.services.audit_service import AuditService
from app.utils.file_handler import file_handler
from app.utils.logger import get_logger

# 获取当前模块的logger
logger = get_logger(__name__)

router = APIRouter(prefix="/attachments", tags=["文件附件"])

# 允许上传的文件类型
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv"
}

# 最大文件大小：10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# 每个销售记录最大附件数量
MAX_ATTACHMENTS_PER_RECORD = 20


async def validate_and_save_attachments(
    files: List[UploadFile],
    sales_record_id: int,
    attachment_type: str,
    db: AsyncSessionDep,
    user_id: int
) -> List[Attachment]:
    """
    验证并保存附件的内部函数
    
    - **files**: 上传的文件列表
    - **sales_record_id**: 销售记录ID
    - **attachment_type**: 附件类型 (sales/logistics)
    - **db**: 数据库会话
    - **user_id**: 用户ID（用于日志记录）
    
    Returns:
        List[Attachment]: 创建的附件对象列表
    
    Raises:
        HTTPException: 文件验证失败或保存失败时抛出
    """
    if not files:
        return []
    
    # 验证附件类型
    if attachment_type not in [AttachmentType.SALES.value, AttachmentType.LOGISTICS.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的附件类型: {attachment_type}"
        )
    
    logger.info(f"开始处理附件 - sales_record_id: {sales_record_id}, 附件类型: {attachment_type}, 文件数量: {len(files)}, user_id: {user_id}")
    
    # 检查当前销售记录的附件数量
    result = await db.execute(
        select(Attachment).where(Attachment.sales_record_id == sales_record_id)
    )
    current_attachments = result.scalars().all()
    current_count = len(current_attachments)
    
    # 检查附件数量限制
    total_after_upload = current_count + len(files)
    if total_after_upload > MAX_ATTACHMENTS_PER_RECORD:
        allowed_count = MAX_ATTACHMENTS_PER_RECORD - current_count
        if allowed_count <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"每个销售记录最多只能有{MAX_ATTACHMENTS_PER_RECORD}个附件，当前已有{current_count}个"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"每个销售记录最多只能有{MAX_ATTACHMENTS_PER_RECORD}个附件，当前已有{current_count}个，只能再上传{allowed_count}个"
            )
    
    # 验证所有文件
    for file in files:
        # 检查文件大小
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件 {file.filename} 太大，最大允许 {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # 检查文件类型
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"不支持的文件类型: {file.content_type}"
            )
    
    # 保存文件并创建附件记录
    attachments = []
    saved_files = []  # 跟踪已保存的文件，用于错误回滚
    
    try:
        for file in files:
            # 保存文件
            file_md5, stored_filename, file_size = await file_handler.save_upload_file(file)
            saved_files.append(stored_filename)
            
            # 创建附件记录
            attachment_data = AttachmentCreate(
                sales_record_id=sales_record_id,
                original_filename=file.filename,
                stored_filename=stored_filename,
                file_size=file_size,
                content_type=file.content_type,
                file_md5=file_md5,
                attachment_type=attachment_type
            )
            
            attachment = Attachment(**attachment_data.model_dump())
            db.add(attachment)
            attachments.append(attachment)
            
            logger.info(f"文件保存成功 - 原文件名: {file.filename}, 存储文件名: {stored_filename}, 附件类型: {attachment_type}, MD5: {file_md5}")
        
        logger.info(f"所有附件处理完成 - sales_record_id: {sales_record_id}, 附件类型: {attachment_type}, 成功处理 {len(attachments)} 个文件")
        return attachments
    
    except Exception as e:
        logger.error(f"保存附件失败: {str(e)}", exc_info=True)
        
        # 清理已保存的文件
        for stored_filename in saved_files:
            try:
                # 检查文件是否被其他记录引用
                result = await db.execute(
                    select(Attachment).where(Attachment.stored_filename == stored_filename)
                )
                if not result.scalar_one_or_none():
                    file_handler.delete_file(stored_filename)
                    logger.info(f"清理：删除未被引用的文件 - {stored_filename}")
                else:
                    logger.info(f"清理：文件被其他记录引用，不删除 - {stored_filename}")
            except Exception as cleanup_error:
                logger.warning(f"清理文件时出错: {cleanup_error}")
        
        # 重新抛出原始异常
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存附件失败: {str(e)}"
            )


@router.post("/upload/{sales_record_id}", response_model=List[AttachmentResponse])
async def upload_attachments(
    sales_record_id: int,
    attachment_type: Annotated[str, Form()],
    files: Annotated[List[UploadFile], File(...)],
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> List[Attachment]:
    """
    上传销售记录的附件
    
    - **sales_record_id**: 销售记录ID
    - **attachment_type**: 附件类型 (sales: 销售附件, logistics: 后勤附件)
    - **files**: 上传的文件列表
    
    权限要求：
    - 销售附件：只能在阶段一且是创建者本人上传
    - 后勤附件：只能在阶段三且具有后勤职能的人上传
    """
    logger.info(f"开始上传附件 - sales_record_id: {sales_record_id}, 附件类型: {attachment_type}, 文件数量: {len(files)}, user_id: {current_user.id}")
    
    # 验证销售记录是否存在并获取详细信息
    result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == sales_record_id)
    )
    sales_record = result.scalar_one_or_none()
    
    if not sales_record:
        logger.warning(f"销售记录不存在 - sales_record_id: {sales_record_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售记录不存在"
        )
    
    # 验证附件类型并检查权限
    from app.core.permissions import SalesRecordPermission, Action
    
    permission_checker = SalesRecordPermission(current_user)
    
    if attachment_type == AttachmentType.SALES.value:
        # 检查销售附件管理权限
        has_permission = await permission_checker.has_permission(Action.MANAGE_SALES_ATTACHMENT, sales_record)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="销售附件只能在阶段一且由创建者本人上传"
            )
    elif attachment_type == AttachmentType.LOGISTICS.value:
        # 检查后勤附件管理权限
        has_permission = await permission_checker.has_permission(Action.MANAGE_LOGISTICS_ATTACHMENT, sales_record)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="后勤附件只能在阶段三且由具有后勤职能的人上传"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的附件类型: {attachment_type}"
        )
    
    # 调用内部函数处理附件
    attachments = await validate_and_save_attachments(files, sales_record_id, attachment_type, db, current_user.id)
    
    try:
        await db.commit()
        for attachment in attachments:
            await db.refresh(attachment)
        
        # 记录审计日志
        try:
            file_names = [att.original_filename for att in attachments]
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.CREATE,
                resource_type=AuditResourceType.ATTACHMENT,
                resource_id=sales_record_id,
                description=f"上传{attachment_type}附件",
                details={
                    "attachment_type": attachment_type,
                    "file_count": len(attachments),
                    "file_names": file_names,
                    "sales_record_id": sales_record_id
                },
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
        logger.info(f"附件上传完成 - sales_record_id: {sales_record_id}, 附件类型: {attachment_type}, 成功上传 {len(attachments)} 个文件")
        return attachments
    
    except Exception as e:
        logger.error(f"保存附件记录失败: {str(e)}", exc_info=True)
        await db.rollback()
        
        # 清理已保存的文件
        for attachment in attachments:
            try:
                # 检查文件是否被其他记录引用
                result = await db.execute(
                    select(Attachment).where(Attachment.stored_filename == attachment.stored_filename)
                )
                if not result.scalar_one_or_none():
                    file_handler.delete_file(attachment.stored_filename)
                    logger.info(f"回滚：删除未被引用的文件 - {attachment.stored_filename}")
                else:
                    logger.info(f"回滚：文件被其他记录引用，不删除 - {attachment.stored_filename}")
            except Exception as cleanup_error:
                logger.warning(f"清理文件时出错: {cleanup_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="保存附件记录失败"
        )


@router.get("/{sales_record_id}", response_model=List[AttachmentResponse])
@check_sales_record_permissions(Action.READ, lambda db, sales_record_id, **kwargs: get_sales_record(db, sales_record_id, **kwargs))
async def get_attachments(
    sales_record_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    attachment_type: str = None
) -> List[Attachment]:
    """
    获取销售记录的附件列表
    
    - **sales_record_id**: 销售记录ID
    - **attachment_type**: 可选，按附件类型过滤 (sales: 销售附件, logistics: 后勤附件)
    """
    logger.info(f"获取附件列表 - sales_record_id: {sales_record_id}, attachment_type: {attachment_type}, user_id: {current_user.id}")
    
    # 构建查询条件
    query = select(Attachment).where(Attachment.sales_record_id == sales_record_id)
    
    # 如果指定了附件类型，添加过滤条件
    if attachment_type:
        if attachment_type not in [AttachmentType.SALES.value, AttachmentType.LOGISTICS.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的附件类型: {attachment_type}"
            )
        query = query.where(Attachment.attachment_type == attachment_type)
    
    query = query.order_by(Attachment.created_at.desc())
    
    result = await db.execute(query)
    attachments = result.scalars().all()
    
    logger.info(f"查询到 {len(attachments)} 个附件")
    return attachments


@router.get("/download/{attachment_id}")
@check_sales_record_permissions(Action.READ, lambda db, attachment_id, **kwargs: get_attachment_sales_record(db, attachment_id))
async def download_attachment(
    attachment_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> FileResponse:
    """
    下载附件
    
    - **attachment_id**: 附件ID
    """
    logger.info(f"下载附件 - attachment_id: {attachment_id}, user_id: {current_user.id}")
    
    # 获取附件信息
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        logger.warning(f"附件不存在 - attachment_id: {attachment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在"
        )
    
    # 检查文件是否存在
    if not file_handler.file_exists(attachment.stored_filename):
        logger.error(f"文件不存在 - stored_filename: {attachment.stored_filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    file_path = file_handler.get_file_path(attachment.stored_filename)
    
    logger.info(f"开始下载文件 - 原文件名: {attachment.original_filename}, 存储文件名: {attachment.stored_filename}")
    
    return FileResponse(
        path=str(file_path),
        filename=attachment.original_filename,
        media_type=attachment.content_type
    )


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request
) -> dict:
    """
    删除附件
    
    - **attachment_id**: 附件ID
    
    权限要求：
    - 销售附件：只能在阶段一且由创建者本人删除
    - 后勤附件：只能在阶段三且由具有后勤职能的人删除
    """
    logger.info(f"删除附件 - attachment_id: {attachment_id}, user_id: {current_user.id}")
    
    # 获取附件信息和关联的销售记录
    result = await db.execute(
        select(Attachment, SalesRecord)
        .join(SalesRecord, Attachment.sales_record_id == SalesRecord.id)
        .where(Attachment.id == attachment_id)
    )
    attachment_record = result.first()
    
    if not attachment_record:
        logger.warning(f"附件不存在 - attachment_id: {attachment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在"
        )
    
    attachment, sales_record = attachment_record
    
    # 验证权限
    from app.core.permissions import SalesRecordPermission, Action
    
    permission_checker = SalesRecordPermission(current_user)
    
    if attachment.attachment_type == AttachmentType.SALES.value:
        # 检查销售附件管理权限
        has_permission = await permission_checker.has_permission(Action.MANAGE_SALES_ATTACHMENT, sales_record)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="销售附件只能在阶段一且由创建者本人删除"
            )
    elif attachment.attachment_type == AttachmentType.LOGISTICS.value:
        # 检查后勤附件管理权限
        has_permission = await permission_checker.has_permission(Action.MANAGE_LOGISTICS_ATTACHMENT, sales_record)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="后勤附件只能在阶段三且由具有后勤职能的人删除"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的附件类型: {attachment.attachment_type}"
        )
    
    stored_filename = attachment.stored_filename
    original_filename = attachment.original_filename
    
    try:
        # 删除数据库记录
        await db.execute(delete(Attachment).where(Attachment.id == attachment_id))
        await db.commit()
        
        # 删除文件（如果没有其他记录引用此文件）
        result = await db.execute(
            select(Attachment).where(Attachment.stored_filename == stored_filename)
        )
        if not result.scalar_one_or_none():
            file_handler.delete_file(stored_filename)
            logger.info(f"文件已删除 - stored_filename: {stored_filename}")
        else:
            logger.info(f"文件仍被其他记录引用，不删除 - stored_filename: {stored_filename}")
        
        # 记录审计日志
        try:
            await AuditService.log_action(
                db=db,
                user_id=current_user.id,
                action=AuditAction.DELETE,
                resource_type=AuditResourceType.ATTACHMENT,
                resource_id=attachment_id,
                description=f"删除{attachment.attachment_type}附件",
                details={
                    "attachment_id": attachment_id,
                    "attachment_type": attachment.attachment_type,
                    "original_filename": original_filename,
                    "sales_record_id": attachment.sales_record_id
                },
                request=request
            )
        except Exception as audit_error:
            logger.warning(f"记录审计日志失败: {audit_error}")
        
        logger.info(f"附件删除成功 - attachment_id: {attachment_id}, 原文件名: {original_filename}")
        return {"message": f"附件 {original_filename} 已删除"}
    
    except Exception as e:
        logger.error(f"删除附件失败 - attachment_id: {attachment_id}: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除附件失败"
        )


async def get_attachment_sales_record(db, attachment_id: int) -> SalesRecord:
    """通过附件ID获取对应的销售记录（用于权限检查）"""
    result = await db.execute(
        select(SalesRecord)
        .join(Attachment, SalesRecord.id == Attachment.sales_record_id)
        .where(Attachment.id == attachment_id)
    )
    return result.scalar_one_or_none()