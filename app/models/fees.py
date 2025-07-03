from app.db.base_class import Base
from sqlalchemy import Integer, Float, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum


# 物流类型，国内快递/国际快递
class LogisticsType(str, Enum):
    DOMESTIC_EXPRESS = "domestic_express"
    INTERNATIONAL_EXPRESS = "international_express"

"""
ShippingFees 运费表，和订单是多对一关系，一个订单可以有多个运费
"""
class ShippingFees(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # 订单id
    sales_record_id: Mapped[int] = mapped_column(ForeignKey("sales_record.id"), nullable=False)
    sales_record: Mapped["SalesRecord"] = relationship(
        "SalesRecord", 
        back_populates="shipping_fees"
    )
    
    # 核心字段，运费金额，物流类型，支付方式，物流公司，备注
    # 运费金额（人民币）
    shipping_fee: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    # 物流类型，国内/海外
    logistics_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # 支付方式
    payment_method: Mapped[str] = mapped_column(String(100), nullable=False)
    # 物流公司
    logistics_company: Mapped[str] = mapped_column(String(100), nullable=False)
    # 备注
    remarks: Mapped[str] = mapped_column(String(1000), nullable=True)
    