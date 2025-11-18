from fastapi import APIRouter
from app.api.endpoints import sync, health # Adiciona health

api_router = APIRouter()

# Inclui as rotas
api_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
api_router.include_router(health.router, tags=["Health"]) # Adiciona health