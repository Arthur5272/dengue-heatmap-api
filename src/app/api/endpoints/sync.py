# src/app/api/endpoints/sync.py

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionFactory
# REMOVIDO: from app.services.pysus_sync import PysusSyncService, SyncServiceError
# ADICIONADO:
from app.services.infodengue_sync import InfoDengueSyncService, SyncServiceError

logger = logging.getLogger(__name__)
router = APIRouter()

# --- MUDANÇA AQUI ---
# O request agora aceita uma janela de tempo (opcional)
class SyncRequest(BaseModel):
    ew_start: Optional[int] = None
    ey_start: Optional[int] = None
    ew_end: Optional[int] = None
    ey_end: Optional[int] = None

class SyncResponse(BaseModel):
    message: str
    task_id: str | None = None
    time_window: dict
    stats: dict | None = None

@router.post(
    "/sync", 
    response_model=SyncResponse,
    summary="Aciona a sincronização dos dados do InfoDengue em background"
)
async def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Inicia o processo de sincronização do InfoDengue em background.
    Se nenhuma janela de tempo for fornecida, usa o padrão (últimas 8 semanas).
    """
    
    time_window = request.model_dump()
    
    async def background_sync_task(params: dict):
        async with AsyncSessionFactory() as session:
            try:
                # --- MUDANÇA AQUI ---
                service = InfoDengueSyncService(session)
                logger.info(f"Iniciando task de sincronização (InfoDengue) em background com params: {params}")
                stats = await service.run_full_sync(**params)
                await session.commit()
                logger.info(f"Task de sincronização (InfoDengue) em background concluída. Stats: {stats}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Erro na task de sincronização (InfoDengue) em background: {e}")
            finally:
                await session.close()
    
    background_tasks.add_task(background_sync_task, time_window)
    
    return SyncResponse(
        message="Sincronização (InfoDengue) iniciada em background.",
        time_window=time_window
    )

@router.post(
    "/sync/wait", 
    response_model=SyncResponse,
    summary="Aciona a sincronização (InfoDengue) e aguarda o resultado"
)
async def trigger_sync_and_wait(
    request: SyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Inicia a sincronização do InfoDengue e aguarda a conclusão.
    **Atenção:** Pode levar vários minutos e causar timeout.
    """
    
    time_window = request.model_dump()
    logger.info(f"Iniciando sincronização (InfoDengue - aguardando) com params: {time_window}")
    
    try:
        # --- MUDANÇA AQUI ---
        service = InfoDengueSyncService(db)
        stats = await service.run_full_sync(**time_window)
        # Commit é tratado pelo 'get_db'
        
        return SyncResponse(
            message="Sincronização (InfoDengue) concluída.",
            time_window=time_window,
            stats=stats
        )
    except SyncServiceError as e:
        logger.error(f"Falha na sincronização 'wait' (InfoDengue): {e}")
        raise HTTPException(status_code=500, detail=str(e))