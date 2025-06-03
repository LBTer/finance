# Docker 部署说明

## 概述

本项目使用 Docker Compose 进行容器化部署，包含以下组件：
- **应用服务 (app)**: FastAPI应用
- **数据库服务 (db)**: PostgreSQL 15

## 快速开始

### 1. 构建并启动所有服务
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看应用日志
docker-compose logs -f app
```

### 2. 访问应用
- **应用地址**: http://localhost:8000
- **销售记录页面**: http://localhost:8000/sales
- **用户管理页面**: http://localhost:8000/users
- **登录页面**: http://localhost:8000/login

### 3. 默认管理员账户
- **邮箱**: admin@example.com
- **密码**: admin123
- **角色**: 超级管理员

## 常用命令

### 服务管理
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启应用服务
docker-compose restart app

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [service_name]
```

### 数据库管理
```bash
# 连接到数据库容器
docker-compose exec db psql -U finance_user -d finance_db

# 查看数据库日志
docker-compose logs -f db

# 重启数据库
docker-compose restart db
```

### 应用管理
```bash
# 重新构建应用镜像
docker-compose build app

# 强制重新构建（无缓存）
docker-compose build --no-cache app

# 查看应用日志
docker-compose logs -f app

# 进入应用容器
docker-compose exec app bash
```

## 环境配置

### 数据库配置
- **数据库名**: finance_db
- **用户名**: finance_user  
- **密码**: finance_password
- **端口**: 5432

### 应用配置
以下环境变量可在 `docker-compose.yml` 中修改：

```yaml
environment:
  # 数据库连接
  DATABASE_URL: postgresql+asyncpg://finance_user:finance_password@db:5432/finance_db
  
  # 应用基础配置
  APP_NAME: 财务管理系统
  SECRET_KEY: your-super-secret-key-change-in-production
  ALGORITHM: HS256
  ACCESS_TOKEN_EXPIRE_MINUTES: 30
  
  # 日志配置
  LOG_LEVEL: INFO
  LOG_DIR: logs
  
  # 超级管理员配置
  SUPERUSER_EMAIL: admin@example.com
  SUPERUSER_PASSWORD: admin123
  SUPERUSER_FULL_NAME: 系统管理员
```

## 故障排查

### 1. 应用无法启动
```bash
# 查看应用日志
docker-compose logs app

# 检查数据库是否已启动
docker-compose ps db

# 重新构建应用镜像
docker-compose build --no-cache app
```

### 2. 数据库连接失败
```bash
# 检查数据库健康状态
docker-compose ps

# 查看数据库日志
docker-compose logs db

# 测试数据库连接
docker-compose exec db pg_isready -U finance_user -d finance_db
```

### 3. 数据库迁移失败
```bash
# 进入应用容器手动运行迁移
docker-compose exec app alembic upgrade head

# 查看迁移历史
docker-compose exec app alembic history

# 查看当前迁移版本
docker-compose exec app alembic current
```

### 4. 清理和重置
```bash
# 停止并删除所有容器
docker-compose down

# 清理所有相关数据
docker-compose down -v

# 重新开始
docker-compose up -d --build
```

## 生产环境部署

### 安全配置
在生产环境中，请务必修改以下配置：

1. **修改数据库密码**:
```yaml
environment:
  POSTGRES_PASSWORD: 使用强密码
```

2. **修改SECRET_KEY**:
```yaml
environment:
  SECRET_KEY: 使用随机生成的强密钥
```

3. **修改管理员密码**:
```yaml
environment:
  SUPERUSER_PASSWORD: 使用强密码
```

### 网络配置
```yaml
services:
  db:
    ports: []  # 移除端口映射，不暴露数据库端口
    
  app:
    ports:
      - "8000:8000"  # 或使用反向代理
```

### 日志管理
```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 技术细节

### 自动化流程
1. **应用启动流程**:
   - 等待数据库健康检查通过
   - 运行数据库迁移 (`alembic upgrade head`)
   - 初始化超级管理员账户
   - 启动FastAPI应用

2. **依赖管理**:
   - 使用 `uv` 进行快速依赖安装
   - 自动安装所有Python依赖

3. **数据库迁移**:
   - 容器启动时自动运行最新迁移
   - 无需手动干预

### 镜像信息
- **基础镜像**: python:3.12-slim
- **Python版本**: 3.12
- **包管理器**: uv
- **数据库**: PostgreSQL 15 