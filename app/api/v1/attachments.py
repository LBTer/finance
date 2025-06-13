import logging
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.core.permissions import Action, check_sales_record_permissions, get_sales_record
from app.models.user import User
from app.models.sales_record import SalesRecord
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentResponse, AttachmentCreate
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


async def validate_and_save_attachments(
    files: List[UploadFile],
    sales_record_id: int,
    db: AsyncSessionDep,
    user_id: int
) -> List[Attachment]:
    """
    验证并保存附件的内部函数
    
    - **files**: 上传的文件列表
    - **sales_record_id**: 销售记录ID
    - **db**: 数据库会话
    - **user_id**: 用户ID（用于日志记录）
    
    Returns:
        List[Attachment]: 创建的附件对象列表
    
    Raises:
        HTTPException: 文件验证失败或保存失败时抛出
    """
    if not files:
        return []
    
    logger.info(f"开始处理附件 - sales_record_id: {sales_record_id}, 文件数量: {len(files)}, user_id: {user_id}")
    
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
                file_md5=file_md5
            )
            
            attachment = Attachment(**attachment_data.model_dump())
            db.add(attachment)
            attachments.append(attachment)
            
            logger.info(f"文件保存成功 - 原文件名: {file.filename}, 存储文件名: {stored_filename}, MD5: {file_md5}")
        
        logger.info(f"所有附件处理完成 - sales_record_id: {sales_record_id}, 成功处理 {len(attachments)} 个文件")
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
@check_sales_record_permissions(Action.UPDATE, lambda db, sales_record_id, **kwargs: get_sales_record(db, sales_record_id, **kwargs))
async def upload_attachments(
    sales_record_id: int,
    files: Annotated[List[UploadFile], File(...)],
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> List[Attachment]:
    """
    上传销售记录的附件
    
    - **sales_record_id**: 销售记录ID
    - **files**: 上传的文件列表
    """
    logger.info(f"开始上传附件 - sales_record_id: {sales_record_id}, 文件数量: {len(files)}, user_id: {current_user.id}")
    
    # 验证销售记录是否存在
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
    
    # 调用内部函数处理附件
    attachments = await validate_and_save_attachments(files, sales_record_id, db, current_user.id)
    
    try:
        await db.commit()
        for attachment in attachments:
            await db.refresh(attachment)
        
        logger.info(f"附件上传完成 - sales_record_id: {sales_record_id}, 成功上传 {len(attachments)} 个文件")
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
    current_user: Annotated[User, Depends(get_current_user)]
) -> List[Attachment]:
    """
    获取销售记录的附件列表
    
    - **sales_record_id**: 销售记录ID
    """
    logger.info(f"获取附件列表 - sales_record_id: {sales_record_id}, user_id: {current_user.id}")
    
    result = await db.execute(
        select(Attachment)
        .where(Attachment.sales_record_id == sales_record_id)
        .order_by(Attachment.created_at.desc())
    )
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
@check_sales_record_permissions(Action.UPDATE, lambda db, attachment_id, **kwargs: get_attachment_sales_record(db, attachment_id))
async def delete_attachment(
    attachment_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict:
    """
    删除附件
    
    - **attachment_id**: 附件ID
    """
    logger.info(f"删除附件 - attachment_id: {attachment_id}, user_id: {current_user.id}")
    
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