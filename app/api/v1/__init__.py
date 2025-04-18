from fastapi import APIRouter
from .auth import router as auth_router
from .sales import router as sales_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(sales_router) 