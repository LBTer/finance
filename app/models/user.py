from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
import enum

class UserRole(str, enum.Enum):
    """用户角色枚举"""
    NORMAL = "normal"  # 普通用户
    SENIOR = "senior"  # 高级用户
    ADMIN = "admin"    # 超级管理员

class UserFunction(str, enum.Enum):
    """用户职能枚举（仅适用于普通用户）"""
    SALES = "sales"              # 销售用户
    LOGISTICS = "logistics"      # 后勤用户
    SALES_LOGISTICS = "sales_logistics"  # 销售和后勤用户（兼具两种职能）

class User(Base):
    """用户模型"""
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(11), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 用户角色
    role: Mapped[str] = mapped_column(
        String(20),
        default=UserRole.NORMAL.value,
        nullable=False
    )
    
    # 用户职能（仅普通用户需要）
    function: Mapped[str] = mapped_column(
        String(30),
        default=UserFunction.SALES.value,
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
    
    def has_sales_function(self) -> bool:
        """检查用户是否具有销售职能"""
        return self.role in [UserRole.SENIOR.value, UserRole.ADMIN.value] or \
               self.function in [UserFunction.SALES.value, UserFunction.SALES_LOGISTICS.value]
    
    def has_logistics_function(self) -> bool:
        """检查用户是否具有后勤职能"""
        return self.role in [UserRole.SENIOR.value, UserRole.ADMIN.value] or \
               self.function in [UserFunction.LOGISTICS.value, UserFunction.SALES_LOGISTICS.value]
    
    def can_approve_logistics(self) -> bool:
        """检查用户是否可以进行后勤审核（第二阶段 -> 第三阶段）"""
        return self.has_logistics_function()
    
    def can_approve_final(self) -> bool:
        """检查用户是否可以进行最终审核（第四阶段 -> 第五阶段）"""
        return self.role in [UserRole.SENIOR.value, UserRole.ADMIN.value]
    
    def __repr__(self) -> str:
        # 完全避免访问任何可能触发数据库查询的SQLAlchemy属性
        # 使用对象的内存地址来提供唯一标识
        return f"<User at {hex(id(self))}>" 