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
alembic upgrade heads
// 另外，在你第一次执行upgrade的时候，就会在数据库中创建一个名叫alembic_version表，这个表只会有一条数据，记录当前数据库映射的是哪个版本的迁移文件


// 降级
alembic downgrade head


// 后续更新表内容
alembic revision --autogenerate -m "message"
alembic upgrade head
// 4. 撤回迁移

```
参考：https://hellowac.github.io/technology/python/alembic/


# 启动服务
```
// 环境激活
source .venv/bin/activate
// 后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```