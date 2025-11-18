import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Adiciona o diretório 'src' ao sys.path
import os
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# Importa as configurações e a Base dos modelos
from app.core.config import settings
# IMPORTANTE: Atualizado para o novo models.py
from app.models.models import Base 

# Configuração do Alembic
config = context.config

# Interpreta o arquivo de config para o logging do Python.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define a URL do banco de dados a partir das nossas settings
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Define o metadata dos modelos para o Alembic 'autogenerate'
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """
    Roda migrações no modo 'offline'.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Função de callback para rodar as migrações.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Roda migrações no modo 'online' (conectado ao DB).
    Configurado para asyncio.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())