import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text 

from app.core.config import settings
from app.core.scheduler import scheduler, setup_scheduler

logger = logging.getLogger(__name__)


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    
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
    
    logger.info("Iniciando a aplicação...")
    
    
    try:
        async with engine.connect() as conn:
            
            await conn.execute(text("SELECT 1"))
        logger.info("Conexão com o banco de dados estabelecida com sucesso!")
    except Exception as e:
        logger.error(f"Não foi possível conectar ao banco de dados no startup: {e}")
    
    
    try:
        setup_scheduler()
    except Exception as e:
        logger.error(f"Falha ao iniciar o scheduler: {e}")

    yield 
    
    
    logger.info("Finalizando a aplicação...")
    
    
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler finalizado.")
        
    
    await engine.dispose()
    logger.info("Conexão com DB fechada.")