from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone


@as_declarative()
class Base:
    id: Any
    __name__: str
    
    # 根据类名生成表名
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() 
    
    # 添加通用的创建时间字段 - 使用timezone代替UTC并确保一致性
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # 添加通用的更新时间字段 - 使用timezone代替UTC并确保一致性
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 添加通用的序列化方法
    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    