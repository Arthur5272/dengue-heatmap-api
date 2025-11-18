import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text # <-- CORREÇÃO IMPORTADA

from app.db.session import get_db
from app.core.scheduler import job_status, scheduler

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get(
    "/health", 
    summary="Verifica a saúde da aplicação, DB e Scheduler"
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Retorna o status da aplicação:
    - API: (se 200 OK, está rodando)
    - DB: Verifica a conexão
    - Scheduler: Status do último job de sincronização
    """
    
    # 1. Verifica DB
    try:
        # CORREÇÃO: Usando text()
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Health check: Falha na conexão com DB: {e}")
        db_status = "error"

    # 2. Verifica Scheduler
    scheduler_running = scheduler.running
    
    return {
        "status": "ok",
        "database_status": db_status,
        "scheduler_status": "running" if scheduler_running else "stopped",
        "last_sync_job": job_status
    }