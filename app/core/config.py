from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import EmailStr, field_validator, computed_field


class Settings(BaseSettings):
    """应用配置类
    
    配置加载顺序（优先级从高到低）：
    1. 环境变量：直接在系统中设置的环境变量优先级最高
    2. .env文件：如果环境变量未设置，则从.env文件中读取
    3. 默认值：如果前两者都未提供值，则使用这里定义的默认值
    """
    
    # 应用配置
    APP_NAME: str = "销售提成管理系统"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str
    
    # JWT配置
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # 邮件配置
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_TLS: bool
    MAIL_SSL: bool = False
    
    # 超级管理员配置
    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    FIRST_SUPERUSER_PHONE: str = "13800138000"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"
    FIRST_SUPERUSER_FULL_NAME: str = "System Administrator"
    
    @field_validator("DATABASE_URL")
    def assemble_db_url(cls, v: str | None, info) -> str:
        """验证并组装数据库URL
        
        如果直接提供了DATABASE_URL，则使用该值
        否则尝试从其他PostgreSQL相关配置构建URL
        """
        if isinstance(v, str):
            return v
            
        # 如果没有提供 DATABASE_URL，则从其他设置构建
        return f"postgresql+asyncpg://{info.data.get('POSTGRES_USER')}:{info.data.get('POSTGRES_PASSWORD')}@{info.data.get('POSTGRES_SERVER')}:{info.data.get('POSTGRES_PORT')}/{info.data.get('POSTGRES_DB')}"

    @computed_field
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """为SQLAlchemy提供数据库URI
        
        这是一个计算属性，返回DATABASE_URL的值
        """
        return self.DATABASE_URL
    
    class Config:
        """pydantic-settings配置
        
        env_file: 指定环境变量文件的路径
        case_sensitive: 配置大小写敏感，例如APP_NAME和app_name将被视为不同的变量
        """
        env_file = ".env"
        case_sensitive = True


settings = Settings() 