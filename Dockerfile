# 使用Python 3.11官方镜像
FROM python:3.11.8-slim

# 设置工作目录
WORKDIR /app

# # 1. 修复系统时间问题（最关键步骤）
# RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
#     echo "Asia/Shanghai" > /etc/timezone && \
#     # 安装ntpdate确保时间准确
#     apt-get update && \
#     DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
#         ca-certificates \
#         tzdata \
#         ntpdate && \
#     # 同步系统时间
#     ntpdate -s time.nist.gov || ntpdate -s ntp.ubuntu.com || true && \
#     # 清理
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# 适配新版本 Debian 的 DEB822 格式源配置
# 替换为国内镜像源（避免清华限制，改用阿里云）
RUN if [ -f /etc/apt/sources.list ]; then \
        sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list && \
        sed -i 's|http://security.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list; \
    fi && \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
        sed -i 's|http://security.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    fi

# 安装系统依赖（构建psycopg2所需）
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install --upgrade pip
RUN pip install uv

# 创建文件目录
RUN mkdir -p /app/files

# 复制项目文件
COPY . .

# 替换alembic.ini中的数据库地址
RUN sed -i 's/localhost:15432/postgres:5432/g' alembic.ini

# 创建虚拟环境并安装依赖
# RUN uv venv /app/.venv && \
#     . /app/.venv/bin/activate && \
#     uv pip install --upgrade pip setuptools wheel && \
#     uv pip install psycopg2-binary && \
#     uv pip install -e .
# 创建虚拟环境并安装依赖
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -e .

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

# 启动命令，不需要启动服务，等待即可
CMD ["/app/start.sh"]
# CMD ["tail", "-f", "/dev/null"]