from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, ForeignKey, Enum as SQLAlchemyEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
import enum

class SalesStatus(str, enum.Enum):
    """销售记录状态枚举"""
    PENDING = "pending"      # 待审核
    APPROVED = "approved"    # 已审核
    REJECTED = "rejected"    # 已拒绝

class SalesRecord(Base):
    """销售记录模型"""
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    
    # 外键关联
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="sales_records")
    
    # 销售信息
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    
    # 费用信息
    shipping_fee: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    refund_amount: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    tax_refund: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    
    # 状态
    status: Mapped[SalesStatus] = mapped_column(
        SQLAlchemyEnum(SalesStatus),
        default=SalesStatus.PENDING,
        nullable=False
    )
    
    # 备注
    remarks: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # 审核信息
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    approved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_id],
        remote_side="User.id"
    )
    
    @property
    def total_amount(self) -> float:
        """计算总金额"""
        return self.quantity * self.unit_price + self.shipping_fee - self.refund_amount - self.tax_refund
    
    def __repr__(self) -> str:
        return f"<SalesRecord {self.order_number}>" 