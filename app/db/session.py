import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    def init(self):
        if not self._engine:
            # 使用asyncpg驱动，并配置日期时间处理
            self._engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                # 添加日期时间处理选项
                connect_args={
                    "server_settings": {
                        "timezone": "UTC"
                    },
                    # 添加日期时间处理器
                    "command_timeout": 60
                },
                json_serializer=lambda obj: obj,  # 防止JSON序列化错误
            )
            self._session = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
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
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话异常: {e}")
            raise e
        finally:
            await session.close() 