from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole, UserFunction
from .base import BaseSchema, TimestampSchema

class UserBase(BaseSchema):
    """用户基础Schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: Optional[str] = Field(default=UserRole.NORMAL.value)
    function: Optional[str] = Field(default=UserFunction.SALES.value)
    is_active: Optional[bool] = Field(default=True)
    is_superuser: Optional[bool] = Field(default=False)

class UserCreate(UserBase):
    """用户创建Schema"""
    phone: str
    email: str | None = None
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = UserRole.NORMAL.value
    function: str = UserFunction.SALES.value
    is_active: bool = True
    is_superuser: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "12345678901",
                "email": "user@example.com",
                "password": "strongpassword123",
                "full_name": "张三",
                "role": "normal",
                "function": "sales"
            }
        }

class UserUpdate(BaseSchema):
    """用户更新Schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[str] = None
    function: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserInDBBase(UserBase, TimestampSchema):
    """数据库中的用户Schema基类"""
    id: int

    class Config:
        from_attributes = True

class UserInDB(UserInDBBase):
    """数据库中的用户Schema（包含密码哈希）"""
    password_hash: str

class UserResponse(UserInDBBase):
    """用户响应Schema"""
    phone: str
    email: str | None
    full_name: str
    role: str
    function: str
    is_active: bool
    
    class Config:
        from_attributes = True

class UserInfoUpdate(BaseSchema):
    """用户信息更新Schema（仅超级管理员可使用）"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    function: Optional[str] = None
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "张三",
                "email": "user@example.com",
                "role": "senior",
                "function": "sales_logistics",
                "is_active": True
            }
        }

class PasswordReset(BaseSchema):
    """重置密码请求体"""
    phone: str
    new_password: str = Field(..., min_length=8, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "phone": "12345678901",
                "new_password": "newpassword123"
            }
        } 