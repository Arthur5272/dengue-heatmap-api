

import asyncio
import logging
import httpx
import pandas as pd
import io
import sys
import os
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import OperationalError



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from app.db.session import AsyncSessionFactory
from app.models.models import Territory
from app.core.config import settings 



DATA_SOURCE_URL = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_territories")

async def fetch_municipios_csv() -> pd.DataFrame:
    
    logger.info(f"Baixando dados de municípios de {DATA_SOURCE_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(DATA_SOURCE_URL)
            response.raise_for_status() 
            
            
            csv_data = io.StringIO(response.text)
            df = pd.read_csv(csv_data)
            logger.info(f"Total de {len(df)} municípios baixados.")
            return df
        except httpx.HTTPStatusError as e:
            logger.error(f"Falha ao baixar o arquivo CSV: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao processar o CSV: {e}")
            raise

def prepare_data(df: pd.DataFrame) -> list[dict]:
    
    logger.info("Preparando dados (limpando e renomeando colunas)...")
    
    
    df_clean = df[['codigo_ibge', 'nome', 'codigo_uf']].copy()
    
    
    df_clean.rename(columns={
        'codigo_ibge': 'geocode',
        'nome': 'name',
        'codigo_uf': 'state_code'
    }, inplace=True)
    
    
    
    df_clean['geocode'] = df_clean['geocode'].astype(int).astype(str)
    
    
    df_clean.drop_duplicates(subset=['geocode'], inplace=True)
    
    logger.info(f"Total de {len(df_clean)} municípios únicos preparados para inserção.")
    
    
    return df_clean.to_dict('records')

async def seed_database(territories_data: list[dict]):
    
    logger.info("Conectando ao banco de dados...")
    
    if not territories_data:
        logger.warning("Nenhum dado para inserir.")
        return

    async with AsyncSessionFactory() as session:
        try:
            logger.info("Iniciando a inserção dos dados na tabela 'territories'...")
            
            
            
            stmt = pg_insert(Territory).values(territories_data)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['geocode'] 
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            
            
            logger.info("Operação de 'seed' concluída.")
            logger.info("O banco de dados de territórios está populado.")

        except OperationalError as e:
            logger.error(f"Erro de conexão com o banco. Verifique a DATABASE_URL e se o DB está rodando. Erro: {e}")
            await session.rollback()
        except Exception as e:
            logger.error(f"Erro durante a inserção no banco: {e}")
            await session.rollback()
            raise

async def main():
    
    try:
        df = await fetch_municipios_csv()
        territories_data = prepare_data(df)
        await seed_database(territories_data)
    except Exception as e:
        logger.error(f"Falha no processo de 'seed': {e}")
        sys.exit(1)

if __name__ == "__main__":
    
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL não encontrada. Verifique seu arquivo .env")
        sys.exit(1)
        
    asyncio.run(main())