"""
用户登陆相关接口，包括登录、注册、重置密码
"""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.dependencies import AsyncSessionDep, get_current_active_superuser, get_current_active_senior_or_admin
from app.models.user import User, UserFunction, UserRole
from app.schemas.user import UserCreate, UserResponse, PasswordReset, UserInfoUpdate
from app.utils.validators import Validators

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
        select(User).where(User.phone == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
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
    current_user: Annotated[User, Depends(get_current_active_senior_or_admin)]
) -> User:
    """
    注册新用户
    - 超级管理员可以创建高级用户和普通用户
    - 高级用户只能创建普通用户
    - 普通用户不能创建用户
    """
    # 创建的用户类型检查
    if user_in.role not in [UserRole.NORMAL.value, UserRole.SENIOR.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户角色"
        )
    if user_in.function not in [UserFunction.SALES.value, UserFunction.LOGISTICS.value, UserFunction.SALES_LOGISTICS.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户职能"
        )

    # 权限检查
    if current_user.role == UserRole.NORMAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通用户不能创建新用户"
        )
    if current_user.role == UserRole.SENIOR.value and user_in.role != UserRole.NORMAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="高级用户只能创建普通用户"
        )
    if user_in.role == UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能通过接口创建超级管理员"
        )
    
    # 验证手机号格式
    try:
        Validators.validate_phone_number(user_in.phone)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )
    
    # 检查手机号是否已存在
    result = await db.execute(
        select(User).where(User.phone == user_in.phone)
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
        phone=user_in.phone,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        function=user_in.function,
        is_active=user_in.is_active,
        is_superuser=False  # 确保通过接口创建的用户不是超级用户
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/reset-password")
async def reset_password(
    db: AsyncSessionDep,
    reset_data: PasswordReset,
    current_user: Annotated[User, Depends(get_current_active_senior_or_admin)]
) -> dict:
    """
    重置用户密码
    - 超级管理员可以重置所有人的密码
    - 高级用户可以重置自己和普通用户的密码
    - 普通用户只能重置自己的密码
    """
    # 验证手机号格式
    try:
        Validators.validate_phone_number(reset_data.phone)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )
    
    # 查找用户
    result = await db.execute(
        select(User).where(User.phone == reset_data.phone)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查
    if current_user.role == UserRole.NORMAL.value and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能重置自己的密码"
        )
    if current_user.role == UserRole.SENIOR.value and user.id != current_user.id and user.role != UserRole.NORMAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能重置普通用户的密码"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(reset_data.new_password)
    await db.commit()
    
    return {"message": "密码重置成功"} 

@router.put("/users/{user_id}/info", response_model=UserResponse)
async def update_user_info(
    user_id: int,
    user_update: UserInfoUpdate,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
) -> User:
    """
    修改用户信息
    - 只有超级管理员可以使用此接口
    - 可以修改用户的姓名、邮箱、角色、职能、启用状态
    - 用户角色只能修改成普通用户/高级用户
    """
    # 查找要修改的用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证角色
    if user_update.role is not None:
        if user_update.role not in [UserRole.NORMAL.value, UserRole.SENIOR.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户角色只能修改为普通用户或高级用户"
            )
    
    # 验证职能
    if user_update.function is not None:
        if user_update.function not in [UserFunction.SALES.value, UserFunction.LOGISTICS.value, UserFunction.SALES_LOGISTICS.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的用户职能"
            )
    
    # 验证邮箱是否已被其他用户使用
    if user_update.email is not None:
        existing_user_result = await db.execute(
            select(User).where(User.email == user_update.email, User.id != user_id)
        )
        if existing_user_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被其他用户使用"
            )
    
    # 更新用户信息
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.function is not None:
        user.function = user_update.function
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    await db.commit()
    await db.refresh(user)
    
    return user 