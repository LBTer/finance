from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime
from datetime import datetime, UTC


@as_declarative()
class Base:
    id: Any
    __name__: str
    
    # 根据类名生成表名
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() 
    
    # 添加通用的创建时间字段
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 添加通用的更新时间字段
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # 添加通用的序列化方法
    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    