"""
查看用户信息，包括当前用户信息、所有用户信息、指定用户信息
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AsyncSessionDep, get_current_user, get_current_active_superuser, get_current_active_senior_or_admin
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserListResponse

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前登录用户信息
    """
    return current_user

@router.get("", response_model=UserListResponse)
async def get_users(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量")
) -> UserListResponse:
    """
    获取用户列表（分页）
    
    权限要求：
    - 超级管理员：可以查看所有用户
    - 高级用户：可以查看自己和普通用户
    
    按创建时间从早到晚排序
    """
    # 构建基础查询
    base_query = select(User)
    
    # 根据当前用户角色过滤
    if current_user.role == UserRole.NORMAL:
        # 普通用户只能看到自己
        base_query = base_query.where(User.id == current_user.id)
    elif current_user.role == UserRole.SENIOR:
        # 高级用户只能看到自己和普通用户
        base_query = base_query.where(
            (User.id == current_user.id) | (User.role == UserRole.NORMAL)
        )
    # 超级管理员可以看到所有用户，不需要额外过滤
    
    # 获取总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 计算分页参数
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size
    
    # 构建分页查询，按创建时间从早到晚排序
    query = base_query.order_by(User.created_at.asc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_active_senior_or_admin)]
) -> User:
    """
    获取指定用户信息
    - 超级管理员：可以看到所有用户
    - 高级用户：可以看到所有高级用户和所有普通用户
    - 普通用户：可以看到所有普通用户
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
    if current_user.role == UserRole.NORMAL.value and user.role != UserRole.NORMAL.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能查看普通用户的信息"
        )
    if current_user.role == UserRole.SENIOR.value and user.role == UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能查看普通用户和高级用户的信息"
        )
    
    return user