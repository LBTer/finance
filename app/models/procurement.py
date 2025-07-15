from app.db.base_class import Base
from sqlalchemy import Integer, Float, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


"""
procurement 采购表，和订单是多对一关系，一个订单可以有多个采购
"""
class Procurement(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 订单id
    sales_record_id: Mapped[int] = mapped_column(ForeignKey("salesrecord.id"), nullable=False)
    sales_record: Mapped["SalesRecord"] = relationship(
        "SalesRecord", 
        back_populates="procurement"
    )
    
    # 核心字段，供应单位，采购事项，数量，金额（人民币），支付方式，备注
    # 供应单位
    supplier: Mapped[str] = mapped_column(String(100), nullable=False)
    # 采购事项
    procurement_item: Mapped[str] = mapped_column(String(1000), nullable=False)
    # 数量
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # 金额（人民币）
    amount: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    # 支付方式
    payment_method: Mapped[str] = mapped_column(String(100), nullable=False)
    # 备注
    remarks: Mapped[str] = mapped_column(String(1000), nullable=True)
    