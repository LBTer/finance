from app.db.base_class import Base
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import Optional
from datetime import datetime


class AuditAction(str, Enum):
    """审计操作类型枚举"""
    CREATE = "create"  # 创建
    UPDATE = "update"  # 更新
    DELETE = "delete"  # 删除
    APPROVE = "approve"  # 审核通过
    REJECT = "reject"  # 审核拒绝
    UPLOAD = "upload"  # 上传附件
    DOWNLOAD = "download"  # 下载附件
    LOGIN = "login"  # 登录
    LOGOUT = "logout"  # 登出


class AuditResourceType(str, Enum):
    """审计资源类型枚举"""
    SALES_RECORD = "sales_record"  # 销售记录
    USER = "user"  # 用户
    ATTACHMENT = "attachment"  # 附件
    SHIPPING_FEES = "shipping_fees"  # 运费
    PROCUREMENT = "procurement"  # 采购
    SYSTEM = "system"  # 系统


class AuditLog(Base):
    """审计日志模型"""
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # 操作用户
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True, index=True)
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    
    # 操作信息
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    # 操作详情
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON格式的详细信息
    
    # 请求信息
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # 支持IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # 操作结果
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, resource_type={self.resource_type})>"