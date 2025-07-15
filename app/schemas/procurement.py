from typing import Optional
from datetime import datetime
from pydantic import Field, field_validator
from .base import BaseSchema, TimestampSchema

class ProcurementBase(BaseSchema):
    """采购基础Schema"""
    supplier: str = Field(..., max_length=100, description="供应单位")
    procurement_item: str = Field(..., max_length=1000, description="采购事项")
    quantity: int = Field(..., gt=0, description="数量")
    amount: float = Field(..., gt=0, description="金额（人民币）")
    payment_method: str = Field(..., max_length=100, description="支付方式")
    remarks: Optional[str] = Field(None, max_length=1000, description="备注")

    @field_validator("amount")
    def validate_amount(cls, v: float) -> float:
        """验证金额，保留两位小数"""
        return round(v, 2)

class ProcurementCreate(ProcurementBase):
    """采购创建Schema"""
    sales_record_id: int = Field(..., description="订单ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sales_record_id": 1,
                "supplier": "深圳某某供应商",
                "procurement_item": "电子元器件批次采购",
                "quantity": 100,
                "amount": 5000.00,
                "payment_method": "银行转账",
                "remarks": "质量要求：符合CE认证标准"
            }
        }

class ProcurementUpdate(BaseSchema):
    """采购更新Schema"""
    supplier: Optional[str] = Field(None, max_length=100, description="供应单位")
    procurement_item: Optional[str] = Field(None, max_length=1000, description="采购事项")
    quantity: Optional[int] = Field(None, gt=0, description="数量")
    amount: Optional[float] = Field(None, gt=0, description="金额（人民币）")
    payment_method: Optional[str] = Field(None, max_length=100, description="支付方式")
    remarks: Optional[str] = Field(None, max_length=1000, description="备注")

    @field_validator("amount")
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        """验证金额，保留两位小数"""
        if v is not None:
            return round(v, 2)
        return v

class ProcurementInDBBase(ProcurementBase, TimestampSchema):
    """数据库中的采购Schema基类"""
    id: int
    sales_record_id: int

class ProcurementInDB(ProcurementInDBBase):
    """数据库中的采购Schema"""
    pass

# 销售记录简化信息（避免循环引用）
class SalesRecordSimple(BaseSchema):
    """销售记录简化信息"""
    id: int
    order_number: str
    order_source: str
    
    class Config:
        from_attributes = True

class ProcurementResponse(ProcurementInDBBase):
    """采购响应Schema"""
    sales_record: SalesRecordSimple

    class Config:
        from_attributes = True 