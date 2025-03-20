from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import EmailStr, field_validator, computed_field


class Settings(BaseSettings):
    """应用配置类"""
    
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
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    
    @field_validator("DATABASE_URL")
    def assemble_db_url(cls, v: str | None, info) -> str:
        if isinstance(v, str):
            return v
            
        # 如果没有提供 DATABASE_URL，则从其他设置构建
        return f"postgresql://{info.data.get('POSTGRES_USER')}:{info.data.get('POSTGRES_PASSWORD')}@{info.data.get('POSTGRES_SERVER')}:{info.data.get('POSTGRES_PORT')}/{info.data.get('POSTGRES_DB')}"

    @computed_field
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 