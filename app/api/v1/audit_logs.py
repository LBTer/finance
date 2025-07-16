from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AsyncSessionDep, get_current_user
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogQuery, AuditLogResponse
from app.services.audit_service import AuditService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def get_audit_logs(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[int] = Query(None, description="资源ID"),
    success: Optional[bool] = Query(None, description="操作是否成功"),
    start_date: Optional[str] = Query(None, description="开始时间 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束时间 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取审计日志列表
    
    只有管理员和高级用户可以查看所有审计日志
    普通用户只能查看自己的操作记录
    """
    try:
        # 权限检查
        if current_user.role not in [UserRole.ADMIN.value, UserRole.SENIOR.value]:
            # 普通用户只能查看自己的记录
            if user_id is not None and user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="普通用户只能查看自己的操作记录"
                )
            user_id = current_user.id
        
        # 解析日期
        start_datetime = None
        end_datetime = None
        if start_date:
            try:
                from datetime import datetime
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="开始时间格式错误，请使用 YYYY-MM-DD 格式"
                )
        
        if end_date:
            try:
                from datetime import datetime, time
                end_datetime = datetime.combine(
                    datetime.strptime(end_date, "%Y-%m-%d").date(),
                    time(23, 59, 59)
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="结束时间格式错误，请使用 YYYY-MM-DD 格式"
                )
        
        # 构建查询参数
        query = AuditLogQuery(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            start_date=start_datetime,
            end_date=end_datetime,
            page=page,
            size=size
        )
        
        # 查询审计日志
        audit_logs, total = await AuditService.get_audit_logs(db, query)
        
        return {
            "items": audit_logs,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取审计日志失败"
        )


@router.get("/recent", response_model=List[AuditLogResponse])
async def get_recent_actions(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(10, ge=1, le=50, description="返回数量限制")
):
    """
    获取当前用户最近的操作记录
    """
    try:
        audit_logs = await AuditService.get_user_recent_actions(
            db=db,
            user_id=current_user.id,
            limit=limit
        )
        
        return audit_logs
        
    except Exception as e:
        logger.error(f"Failed to get recent actions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取最近操作记录失败"
        )


@router.get("/stats", response_model=dict)
async def get_audit_stats(
    db: AsyncSessionDep,
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=365, description="统计天数")
):
    """
    获取审计统计信息
    
    只有管理员和高级用户可以查看统计信息
    """
    try:
        # 权限检查
        if current_user.role not in [UserRole.ADMIN.value, UserRole.SENIOR.value]:
            raise HTTPException(
                status_code=403,
                detail="权限不足，只有管理员和高级用户可以查看统计信息"
            )
        
        from datetime import datetime, timedelta
        from app.models.audit_log import AuditLog
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 总操作数
        total_operations_result = await db.execute(
            select(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date
                )
            )
        )
        total_operations = total_operations_result.scalar()
        
        # 成功操作数
        successful_operations_result = await db.execute(
            select(func.count(AuditLog.id)).filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date,
                    AuditLog.success == True
                )
            )
        )
        successful_operations = successful_operations_result.scalar()
        
        # 失败操作数
        failed_operations = total_operations - successful_operations
        
        # 按操作类型统计
        action_stats_result = await db.execute(
            select(AuditLog.action, func.count(AuditLog.id).label('count'))
            .filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date
                )
            )
            .group_by(AuditLog.action)
        )
        action_stats = action_stats_result.all()
        
        # 按资源类型统计
        resource_stats_result = await db.execute(
            select(AuditLog.resource_type, func.count(AuditLog.id).label('count'))
            .filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date
                )
            )
            .group_by(AuditLog.resource_type)
        )
        resource_stats = resource_stats_result.all()
        
        # 活跃用户统计
        active_users_result = await db.execute(
            select(func.count(func.distinct(AuditLog.user_id)))
            .filter(
                and_(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date,
                    AuditLog.user_id.isnot(None)
                )
            )
        )
        active_users = active_users_result.scalar()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "success_rate": round(successful_operations / total_operations * 100, 2) if total_operations > 0 else 0,
                "active_users": active_users
            },
            "action_stats": {action: count for action, count in action_stats},
            "resource_stats": {resource_type: count for resource_type, count in resource_stats}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取审计统计信息失败"
        )