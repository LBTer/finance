from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import Field, field_validator
from app.models.sales_record import OrderSource, OrderStage
from .base import BaseSchema, TimestampSchema
from .user import UserResponse
from .attachment import AttachmentResponse

if TYPE_CHECKING:
    from .fees import ShippingFeesResponse
    from .procurement import ProcurementResponse

class SalesRecordBase(BaseSchema):
    """销售记录基础Schema"""
    order_number: str = Field(..., min_length=3, max_length=50, description="订单编号")
    order_type: str = Field(..., description="订单类型")
    order_source: str = Field(..., description="订单来源")
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0, description="单价（美元）")
    total_price: float = Field(..., gt=0, description="总价（美元）")
    exchange_rate: float = Field(..., gt=0, description="汇率（美元-人民币）", ge=1.0, le=20.0)
    factory_price: float = Field(default=0.0, ge=0, description="出厂价格（人民币）")
    refund_amount: float = Field(default=0.0, ge=0, description="退款金额（人民币）")
    tax_refund: float = Field(default=0.0, ge=0, description="退税金额（人民币）")
    profit: float = Field(default=0.0, description="利润（人民币）")
    remarks: Optional[str] = Field(None, max_length=1000)

    @field_validator("unit_price", "total_price", "factory_price", "refund_amount", "tax_refund", "profit")
    def validate_amount(cls, v: float) -> float:
        """验证金额，保留两位小数"""
        return round(v, 2)
    
    @field_validator("exchange_rate")
    def validate_exchange_rate(cls, v: float) -> float:
        """验证汇率，保留四位小数"""
        return round(v, 4)

    @field_validator("total_price")
    def validate_total_price(cls, v: float, values) -> float:
        """验证总价，如果没有提供，则自动计算"""
        if v == 0 and "quantity" in values.data and "unit_price" in values.data:
            return round(values.data["quantity"] * values.data["unit_price"], 2)
        return v

class SalesRecordCreate(SalesRecordBase):
    """销售记录创建Schema"""
    class Config:
        json_schema_extra = {
            "example": {
                "order_number": "ORD20240101001",
                "order_type": "overseas",
                "order_source": "alibaba",
                "product_name": "示例产品",
                "quantity": 1,
                "unit_price": 99.99,
                "total_price": 99.99,
                "exchange_rate": 6.5,
                "refund_amount": 0.00,
                "tax_refund": 0.00,
                "profit": 210.00,
                "remarks": "示例备注"
            }
        }

class SalesRecordUpdate(BaseSchema):
    """销售记录更新Schema"""
    order_type: Optional[str] = Field(None, description="订单类型")
    order_source: Optional[str] = Field(None, description="订单来源")
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0, description="单价（美元）")
    total_price: Optional[float] = Field(None, gt=0, description="总价（美元）")
    exchange_rate: Optional[float] = Field(None, gt=0, description="汇率（美元-人民币）", ge=1.0, le=20.0)
    factory_price: Optional[float] = Field(None, ge=0, description="出厂价格（人民币）")
    refund_amount: Optional[float] = Field(None, ge=0, description="退款金额（人民币）")
    tax_refund: Optional[float] = Field(None, ge=0, description="退税金额（人民币）")
    profit: Optional[float] = Field(None, description="利润（人民币）")
    remarks: Optional[str] = Field(None, max_length=1000)
    stage: Optional[str] = Field(None, description="订单阶段")

    @field_validator("unit_price", "total_price", "exchange_rate", "factory_price", "refund_amount", "tax_refund", "profit")
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        """验证金额，保留两位小数"""
        if v is not None:
            return round(v, 2)
        return v
    
    @field_validator("exchange_rate")
    def validate_exchange_rate(cls, v: Optional[float]) -> Optional[float]:
        """验证汇率，保留四位小数"""
        if v is not None:
            return round(v, 4)
        return v

class SalesRecordInDBBase(SalesRecordBase, TimestampSchema):
    """数据库中的销售记录Schema基类"""
    id: int
    user_id: int
    stage: str
    logistics_approved_at: Optional[datetime] = None
    logistics_approved_by_id: Optional[int] = None
    final_approved_at: Optional[datetime] = None
    final_approved_by_id: Optional[int] = None

class SalesRecordInDB(SalesRecordInDBBase):
    """数据库中的销售记录Schema"""
    pass

class SalesRecordResponse(SalesRecordInDBBase):
    """销售记录响应Schema"""
    user: UserResponse
    logistics_approved_by: Optional[UserResponse] = None
    final_approved_by: Optional[UserResponse] = None
    total_amount: float
    attachments: List[AttachmentResponse] = []
    shipping_fees: List["ShippingFeesResponse"] = []
    procurement: List["ProcurementResponse"] = []

    class Config:
        from_attributes = True

# 解决前向引用问题
def rebuild_models():
    """重建模型以解决前向引用"""
    try:
        from .fees import ShippingFeesResponse
        from .procurement import ProcurementResponse
        SalesRecordResponse.model_rebuild()
    except ImportError:
        pass 