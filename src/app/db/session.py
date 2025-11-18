import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text # <-- CORREÇÃO IMPORTADA

from app.core.config import settings
from app.core.scheduler import scheduler, setup_scheduler

logger = logging.getLogger(__name__)

# Cria a engine assíncrona
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Cria a fábrica de sessões assíncronas
AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependência do FastAPI para obter uma sessão de DB.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Erro na sessão do banco de dados: {e}")
            raise
        finally:
            await session.close()

@asynccontextmanager
async def lifespan(app):
    """
    Context manager para o lifespan do FastAPI.
    Verifica a conexão com o DB e gerencia o scheduler.
    """
    logger.info("Iniciando a aplicação...")
    
    # 1. Verifica conexão com DB
    try:
        async with engine.connect() as conn:
            # CORREÇÃO: Usando text()
            await conn.execute(text("SELECT 1"))
        logger.info("Conexão com o banco de dados estabelecida com sucesso!")
    except Exception as e:
        logger.error(f"Não foi possível conectar ao banco de dados no startup: {e}")
    
    # 2. Inicia o Scheduler
    try:
        setup_scheduler()
    except Exception as e:
        logger.error(f"Falha ao iniciar o scheduler: {e}")

    yield # A aplicação fica ativa aqui
    
    # --- Shutdown ---
    logger.info("Finalizando a aplicação...")
    
    # 3. Para o Scheduler
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler finalizado.")
        
    # 4. Fecha a engine do DB
    await engine.dispose()
    logger.info("Conexão com DB fechada.")