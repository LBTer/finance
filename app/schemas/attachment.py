from typing import Optional
from pydantic import Field
from .base import BaseSchema, TimestampSchema


class AttachmentBase(BaseSchema):
    """附件基础Schema"""
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    content_type: str = Field(..., min_length=1, max_length=100)


class AttachmentCreate(AttachmentBase):
    """附件创建Schema"""
    sales_record_id: int = Field(..., gt=0)
    stored_filename: str = Field(..., min_length=1, max_length=255)
    file_md5: str = Field(..., min_length=32, max_length=32)


class AttachmentInDBBase(AttachmentBase, TimestampSchema):
    """数据库中的附件Schema基类"""
    id: int
    sales_record_id: int
    stored_filename: str
    file_md5: str


class AttachmentInDB(AttachmentInDBBase):
    """数据库中的附件Schema"""
    pass


class AttachmentResponse(AttachmentInDBBase):
    """附件响应Schema"""
    
    class Config:
        from_attributes = True 