import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, select, func
from sqlalchemy.orm import selectinload
from fastapi import Request

from app.models.audit_log import AuditLog, AuditAction, AuditResourceType
from app.models.user import User
from app.schemas.audit_log import AuditLogCreate, AuditLogQuery, AuditLogResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuditService:
    """审计服务类"""
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: Optional[int],
        action: AuditAction,
        resource_type: AuditResourceType,
        description: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        记录审计日志
        
        Args:
            db: 数据库会话
            user_id: 操作用户ID
            action: 操作类型
            resource_type: 资源类型
            description: 操作描述
            resource_id: 资源ID
            details: 详细信息字典
            request: FastAPI请求对象
            success: 操作是否成功
            error_message: 错误信息
            
        Returns:
            创建的审计日志对象
        """
        try:
            # 从请求中提取IP和User-Agent
            ip_address = None
            user_agent = None
            if request:
                # 获取真实IP地址（考虑代理）
                ip_address = (
                    request.headers.get("X-Forwarded-For", "")
                    or request.headers.get("X-Real-IP", "")
                    or request.client.host if request.client else None
                )
                if ip_address and "," in ip_address:
                    ip_address = ip_address.split(",")[0].strip()
                
                user_agent = request.headers.get("User-Agent")
            
            # 将详细信息转换为JSON字符串
            details_json = None
            if details:
                try:
                    details_json = json.dumps(details, ensure_ascii=False, default=str)
                except Exception as e:
                    logger.warning(f"Failed to serialize audit details: {e}")
                    details_json = str(details)
            
            # 创建审计日志
            audit_log = AuditLog(
                user_id=user_id,
                action=action.value,
                resource_type=resource_type.value,
                resource_id=resource_id,
                description=description,
                details=details_json,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            db.add(audit_log)
            await db.commit()
            await db.refresh(audit_log)
            
            logger.info(
                f"Audit log created: user_id={user_id}, action={action.value}, "
                f"resource_type={resource_type.value}, resource_id={resource_id}, "
                f"success={success}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        query: AuditLogQuery
    ) -> tuple[List[AuditLogResponse], int]:
        """
        查询审计日志
        
        Args:
            db: 数据库会话
            query: 查询参数
            
        Returns:
            (审计日志列表, 总数)
        """
        # 构建查询条件
        conditions = []
        
        if query.user_id is not None:
            conditions.append(AuditLog.user_id == query.user_id)
        
        if query.action:
            conditions.append(AuditLog.action == query.action)
        
        if query.resource_type:
            conditions.append(AuditLog.resource_type == query.resource_type)
        
        if query.resource_id is not None:
            conditions.append(AuditLog.resource_id == query.resource_id)
        
        if query.success is not None:
            conditions.append(AuditLog.success == query.success)
        
        if query.start_date:
            conditions.append(AuditLog.created_at >= query.start_date)
        
        if query.end_date:
            conditions.append(AuditLog.created_at <= query.end_date)
        
        # 构建基础查询
        base_query = select(AuditLog).options(selectinload(AuditLog.user))
        
        if conditions:
            base_query = base_query.filter(and_(*conditions))
        
        # 获取总数
        count_query = select(func.count(AuditLog.id))
        if conditions:
            count_query = count_query.filter(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        paginated_query = (
            base_query
            .order_by(desc(AuditLog.created_at))
            .offset((query.page - 1) * query.size)
            .limit(query.size)
        )
        
        result = await db.execute(paginated_query)
        audit_logs = result.scalars().all()
        
        # 转换为响应格式
        responses = []
        for log in audit_logs:
            response_data = {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": log.user.full_name if log.user else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "success": log.success,
                "error_message": log.error_message,
                "created_at": log.created_at,
                "updated_at": log.updated_at
            }
            responses.append(AuditLogResponse(**response_data))
        
        return responses, total
    
    @staticmethod
    async def get_audit_log_by_id(
        db: AsyncSession,
        log_id: int
    ) -> Optional[AuditLogResponse]:
        """
        根据ID获取单个审计日志
        
        Args:
            db: 数据库会话
            log_id: 审计日志ID
            
        Returns:
            审计日志详情或None
        """
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .filter(AuditLog.id == log_id)
        )
        
        result = await db.execute(query)
        log = result.scalar_one_or_none()
        
        if not log:
            return None
        
        response_data = {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.full_name if log.user else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "success": log.success,
            "error_message": log.error_message,
            "created_at": log.created_at,
            "updated_at": log.updated_at
        }
        
        return AuditLogResponse(**response_data)
    
    @staticmethod
    async def get_user_recent_actions(
        db: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[AuditLogResponse]:
        """
        获取用户最近的操作记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            用户最近的操作记录列表
        """
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .filter(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        
        result = await db.execute(query)
        audit_logs = result.scalars().all()
        
        responses = []
        for log in audit_logs:
            response_data = {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": log.user.full_name if log.user else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "success": log.success,
                "error_message": log.error_message,
                "created_at": log.created_at,
                "updated_at": log.updated_at
            }
            responses.append(AuditLogResponse(**response_data))
        
        return responses


# 便捷函数
async def log_create_action(
    db: AsyncSession,
    user_id: Optional[int],
    resource_type: AuditResourceType,
    resource_id: int,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """记录创建操作"""
    return await AuditService.log_action(
        db=db,
        user_id=user_id,
        action=AuditAction.CREATE,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        details=details,
        request=request
    )


async def log_update_action(
    db: AsyncSession,
    user_id: Optional[int],
    resource_type: AuditResourceType,
    resource_id: int,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """记录更新操作"""
    return await AuditService.log_action(
        db=db,
        user_id=user_id,
        action=AuditAction.UPDATE,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        details=details,
        request=request
    )


async def log_delete_action(
    db: AsyncSession,
    user_id: Optional[int],
    resource_type: AuditResourceType,
    resource_id: int,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """记录删除操作"""
    return await AuditService.log_action(
        db=db,
        user_id=user_id,
        action=AuditAction.DELETE,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        details=details,
        request=request
    )