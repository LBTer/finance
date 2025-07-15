from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
import enum

class OrderType(str, enum.Enum):
    """订单类型枚举"""
    OVERSEAS = "overseas"    # 海外
    DOMESTIC = "domestic"    # 国内

class OrderSource(str, enum.Enum):
    """订单来源枚举"""
    ALIBABA = "alibaba"      # 阿里
    DOMESTIC = "domestic"    # 国内
    EXHIBITION = "exhibition" # 展会

class OrderStage(str, enum.Enum):
    """订单阶段枚举"""
    STAGE_1 = "stage_1"  # 第一阶段（待销售提交）：初次创建，信息补充阶段
    STAGE_2 = "stage_2"  # 第二阶段（待初步审核）：待后勤审核
    STAGE_3 = "stage_3"  # 第三阶段（待所有信息提交）：后勤审核通过，信息补充阶段
    STAGE_4 = "stage_4"  # 第四阶段（待最终审核）：待最终审核
    STAGE_5 = "stage_5"  # 第五阶段（已最终审核）：超级/高级用户审核通过

class SalesRecord(Base):
    """销售记录模型 - 美金订单"""
    
    # 订单号（系统内部主键）
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # 订单编号（业务编号）
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
    
    # 订单基本信息
    order_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    order_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    
    # 销售信息
    # 产品名称
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 数量
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # 单价（美元）
    unit_price: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    # 总价（美元）
    total_price: Mapped[float] = mapped_column(Float(precision=2), nullable=False)
    # 汇率（美元-人民币）
    exchange_rate: Mapped[float] = mapped_column(Float(precision=4), nullable=False, default=7.0, server_default="7.0") # server_default给旧行添加默认值
    # 出厂价格（人民币）- 由后勤人员填写
    factory_price: Mapped[float] = mapped_column(Float(precision=2), nullable=False, default=0.0, server_default="0.0")
    
    
    # 费用信息
    # 运费
    shipping_fees: Mapped[List["ShippingFees"]] = relationship(
        "ShippingFees",
        back_populates="sales_record",
        cascade="all, delete-orphan"
    )
    # 采购
    procurement: Mapped[List["Procurement"]] = relationship(
        "Procurement",
        back_populates="sales_record",
        cascade="all, delete-orphan"
    )

    # 退款/退税
    # 退款金额 - 人民币
    refund_amount: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    # 退税金额 - 人民币
    tax_refund: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    # 利润 - 人民币
    profit: Mapped[float] = mapped_column(Float(precision=2), default=0.0)
    
    # 订单阶段
    stage: Mapped[str] = mapped_column(
        String(20),
        default=OrderStage.STAGE_1.value,
        nullable=False
    )
    
    # 备注
    remarks: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # 审核信息 - 后勤审核（第二阶段 -> 第三阶段）
    logistics_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    logistics_approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    logistics_approved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[logistics_approved_by_id],
        remote_side="User.id"
    )
    
    # 最终审核信息（第四阶段 -> 第五阶段）
    final_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    final_approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"))
    final_approved_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[final_approved_by_id],
        remote_side="User.id"
    )
    
    @property
    def total_amount(self) -> float:
        """计算总金额（美元 + 运费等费用，按汇率转换）"""
        # 基础总价（美元）
        base_amount = self.total_price

        # 出厂价格（人民币）
        factory_price = self.factory_price
        
        # 计算运费总额（人民币转美元）
        shipping_fee_total = sum(fee.shipping_fee for fee in self.shipping_fees) / self.exchange_rate if self.shipping_fees else 0
        
        # 计算采购总额（人民币转美元）
        procurement_total = sum(proc.amount for proc in self.procurement) / self.exchange_rate if self.procurement else 0
        
        # 计算退款退税（人民币转美元）
        refund_tax_total = (self.refund_amount + self.tax_refund) / self.exchange_rate
        
        return base_amount - factory_price - shipping_fee_total - procurement_total + refund_tax_total
    
    @property
    def sales_attachments(self) -> List["Attachment"]:
        """获取销售附件"""
        from app.models.attachment import AttachmentType
        return [att for att in self.attachments if att.attachment_type == AttachmentType.SALES.value]
    
    @property
    def logistics_attachments(self) -> List["Attachment"]:
        """获取后勤附件"""
        from app.models.attachment import AttachmentType
        return [att for att in self.attachments if att.attachment_type == AttachmentType.LOGISTICS.value]
    
    # 关系：附件
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment",
        back_populates="sales_record",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        # 完全避免访问任何可能触发数据库查询的SQLAlchemy属性
        # 使用对象的内存地址来提供唯一标识
        return f"<SalesRecord at {hex(id(self))}>" 