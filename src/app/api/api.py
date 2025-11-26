from fastapi import APIRouter
from app.api.endpoints import sync, health, reports, map

api_router = APIRouter()


api_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(map.router, prefix="/map", tags=["Map & Dashboard"])