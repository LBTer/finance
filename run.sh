#!/bin/bash

echo "安装依赖..."
uv pip install -r requirements.txt

echo "启动应用程序..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 