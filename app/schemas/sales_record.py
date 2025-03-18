from typing import Optional
from datetime import datetime
from pydantic import Field, validator
from app.models.sales_record import SalesStatus
from .base import BaseSchema, TimestampSchema
from .user import UserResponse

class SalesRecordBase(BaseSchema):
    """销售记录基础Schema"""
    order_number: str = Field(..., min_length=3, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    shipping_fee: float = Field(default=0.0, ge=0)
    refund_amount: float = Field(default=0.0, ge=0)
    tax_refund: float = Field(default=0.0, ge=0)
    remarks: Optional[str] = Field(None, max_length=1000)

    @validator("unit_price", "shipping_fee", "refund_amount", "tax_refund")
    def validate_amount(cls, v: float) -> float:
        """验证金额，保留两位小数"""
        return round(v, 2)

class SalesRecordCreate(SalesRecordBase):
    """销售记录创建Schema"""
    class Config:
        json_schema_extra = {
            "example": {
                "order_number": "ORD20240101001",
                "product_name": "示例产品",
                "quantity": 1,
                "unit_price": 99.99,
                "shipping_fee": 10.00,
                "remarks": "示例备注"
            }
        }

class SalesRecordUpdate(BaseSchema):
    """销售记录更新Schema"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    shipping_fee: Optional[float] = Field(None, ge=0)
    refund_amount: Optional[float] = Field(None, ge=0)
    tax_refund: Optional[float] = Field(None, ge=0)
    remarks: Optional[str] = Field(None, max_length=1000)
    status: Optional[SalesStatus] = None

    @validator("unit_price", "shipping_fee", "refund_amount", "tax_refund")
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