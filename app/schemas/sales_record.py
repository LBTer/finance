from typing import Optional
from datetime import datetime
from pydantic import Field, field_validator
from app.models.sales_record import SalesStatus
from .base import BaseSchema, TimestampSchema
from .user import UserResponse

class SalesRecordBase(BaseSchema):
    """销售记录基础Schema"""
    order_number: str = Field(..., min_length=3, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    domestic_shipping_fee: float = Field(default=0.0, ge=0)
    overseas_shipping_fee: float = Field(default=0.0, ge=0)
    logistics_company: Optional[str] = Field(None, max_length=100)
    refund_amount: float = Field(default=0.0, ge=0)
    tax_refund: float = Field(default=0.0, ge=0)
    profit: float = Field(default=0.0)
    remarks: Optional[str] = Field(None, max_length=1000)

    @field_validator("unit_price", "total_price", "domestic_shipping_fee", "overseas_shipping_fee", "refund_amount", "tax_refund", "profit")
    def validate_amount(cls, v: float) -> float:
        """验证金额，保留两位小数"""
        return round(v, 2)

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
                "product_name": "示例产品",
                "category": "电子产品",
                "quantity": 1,
                "unit_price": 99.99,
                "total_price": 99.99,
                "domestic_shipping_fee": 5.00,
                "overseas_shipping_fee": 15.00,
                "logistics_company": "FedEx",
                "refund_amount": 0.00,
                "tax_refund": 0.00,
                "profit": 30.00,
                "remarks": "示例备注"
            }
        }

class SalesRecordUpdate(BaseSchema):
    """销售记录更新Schema"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    total_price: Optional[float] = Field(None, gt=0)
    domestic_shipping_fee: Optional[float] = Field(None, ge=0)
    overseas_shipping_fee: Optional[float] = Field(None, ge=0)
    logistics_company: Optional[str] = Field(None, max_length=100)
    refund_amount: Optional[float] = Field(None, ge=0)
    tax_refund: Optional[float] = Field(None, ge=0)
    profit: Optional[float] = None
    remarks: Optional[str] = Field(None, max_length=1000)
    status: Optional[SalesStatus] = None

    @field_validator("unit_price", "total_price", "domestic_shipping_fee", "overseas_shipping_fee", "refund_amount", "tax_refund", "profit")
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        """验证金额，保留两位小数"""
        if v is not None:
            return round(v, 2)
        return v

class SalesRecordInDBBase(SalesRecordBase, TimestampSchema):
    """数据库中的销售记录Schema基类"""
    id: int
    user_id: int
    status: SalesStatus
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None

class SalesRecordInDB(SalesRecordInDBBase):
    """数据库中的销售记录Schema"""
    pass

class SalesRecordResponse(SalesRecordInDBBase):
    """销售记录响应Schema"""
    user: UserResponse
    approved_by: Optional[UserResponse] = None
    total_amount: float

    class Config:
        from_attributes = True 