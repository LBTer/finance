# finance
simple finance system for sales and manager

## 🚀 快速启动

### Docker 部署（推荐）
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 服务访问地址
- **Nginx 管理界面**: http://localhost:81
- **应用系统**: 通过 nginx 代理访问（需要配置域名）
- **数据库**: localhost:15432 (仅开发调试用)

## 🔐 SSL 证书配置

### 1. 访问 Nginx Proxy Manager
1. 打开浏览器访问: http://localhost:81
2. 默认登录信息:
   - 邮箱: `admin@example.com`  
   - 密码: `changeme`
3. **首次登录后立即修改密码！**

### 2. 添加代理主机
1. 点击 "Hosts" → "Proxy Hosts" → "Add Proxy Host"
2. 配置信息:
   - **Domain Name**: 您的域名 (如: finance.yourdomain.com)
   - **Scheme**: http
   - **Forward Hostname/IP**: app
   - **Forward Port**: 8000
   - **Websockets Support**: 开启
3. 在 "SSL" 标签页:
   - **SSL Certificate**: Request a new SSL Certificate
   - **Force SSL**: 开启
   - **HTTP/2 Support**: 开启
   - **HSTS Enabled**: 开启
   - **Email**: 输入您的邮箱（用于 Let's Encrypt）
   - **Use a DNS Challenge**: 如果需要泛域名证书可选择
4. 点击 "Save" 保存

### 3. 域名解析
确保您的域名 A 记录指向服务器 IP 地址

## 🔄 证书自动续期
- Let's Encrypt 证书有效期为 90 天
- Nginx Proxy Manager 会自动续期证书
- 无需手动干预

## 🏗️ 开发环境

### 本地开发
```bash
# 环境激活
source .venv/bin/activate

# 直接启动后端（开发模式）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📦 部署说明

### 生产部署
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
docker-compose logs -f nginx-proxy-manager
```

### 跨平台部署
```bash
# 如果目标平台架构不同，先本地编译镜像
# 1. 修改 docker-compose.yml 中的 platform 字段
# 2. 构建并导出镜像
docker-compose build app
docker save finance-app:latest > finance-app.tar

# 3. 在目标服务器导入镜像
docker load < finance-app.tar  
docker-compose up -d
```

## 🗄️ 数据库管理

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

# 部署
```
# 本地启动
docker compose up -d
# 如果平台上无法部署，先本地编译镜像（注意替换docker-compose.yml文件中的架构），然后上传
docker save finance-app:latest > myapp.tar
docker load < myapp.tar  
```