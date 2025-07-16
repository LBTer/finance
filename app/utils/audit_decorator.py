import functools
import inspect
from typing import Optional, Dict, Any, Callable
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditResourceType
from app.models.user import User
from app.services.audit_service import AuditService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def audit_action(
    action: AuditAction,
    resource_type: AuditResourceType,
    description: str,
    get_resource_id: Optional[Callable] = None,
    get_details: Optional[Callable] = None,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    审计操作装饰器
    
    Args:
        action: 操作类型
        resource_type: 资源类型
        description: 操作描述
        get_resource_id: 获取资源ID的函数，接收函数返回值作为参数
        get_details: 获取详细信息的函数，接收函数参数和返回值
        success_message: 成功时的描述信息
        error_message: 失败时的描述信息
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 提取参数
            db = None
            current_user = None
            request = None
            
            # 从函数签名中提取参数
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 查找常见的参数
            for param_name, param_value in bound_args.arguments.items():
                if isinstance(param_value, Session):
                    db = param_value
                elif isinstance(param_value, User):
                    current_user = param_value
                elif isinstance(param_value, Request):
                    request = param_value
            
            # 如果没有找到必要参数，尝试从kwargs中获取
            if db is None:
                db = kwargs.get('db')
            if current_user is None:
                current_user = kwargs.get('current_user')
            if request is None:
                request = kwargs.get('request')
            
            success = True
            error_msg = None
            result = None
            resource_id = None
            details = None
            
            try:
                # 执行原函数
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 获取资源ID
                if get_resource_id and result is not None:
                    try:
                        resource_id = get_resource_id(result)
                    except Exception as e:
                        logger.warning(f"Failed to get resource_id: {e}")
                
                # 获取详细信息
                if get_details:
                    try:
                        details = get_details(bound_args.arguments, result)
                    except Exception as e:
                        logger.warning(f"Failed to get audit details: {e}")
                
            except Exception as e:
                success = False
                error_msg = str(e)
                logger.error(f"Function {func.__name__} failed: {e}")
                raise
            
            finally:
                # 记录审计日志
                if db and current_user:
                    try:
                        final_description = success_message if success and success_message else description
                        if not success and error_message:
                            final_description = error_message
                        
                        await AuditService.log_action(
                            db=db,
                            user_id=current_user.id,
                            action=action,
                            resource_type=resource_type,
                            description=final_description,
                            resource_id=resource_id,
                            details=details,
                            request=request,
                            success=success,
                            error_message=error_msg
                        )
                    except Exception as audit_error:
                        logger.error(f"Failed to log audit action: {audit_error}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 对于同步函数的处理
            # 提取参数
            db = None
            current_user = None
            request = None
            
            # 从函数签名中提取参数
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 查找常见的参数
            for param_name, param_value in bound_args.arguments.items():
                if isinstance(param_value, Session):
                    db = param_value
                elif isinstance(param_value, User):
                    current_user = param_value
                elif isinstance(param_value, Request):
                    request = param_value
            
            # 如果没有找到必要参数，尝试从kwargs中获取
            if db is None:
                db = kwargs.get('db')
            if current_user is None:
                current_user = kwargs.get('current_user')
            if request is None:
                request = kwargs.get('request')
            
            success = True
            error_msg = None
            result = None
            resource_id = None
            details = None
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 获取资源ID
                if get_resource_id and result is not None:
                    try:
                        resource_id = get_resource_id(result)
                    except Exception as e:
                        logger.warning(f"Failed to get resource_id: {e}")
                
                # 获取详细信息
                if get_details:
                    try:
                        details = get_details(bound_args.arguments, result)
                    except Exception as e:
                        logger.warning(f"Failed to get audit details: {e}")
                
            except Exception as e:
                success = False
                error_msg = str(e)
                logger.error(f"Function {func.__name__} failed: {e}")
                raise
            
            finally:
                # 记录审计日志（同步版本，需要在异步上下文中调用）
                if db and current_user:
                    try:
                        import asyncio
                        final_description = success_message if success and success_message else description
                        if not success and error_message:
                            final_description = error_message
                        
                        # 创建异步任务来记录审计日志
                        loop = None
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            pass
                        
                        if loop and loop.is_running():
                            # 如果在异步上下文中，创建任务
                            asyncio.create_task(AuditService.log_action(
                                db=db,
                                user_id=current_user.id,
                                action=action,
                                resource_type=resource_type,
                                description=final_description,
                                resource_id=resource_id,
                                details=details,
                                request=request,
                                success=success,
                                error_message=error_msg
                            ))
                        else:
                            # 如果不在异步上下文中，使用run_until_complete
                            try:
                                asyncio.run(AuditService.log_action(
                                    db=db,
                                    user_id=current_user.id,
                                    action=action,
                                    resource_type=resource_type,
                                    description=final_description,
                                    resource_id=resource_id,
                                    details=details,
                                    request=request,
                                    success=success,
                                    error_message=error_msg
                                ))
                            except Exception as run_error:
                                logger.warning(f"Failed to run audit logging: {run_error}")
                    except Exception as audit_error:
                        logger.error(f"Failed to log audit action: {audit_error}")
            
            return result
        
        # 根据函数类型返回相应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 便捷装饰器
def audit_create(resource_type: AuditResourceType, description: str = "创建资源", **kwargs):
    """审计创建操作装饰器"""
    return audit_action(
        action=AuditAction.CREATE,
        resource_type=resource_type,
        description=description,
        **kwargs
    )


def audit_update(resource_type: AuditResourceType, description: str = "更新资源", **kwargs):
    """审计更新操作装饰器"""
    return audit_action(
        action=AuditAction.UPDATE,
        resource_type=resource_type,
        description=description,
        **kwargs
    )


def audit_delete(resource_type: AuditResourceType, description: str = "删除资源", **kwargs):
    """审计删除操作装饰器"""
    return audit_action(
        action=AuditAction.DELETE,
        resource_type=resource_type,
        description=description,
        **kwargs
    )


def audit_approve(resource_type: AuditResourceType, description: str = "审核通过", **kwargs):
    """审计审核通过操作装饰器"""
    return audit_action(
        action=AuditAction.APPROVE,
        resource_type=resource_type,
        description=description,
        **kwargs
    )


def audit_reject(resource_type: AuditResourceType, description: str = "审核拒绝", **kwargs):
    """审计审核拒绝操作装饰器"""
    return audit_action(
        action=AuditAction.REJECT,
        resource_type=resource_type,
        description=description,
        **kwargs
    )