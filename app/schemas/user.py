from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole
from .base import BaseSchema, TimestampSchema

class UserBase(BaseSchema):
    """用户基础Schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: Optional[UserRole] = Field(default=UserRole.NORMAL)
    is_active: Optional[bool] = Field(default=True)
    is_superuser: Optional[bool] = Field(default=False)

class UserCreate(UserBase):
    """用户创建Schema"""
    phone: str
    email: str | None = None
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.NORMAL
    is_active: bool = True
    is_superuser: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "12345678901",
                "email": "user@example.com",
                "password": "strongpassword123",
                "full_name": "张三",
                "role": "normal"
            }
        }

class UserUpdate(BaseSchema):
    """用户更新Schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: Optional[UserRole] = None
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
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True

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