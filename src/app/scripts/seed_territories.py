# src/app/scripts/seed_territories.py

import asyncio
import logging
import httpx
import pandas as pd
import io
import sys
import os
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import OperationalError

# Adiciona o diretório 'src' ao sys.path
# Isso permite importar 'app.core.config', etc.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from app.db.session import AsyncSessionFactory
from app.models.models import Territory
from app.core.config import settings # Garante que o .env seja lido

# URL da fonte de dados (CSV com municípios brasileiros)
# Fonte: https://github.com/kelvins/municipios-brasileiros
DATA_SOURCE_URL = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_territories")

async def fetch_municipios_csv() -> pd.DataFrame:
    """
    Baixa o CSV de municípios e o carrega em um DataFrame do Pandas.
    """
    logger.info(f"Baixando dados de municípios de {DATA_SOURCE_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(DATA_SOURCE_URL)
            response.raise_for_status() # Lança erro se o request falhar (404, 500, etc)
            
            # Usa io.StringIO para tratar o texto como um arquivo em memória
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
    """
    Limpa e transforma o DataFrame para o formato do nosso modelo Territory.
    """
    logger.info("Preparando dados (limpando e renomeando colunas)...")
    
    # Colunas que precisamos
    df_clean = df[['codigo_ibge', 'nome', 'codigo_uf']].copy()
    
    # Renomeia para bater com o nosso modelo
    df_clean.rename(columns={
        'codigo_ibge': 'geocode',
        'nome': 'name',
        'codigo_uf': 'state_code'
    }, inplace=True)
    
    # Garante que 'geocode' é uma string de 7 dígitos
    # O .astype(int) remove casas decimais, .astype(str) converte
    df_clean['geocode'] = df_clean['geocode'].astype(int).astype(str)
    
    # Remove duplicados (embora 'geocode' deva ser único)
    df_clean.drop_duplicates(subset=['geocode'], inplace=True)
    
    logger.info(f"Total de {len(df_clean)} municípios únicos preparados para inserção.")
    
    # Converte para uma lista de dicionários para o SQLAlchemy
    return df_clean.to_dict('records')

async def seed_database(territories_data: list[dict]):
    """
    Conecta ao banco e insere os dados, pulando conflitos (idempotente).
    """
    logger.info("Conectando ao banco de dados...")
    
    if not territories_data:
        logger.warning("Nenhum dado para inserir.")
        return

    async with AsyncSessionFactory() as session:
        try:
            logger.info("Iniciando a inserção dos dados na tabela 'territories'...")
            
            # Prepara a declaração de INSERT ... ON CONFLICT DO NOTHING
            # Isso torna o script seguro para rodar múltiplas vezes
            stmt = pg_insert(Territory).values(territories_data)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['geocode'] # A Primary Key
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            # result.rowcount não é confiavel no "ON CONFLICT"
            # Então apenas logamos que a operação foi concluída
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
    """
    Orquestra o processo completo de "seeding".
    """
    try:
        df = await fetch_municipios_csv()
        territories_data = prepare_data(df)
        await seed_database(territories_data)
    except Exception as e:
        logger.error(f"Falha no processo de 'seed': {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Garante que temos um .env carregado
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL não encontrada. Verifique seu arquivo .env")
        sys.exit(1)
        
    asyncio.run(main())