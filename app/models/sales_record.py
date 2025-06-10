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
    """销售记录模型 - 美金订单"""
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    
    # 外键关联
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="sales_records",
        foreign_keys=[user_id]
    )
    
    # 销售信息
    # 产品名称
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 类别
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    # 数量
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # 单价（美元）
    unit_price: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    # 总价（美元）
    total_price: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    # 汇率（美元-人民币）
    exchange_rate: Mapped[float] = mapped_column(Float(precision=4), nullable=False, default=7.0)
    
    
    # 费用信息
    # 运费（陆内）- 人民币
    domestic_shipping_fee: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    # 运费（海运）- 人民币
    overseas_shipping_fee: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    # 物流公司
    logistics_company: Mapped[Optional[str]] = mapped_column(String(100))
    # 退款金额 - 人民币
    refund_amount: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    # 退税金额 - 人民币
    tax_refund: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    # 利润 - 人民币
    profit: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    
    # 状态
    status: Mapped[SalesStatus] = mapped_column(
        SQLAlchemyEnum(SalesStatus),
        default=SalesStatus.PENDING,
        nullable=False
    )
    
    # 备注
    remarks: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # 审核信息
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    approved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by_id],
        remote_side="User.id",
        backref="approved_sales"
    )
    
    @property
    def total_amount(self) -> float:
        """计算总金额（美元 + 人民币费用，需要根据汇率转换）"""
        return self.total_price + self.domestic_shipping_fee + self.overseas_shipping_fee - self.refund_amount - self.tax_refund
    
    def __repr__(self) -> str:
        # 完全避免访问任何可能触发数据库查询的SQLAlchemy属性
        # 使用对象的内存地址来提供唯一标识
        return f"<SalesRecord at {hex(id(self))}>" 