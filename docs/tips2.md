**第1步 - 项目初始化和基础结构：**
```
请帮我使用Python 3.12创建一个销售提成管理系统的基础结构，要求如下：

1. 使用以下技术栈：
- FastAPI
- SQLAlchemy
- Pydantic
- FastAPI-users
- FastAPI-JWT-Auth
- Alembic

2. 请创建以下目录结构：
/app
  /api
  /core
  /db
  /models
  /schemas
  /services
  /utils
  main.py
/alembic
/tests
requirements.txt
.env.example

3. 在core目录下创建：
- config.py（配置文件）
- security.py（安全相关）
- dependencies.py（依赖注入）

请生成这些基础文件的代码，并包含必要的依赖配置。
```

**第2步 - 数据库模型：**
```
请为销售提成管理系统创建数据库模型，需要包含以下内容：

1. 在 app/models/ 目录下创建以下模型：
- user.py：用户模型，包含：
  * id, email, password_hash, full_name
  * role (普通用户/高级用户/超级管理员)
  * is_active, created_at, updated_at

- sales_record.py：销售记录模型，包含：
  * id, order_number
  * user_id（关联用户）
  * product_name, quantity, unit_price
  * shipping_fee, refund_amount, tax_refund
  * status（待审核/已审核/已拒绝）
  * created_at, updated_at
  * remarks

请使用SQLAlchemy模型创建这些表，并添加适当的关系和约束。
```

**第3步 - Pydantic Schemas：**
```
请为之前创建的数据库模型创建对应的Pydantic schemas，要求：

1. 在 app/schemas/ 目录下创建：
- user.py：用户相关的schema
  * UserCreate
  * UserUpdate
  * UserResponse
  * UserInDB

- sales_record.py：销售记录相关的schema
  * SalesRecordCreate
  * SalesRecordUpdate
  * SalesRecordResponse
  * SalesRecordInDB

所有schema都需要包含适当的字段验证和类型提示。
```

**第4步 - API路由：**
```
请创建API路由，实现以下功能：

1. 在 app/api/v1/ 目录下创建：
- auth.py：认证相关路由
  * 登录
  * 注册（仅管理员可用）
  * 密码重置

- sales.py：销售记录相关路由
  * 创建销售记录
  * 获取销售记录列表（带分页）
  * 获取单个销售记录详情
  * 更新销售记录
  * 删除销售记录

请确保添加适当的权限控制和错误处理。
```

**第5步 - 权限控制：**
```
请实现权限控制系统，要求：

1. 在 app/core/permissions.py 中实现：
- 基于角色的权限控制
- 自定义权限装饰器

2. 权限规则：
- 销售只能访问自己的记录
- 总理可以查看所有记录并审核
- 管理员拥有所有权限

请实现必要的中间件和辅助函数。
```

**第6步 - 工具函数和测试：**
```
请添加必要的工具函数和测试用例：

1. 在 app/utils/ 目录下创建：
- excel.py：Excel导出功能
- validators.py：自定义验证器

2. 在 tests/ 目录下创建：
- test_auth.py：认证相关测试
- test_sales.py：销售记录相关测试
- test_permissions.py：权限相关测试
