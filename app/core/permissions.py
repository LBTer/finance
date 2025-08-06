from enum import Enum
from typing import Callable, List, Optional, Type, TypeVar
from fastapi import HTTPException, status
from functools import wraps

from app.models.user import User, UserRole, UserFunction
from app.models.sales_record import SalesRecord, OrderStage
from app.models.attachment import AttachmentType

T = TypeVar("T")

class Action(str, Enum):
    """操作类型枚举"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    SUBMIT = "submit"
    WITHDRAW = "withdraw"
    VOID = "void"
    UNVOID = "unvoid"
    MANAGE_SALES_ATTACHMENT = "manage_sales_attachment"
    MANAGE_LOGISTICS_ATTACHMENT = "manage_logistics_attachment"

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
        if self.user.is_superuser or self.user.role == UserRole.ADMIN.value:
            return True
            
        # 高级用户拥有所有权限
        if self.user.role == UserRole.SENIOR.value:
            return True
        
        # 普通用户权限
        if action == Action.CREATE:
            # 只有有销售职能的用户可以创建销售记录
            return self.user.has_sales_function()
        
        if action == Action.READ:
            # 所有用户都可以查看销售记录
            return True
        
        # 需要操作对象的权限检查
        if obj is None:
            return False
        
        if action == Action.UPDATE:
            return await self._can_update_record(obj)
        
        if action == Action.DELETE:
            return await self._can_delete_record(obj)
        
        if action == Action.SUBMIT:
            return await self._can_submit_record(obj)
        
        if action == Action.APPROVE:
            return await self._can_approve_record(obj)
        
        if action == Action.WITHDRAW:
            return await self._can_withdraw_record(obj)
        
        if action == Action.VOID:
            return await self._can_void_record(obj)
        
        if action == Action.UNVOID:
            return await self._can_unvoid_record(obj)
        
        if action == Action.MANAGE_SALES_ATTACHMENT:
            return await self._can_manage_sales_attachment(obj)
        
        if action == Action.MANAGE_LOGISTICS_ATTACHMENT:
            return await self._can_manage_logistics_attachment(obj)
            
        return False
    
    async def _can_update_record(self, obj: SalesRecord) -> bool:
        """检查是否可以更新销售记录"""
        stage = obj.stage
        
        # 阶段一：只有创建记录的本人可以修改
        if stage == OrderStage.STAGE_1.value:
            return obj.user_id == self.user.id and self.user.has_sales_function()
        
        # 阶段二：谁也不能修改
        if stage == OrderStage.STAGE_2.value:
            return False
        
        # 阶段三：具有后勤职能的人可以修改
        if stage == OrderStage.STAGE_3.value:
            return self.user.has_logistics_function()
        
        # 阶段四：谁也不能修改
        if stage == OrderStage.STAGE_4.value:
            return False
        
        # 阶段五：不能修改
        if stage == OrderStage.STAGE_5.value:
            return False
        
        return False
    
    async def _can_delete_record(self, obj: SalesRecord) -> bool:
        """检查是否可以删除销售记录"""
        # 只有在阶段一且是创建者本人才能删除
        return (obj.stage == OrderStage.STAGE_1.value and 
                obj.user_id == self.user.id and 
                self.user.has_sales_function())
    
    async def _can_submit_record(self, obj: SalesRecord) -> bool:
        """检查是否可以提交到下一阶段"""
        stage = obj.stage
        
        # 阶段一到阶段二：只有创建记录的本人可以提交
        if stage == OrderStage.STAGE_1.value:
            return obj.user_id == self.user.id and self.user.has_sales_function()
        
        # 阶段三到阶段四：具有后勤职能的人可以提交
        if stage == OrderStage.STAGE_3.value:
            return self.user.has_logistics_function()
        
        return False
    
    async def _can_approve_record(self, obj: SalesRecord) -> bool:
        """检查是否可以审核记录"""
        stage = obj.stage
        
        # 阶段二到阶段三：具有后勤职能的人可以审核
        if stage == OrderStage.STAGE_2.value:
            return self.user.has_logistics_function()
        
        # 阶段四到阶段五：只有高级用户/超级管理员可以审核
        if stage == OrderStage.STAGE_4.value:
            return self.user.can_approve_final()
        
        return False
    
    async def _can_withdraw_record(self, obj: SalesRecord) -> bool:
        """检查是否可以撤回记录"""
        stage = obj.stage
        
        # 阶段二撤回阶段一：只有创建记录的本人可以撤回
        if stage == OrderStage.STAGE_2.value:
            return obj.user_id == self.user.id and self.user.has_sales_function()
        
        # 阶段三撤回阶段一：有后勤职能的人可以撤回
        if stage == OrderStage.STAGE_3.value:
            return self.user.has_logistics_function()
        
        # 阶段四撤回阶段三：有后勤职能的人可以撤回
        if stage == OrderStage.STAGE_4.value:
            return self.user.has_logistics_function()
        
        # 阶段五撤回阶段三：只有高级用户/超级用户可以撤回
        if stage == OrderStage.STAGE_5.value:
            return self.user.can_approve_final()
        
        return False
    
    async def _can_manage_sales_attachment(self, obj: SalesRecord) -> bool:
        """检查是否可以管理销售附件"""
        stage = obj.stage
        
        # 销售附件只可以在创建时/阶段一修改
        if stage == OrderStage.STAGE_1.value:
            return obj.user_id == self.user.id and self.user.has_sales_function()
        
        return False
    
    async def _can_manage_logistics_attachment(self, obj: SalesRecord) -> bool:
        """检查是否可以管理后勤附件"""
        stage = obj.stage
        
        # 后勤附件只可以在阶段三修改
        if stage == OrderStage.STAGE_3.value:
            return self.user.has_logistics_function()
        
        return False
    
    async def _can_void_record(self, obj: SalesRecord) -> bool:
        """检查是否可以作废销售记录"""
        # 只有高级用户和超级管理员可以作废记录
        return (self.user.is_superuser or 
                self.user.role == UserRole.ADMIN.value or 
                self.user.role == UserRole.SENIOR.value)
    
    async def _can_unvoid_record(self, obj: SalesRecord) -> bool:
        """检查是否可以取消作废销售记录"""
        # 只有高级用户和超级管理员可以取消作废记录
        return (self.user.is_superuser or 
                self.user.role == UserRole.ADMIN.value or 
                self.user.role == UserRole.SENIOR.value)

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
async def get_sales_record(db, record_id: int, **kwargs) -> Optional[SalesRecord]:
    """根据ID获取销售记录"""
    from sqlalchemy import select
    result = await db.execute(
        select(SalesRecord).where(SalesRecord.id == record_id)
    )
    return result.scalar_one_or_none()