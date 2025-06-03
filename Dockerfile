# 使用Python 3.12官方镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（构建psycopg2所需）
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install uv

# 复制项目文件
COPY . .

# 替换alembic.ini中的数据库地址
RUN sed -i 's/localhost:15432/postgres:5432/g' alembic.ini

# 创建虚拟环境并安装依赖
RUN uv venv 
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -e .

# 创建启动脚本
RUN echo '#!/bin/bash\n\
echo "等待数据库连接..."\n\
sleep 5\n\
echo "运行数据库迁移..."\n\
/app/.venv/bin/python -m alembic upgrade head\n\
echo "启动应用..."\n\
/app/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/start.sh

# 给启动脚本执行权限
RUN chmod +x /app/start.sh

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# 启动命令
CMD ["/app/start.sh"] 