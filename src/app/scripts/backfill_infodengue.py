import asyncio
import logging
import sys
import os
from datetime import datetime



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from app.db.session import AsyncSessionFactory
from app.services.infodengue_sync import InfoDengueSyncService, SyncServiceError
from app.core.config import settings 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("backfill_infodengue")




EY_START = 2023
EW_START = 1


current_date = datetime(2025, 11, 16)
EY_END = current_date.year
EW_END = current_date.isocalendar().week


async def main():
    
    logger.info("--- INICIANDO BACKFILL HISTÓRICO (InfoDengue) ---")
    logger.info(f"Período de busca: {EW_START}/{EY_START} até {EW_END}/{EY_END}")
    logger.info("AVISO: Este processo pode levar vários minutos.")

    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL não encontrada. Verifique seu arquivo .env")
        sys.exit(1)

    async with AsyncSessionFactory() as session:
        try:
            service = InfoDengueSyncService(session)
            
            stats = await service.run_full_sync(
                ew_start=EW_START,
                ey_start=EY_START,
                ew_end=EW_END,
                ey_end=EY_END
            )
            
            await session.commit()
            logger.info("--- BACKFILL CONCLUÍDO ---")
            logger.info(f"Estatísticas: {stats}")

        except (SyncServiceError, Exception) as e:
            await session.rollback()
            logger.error(f"Erro fatal durante o backfill: {e}", exc_info=True)
            sys.exit(1)
        finally:
            logger.info("Fechando sessão.")

if __name__ == "__main__":
    asyncio.run(main())