from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.dependencies import AsyncSessionDep, get_current_active_superuser
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.utils.validators import Validators  # 确保导入验证器

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/login")
async def login(
    db: AsyncSessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> dict:
    """
    用户登录（使用手机号）
    """
    # 验证手机号格式
    try:
        Validators.validate_phone_number(form_data.username)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )
    
    # 查找用户
    result = await db.execute(
        select(User).where(User.phone == form_data.username)  # 修改这里
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",  # 修改错误提示
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=UserResponse)
async def register(
    *,
    db: AsyncSessionDep,
    user_in: UserCreate,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
) -> User:
    """
    注册新用户（仅超级管理员可用）
    """
    # 验证手机号格式
    try:
        Validators.validate_phone_number(user_in.phone)  # 添加手机号验证
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )
    
    # 检查手机号是否已存在
    result = await db.execute(
        select(User).where(User.phone == user_in.phone)  # 修改这里
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已被注册"
        )
    
    # 如果提供了邮箱，检查邮箱是否已存在
    if user_in.email:
        result = await db.execute(
            select(User).where(User.email == user_in.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )
    
    # 创建新用户
    user = User(
        phone=user_in.phone,  # 添加手机号
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/reset-password")
async def reset_password(
    db: AsyncSessionDep,
    phone: str,  # 修改为手机号
    new_password: str,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
) -> dict:
    """
    重置用户密码（仅超级管理员可用）
    """
    # 验证手机号格式
    try:
        Validators.validate_phone_number(phone)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )
    
    # 查找用户
    result = await db.execute(
        select(User).where(User.phone == phone)  # 修改这里
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(new_password)
    await db.commit()
    
    return {"message": "密码重置成功"} 