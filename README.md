# finance
simple finance system for sales and manager


# 数据库迁移
```
// 1. 初始化必要的文件
alembic init migrations
// 修改 alembic.ini 文件中的数据库配置，并且修改migrations/env.py文件，导入模型
// 还要加上 target_metadata = Base.metadata
// 2. 创建迁移
alembic revision --autogenerate -m "Initial migration"
// 3. 应用迁移
alembic upgrade head
```

# 启动服务