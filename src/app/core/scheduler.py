# src/app/core/scheduler.py

import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
# REMOVIDO: from app.services.pysus_sync import PysusSyncService
# ADICIONADO:
from app.services.infodengue_sync import InfoDengueSyncService, SyncServiceError

logger = logging.getLogger(__name__)

job_status = {
    "last_run_time": None,
    "last_run_status": "Not Started",
    "last_run_error": None
}

async def scheduled_sync_job():
    """
    Função que o scheduler irá executar.
    Agora usa o InfoDengueSyncService.
    """
    from app.db.session import AsyncSessionFactory 
    
    logger.info("Iniciando job de sincronização agendado (InfoDengue)...")
    job_status["last_run_status"] = "Running"
    
    # O InfoDengueSyncService já calcula a janela de tempo padrão (últimas 8 semanas)
    
    async with AsyncSessionFactory() as session:
        try:
            # --- MUDANÇA AQUI ---
            service = InfoDengueSyncService(session)
            # Roda o sync com a janela de tempo padrão
            stats = await service.run_full_sync() 
            await session.commit()
            # --- FIM DA MUDANÇA ---
            
            logger.info(f"Job de sincronização agendado concluído. Stats: {stats}")
            job_status["last_run_status"] = "Success"
            job_status["last_run_error"] = None
            
        except (SyncServiceError, Exception) as e:
            await session.rollback()
            logger.error(f"Erro no job de sincronização agendado (InfoDengue): {e}", exc_info=True)
            job_status["last_run_status"] = "Failed"
            job_status["last_run_error"] = str(e)
            
        finally:
            await session.close()
            job_status["last_run_time"] = datetime.now()

# Instância única do Scheduler
scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")

def setup_scheduler():
    """
    Configura e inicia o scheduler e o job.
    """
    logger.info("Configurando o scheduler...")
    
    scheduler.add_job(
        scheduled_sync_job,
        trigger=IntervalTrigger(minutes=settings.SYNC_INTERVAL_MINUTES),
        id="full_sync_job",
        # --- MUDANÇA AQUI ---
        name="Sincronização InfoDengue (AlertCity)",
        replace_existing=True,
    )
    
    try:
        scheduler.start()
        logger.info("Scheduler iniciado com sucesso.")
    except Exception as e:
        logger.error(f"Não foi possível iniciar o scheduler: {e}")