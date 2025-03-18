from enum import Enum
from typing import Callable, List, Optional, Type, TypeVar
from fastapi import HTTPException, status
from functools import wraps

from app.models.user import User, UserRole
from app.models.sales_record import SalesRecord

T = TypeVar("T")

class Action(str, Enum):
    """操作类型枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"

class BasePermission:
    """权限基类"""
    
    def __init__(self, user: User):
        self.user = user
    
    async def has_permission(self, action: Action, obj: Optional[T] = None) -> bool:
        """
        检查用户是否有权限执行特定操作
        
        Args:
            action: 操作类型
            obj: 操作对象（可选）
            
        Returns:
            bool: 是否有权限
        """
        raise NotImplementedError

class SalesRecordPermission(BasePermission):
    """销售记录权限"""
    
    async def has_permission(self, action: Action, obj: Optional[SalesRecord] = None) -> bool:
        # 超级管理员拥有所有权限
        if self.user.is_superuser:
            return True
            
        # 高级用户可以查看所有记录并审核
        if self.user.role == UserRole.SENIOR:
            if action == Action.APPROVE:
                return True
            if action in [Action.READ, Action.UPDATE, Action.DELETE]:
                return True
            if action == Action.CREATE:
                return True
                
        # 普通用户只能操作自己的记录
        if self.user.role == UserRole.NORMAL:
            if action == Action.CREATE:
                return True
            if obj is None:
                return False
            if obj.user_id != self.user.id:
                return False
            # 普通用户只能修改/删除待审核的记录
            if action in [Action.UPDATE, Action.DELETE]:
                from app.models.sales_record import SalesStatus
                return obj.status == SalesStatus.PENDING
            return action == Action.READ
            
        return False

def check_permissions(
    permission_class: Type[BasePermission],
    action: Action,
    get_object: Optional[Callable] = None
):
    """
    权限检查装饰器
    
    Args:
        permission_class: 权限类
        action: 操作类型
        get_object: 获取操作对象的函数（可选）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = None
            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                    break
            if not current_user:
                for value in kwargs.values():
                    if isinstance(value, User):
                        current_user = value
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证的用户"
                )
            
            # 获取操作对象
            obj = None
            if get_object:
                obj = await get_object(*args, **kwargs)
            
            # 检查权限
            permission = permission_class(current_user)
            has_perm = await permission.has_permission(action, obj)
            
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 预定义的权限检查装饰器
def check_sales_record_permissions(
    action: Action,
    get_object: Optional[Callable] = None
):
    """销售记录权限检查装饰器"""
    return check_permissions(SalesRecordPermission, action, get_object)

# 工具函数：获取销售记录对象
async def get_sales_record(db, record_id: int) -> Optional[SalesRecord]:
    """根据ID获取销售记录"""
    from sqlalchemy import select
    result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == record_id)
    )
    return result.scalar_one_or_none() 