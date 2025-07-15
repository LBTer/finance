from typing import Optional
from datetime import datetime
from pydantic import Field, field_validator
from .base import BaseSchema, TimestampSchema

class ShippingFeesBase(BaseSchema):
    """运费基础Schema"""
    shipping_fee: float = Field(..., gt=0, description="运费金额（人民币）")
    logistics_type: str = Field(..., description="物流类型（国内/国际）")
    payment_method: str = Field(..., description="支付方式")
    logistics_company: str = Field(..., description="物流公司")
    remarks: Optional[str] = Field(None, max_length=1000, description="备注")

    @field_validator("shipping_fee")
    def validate_shipping_fee(cls, v: float) -> float:
        """验证运费金额，保留两位小数"""
        return round(v, 2)

class ShippingFeesCreate(ShippingFeesBase):
    """运费创建Schema"""
    sales_record_id: int = Field(..., description="订单ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sales_record_id": 1,
                "shipping_fee": 150.00,
                "logistics_type": "domestic_express",
                "payment_method": "现金",
                "logistics_company": "顺丰速运",
                "remarks": "加急配送"
            }
        }

class ShippingFeesUpdate(BaseSchema):
    """运费更新Schema"""
    shipping_fee: Optional[float] = Field(None, gt=0, description="运费金额（人民币）")
    logistics_type: Optional[str] = Field(None, description="物流类型（国内/国际）")
    payment_method: Optional[str] = Field(None, description="支付方式")
    logistics_company: Optional[str] = Field(None, description="物流公司")
    remarks: Optional[str] = Field(None, max_length=1000, description="备注")

    @field_validator("shipping_fee")
    def validate_shipping_fee(cls, v: Optional[float]) -> Optional[float]:
        """验证运费金额，保留两位小数"""
        if v is not None:
            return round(v, 2)
        return v

class ShippingFeesInDBBase(ShippingFeesBase, TimestampSchema):
    """数据库中的运费Schema基类"""
    id: int
    sales_record_id: int

class ShippingFeesInDB(ShippingFeesInDBBase):
    """数据库中的运费Schema"""
    pass

# 销售记录简化信息（避免循环引用）
class SalesRecordSimple(BaseSchema):
    """销售记录简化信息"""
    id: int
    order_number: str
    order_source: str
    
    class Config:
        from_attributes = True

class ShippingFeesResponse(ShippingFeesInDBBase):
    """运费响应Schema"""
    sales_record: SalesRecordSimple

    class Config:
        from_attributes = True 