from fastapi import FastAPI
from app.db.session import lifespan  # Importa o lifespan refatorado
from app.api.api import api_router # Importaremos o router principal
import logging

# Configuração de logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="API de Monitoramento de Dengue",
    description="Projeto para ingestão e visualização de dados do SINAN",
    version="0.1.0",
    lifespan=lifespan # Usa o novo lifespan
)

# Inclui todas as rotas da API
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "API de Monitoramento de Dengue no ar! Acesse /docs para a documentação."}

# O endpoint /health foi movido para api/endpoints/health.py