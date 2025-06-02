from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
import enum

class UserRole(str, enum.Enum):
    """用户角色枚举"""
    NORMAL = "normal"  # 普通用户
    SENIOR = "senior"  # 高级用户
    ADMIN = "admin"    # 超级管理员

class User(Base):
    """用户模型"""
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(11), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 用户角色
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole),
        default=UserRole.NORMAL,
        nullable=False
    )
    
    # 用户状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 关系
    sales_records: Mapped[List["SalesRecord"]] = relationship(
        "SalesRecord",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="SalesRecord.user_id"
    )
    
    def __repr__(self) -> str:
        # 完全避免访问任何可能触发数据库查询的SQLAlchemy属性
        # 使用对象的内存地址来提供唯一标识
        return f"<User at {hex(id(self))}>" 