from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import os

from app.core.config import settings
from app.core.init_db import init_superuser
from app.db.session import db
from app.api.v1 import api_router
from app.utils.logger import init_logger, get_logger

# 初始化日志系统
log_level = os.getenv("LOG_LEVEL", "INFO")
log_dir = os.getenv("LOG_DIR", "logs")
init_logger(
    log_level=log_level,
    log_dir=log_dir,
    app_name="finance_system",
    enable_console=True,
    enable_file=True
)

# 获取logger实例
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="static/pages")

@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行的操作
    """
    logger.info("开始初始化应用...")
    
    async with db.session() as session:
        try:
            logger.info("初始化超级用户...")
            await init_superuser(session)
            logger.info("超级用户初始化完成")
        except Exception as e:
            logger.error(f"初始化超级用户失败: {str(e)}", exc_info=True)
            raise
        finally:
            await session.close()
    
    logger.info("应用初始化完成")

@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时执行的操作
    """
    logger.info("应用正在关闭...")

# 添加API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 主页路由 - 重定向到登录页
@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/login")

# 登录页面
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 仪表盘页面
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# 销售记录页面
@app.get("/sales", response_class=HTMLResponse)
async def sales_page(request: Request):
    return templates.TemplateResponse("sales.html", {"request": request})

# 用户管理页面
@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request}) 

# 运费管理页面
@app.get("/fees", response_class=HTMLResponse)
async def fees_page(request: Request):
    return templates.TemplateResponse("fees.html", {"request": request})

# 采购管理页面
@app.get("/procurement", response_class=HTMLResponse)
async def procurement_page(request: Request):
    return templates.TemplateResponse("procurement.html", {"request": request})

# 审计记录页面
@app.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    return templates.TemplateResponse("audit.html", {"request": request})

