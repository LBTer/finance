from typing import AsyncGenerator, Optional, Annotated
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)

# 定义常用的依赖类型
AsyncSessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]

async def get_current_user(
    db: AsyncSessionDep,
    token: TokenDep,
) -> User:
    """
    获取当前用户

    Args:
        db: 异步数据库会话
        token: JWT令牌

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # 验证令牌是否过期
        exp = payload.get("exp")
        if exp is None:
            raise credentials_exception
        if datetime.now(timezone.utc).timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exception

    try:
        # 将JWT中的字符串ID转换为整数
        user_id_int = int(user_id)
        
        # 从数据库获取用户信息
        result = await db.execute(
            select(User).where(User.id == user_id_int)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已被禁用"
            )
            
        return user
    except ValueError:
        # 用户ID不是有效的整数
        raise credentials_exception

async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前超级用户

    Args:
        current_user: 当前用户对象

    Returns:
        User: 当前超级用户对象

    Raises:
        HTTPException: 当用户不是超级用户时抛出
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

async def get_current_active_senior_or_admin(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前高级用户或管理员用户

    Args:
        current_user: 当前用户对象

    Returns:
        User: 当前高级用户或管理员对象

    Raises:
        HTTPException: 当用户既不是高级用户也不是管理员时抛出
    """
    
    if current_user.role not in [UserRole.SENIOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要高级用户或管理员权限"
        )
    return current_user 