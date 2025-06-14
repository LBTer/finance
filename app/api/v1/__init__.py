from fastapi import APIRouter
from .auth import router as auth_router
from .sales import router as sales_router
from .stats import router as stats_router
from .users import router as users_router
from .attachments import router as attachments_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(sales_router)
api_router.include_router(stats_router)
api_router.include_router(users_router)
api_router.include_router(attachments_router) 