from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """基础Schema类"""
    model_config = ConfigDict(from_attributes=True)

class TimestampSchema(BaseSchema):
    """包含时间戳的Schema"""
    created_at: datetime
    updated_at: datetime 