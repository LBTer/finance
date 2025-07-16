from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.base import BaseSchema, TimestampSchema
from app.models.audit_log import AuditAction, AuditResourceType


class AuditLogBase(BaseSchema):
    """审计日志基础Schema"""
    action: str = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[int] = Field(None, description="资源ID")
    description: str = Field(..., max_length=500, description="操作描述")
    details: Optional[str] = Field(None, description="详细信息（JSON格式）")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP地址")
    user_agent: Optional[str] = Field(None, max_length=500, description="用户代理")
    success: bool = Field(default=True, description="操作是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")


class AuditLogCreate(AuditLogBase):
    """审计日志创建Schema"""
    user_id: Optional[int] = Field(None, description="操作用户ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "action": AuditAction.CREATE.value,
                "resource_type": AuditResourceType.SALES_RECORD.value,
                "resource_id": 123,
                "description": "创建销售记录",
                "details": '{"order_number": "ORD20240101001", "product_name": "锻造轮"}',
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "success": True
            }
        }


class AuditLogUpdate(BaseSchema):
    """审计日志更新Schema（通常审计日志不允许更新）"""
    pass


class AuditLogInDBBase(AuditLogBase, TimestampSchema):
    """数据库中的审计日志Schema基类"""
    id: int
    user_id: Optional[int] = None


class AuditLogInDB(AuditLogInDBBase):
    """数据库中的审计日志Schema"""
    pass


class AuditLogResponse(AuditLogInDBBase):
    """审计日志响应Schema"""
    user_name: Optional[str] = Field(None, description="操作用户姓名")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "user_name": "张三",
                "action": AuditAction.CREATE.value,
                "resource_type": AuditResourceType.SALES_RECORD.value,
                "resource_id": 123,
                "description": "创建销售记录",
                "details": '{"order_number": "ORD20240101001", "product_name": "锻造轮"}',
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "success": True,
                "error_message": None,
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        }


class AuditLogQuery(BaseSchema):
    """审计日志查询Schema"""
    user_id: Optional[int] = Field(None, description="用户ID")
    action: Optional[str] = Field(None, description="操作类型")
    resource_type: Optional[str] = Field(None, description="资源类型")
    resource_id: Optional[int] = Field(None, description="资源ID")
    success: Optional[bool] = Field(None, description="操作是否成功")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")