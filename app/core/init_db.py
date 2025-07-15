from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole, UserFunction
from app.core.security import get_password_hash
from app.core.config import settings

async def init_superuser(db: AsyncSession) -> None:
    """
    初始化超级管理员账号
    如果超级管理员不存在，则创建一个
    """
    # 检查是否已存在超级管理员
    stmt = select(User).where(User.is_superuser == True)
    result = await db.execute(stmt)
    superuser = result.scalars().first()
    
    if not superuser:
        # 创建超级管理员账号
        superuser = User(
            phone=settings.FIRST_SUPERUSER_PHONE,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            full_name=settings.FIRST_SUPERUSER_FULL_NAME,
            role=UserRole.ADMIN,
            function=UserFunction.SALES_LOGISTICS,  # 管理员默认设置为所职能（虽然有所有权限）
            is_active=True,
            is_superuser=True
        )
        
        db.add(superuser)
        await db.commit()
        print("超级管理员账号已创建") 