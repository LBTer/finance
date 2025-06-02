from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AsyncSessionDep, get_current_user, get_current_active_superuser, get_current_active_senior_or_admin
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前登录用户信息
    """
    return current_user

@router.get("", response_model=List[UserResponse])
async def get_users(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_active_senior_or_admin)]
) -> List[User]:
    """
    获取用户列表
    - 超级管理员可以看到所有用户
    - 高级用户可以看到自己和普通用户
    - 普通用户只能看到自己
    """
    # 根据用户角色过滤用户列表
    if current_user.role == UserRole.NORMAL:
        # 普通用户只能看到自己
        query = select(User).where(User.id == current_user.id)
    elif current_user.role == UserRole.SENIOR:
        # 高级用户可以看到自己和普通用户
        query = select(User).where(
            (User.id == current_user.id) | 
            (User.role == UserRole.NORMAL)
        )
    else:  # admin
        # 超级管理员可以看到所有用户
        query = select(User)
    
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_active_senior_or_admin)]
) -> User:
    """
    获取指定用户信息
    - 超级管理员可以查看任何用户
    - 高级用户只能查看自己和普通用户
    - 普通用户只能查看自己
    """
    # 获取目标用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查
    if current_user.role == UserRole.NORMAL and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能查看自己的信息"
        )
    if current_user.role == UserRole.SENIOR and user.id != current_user.id and user.role != UserRole.NORMAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能查看普通用户的信息"
        )
    
    return user