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
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
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
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>" 