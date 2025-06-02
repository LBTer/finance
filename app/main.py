from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.config import settings
from app.core.init_db import init_superuser
from app.db.session import db
from app.api.v1 import api_router

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
    async with db.session() as session:
        try:
            await init_superuser(session)
        finally:
            await session.close()

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