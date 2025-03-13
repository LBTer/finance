from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    def init(self):
        if not self._engine:
            self._engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                future=True,
                poolclass=NullPool
            )
            self._session = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session = None

    @property
    def session(self):
        return self._session

# 创建全局单例实例
db = AsyncDatabaseSession()

# 初始化数据库会话
db.init()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    异步会话依赖函数，用于FastAPI的依赖注入
    """
    async with db.session() as session:
        try:
            yield session
        finally:
            await session.close() 