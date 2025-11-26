from fastapi import FastAPI
from app.db.session import lifespan  
from app.api.api import api_router 
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="API de Monitoramento de Dengue",
    description="Projeto para ingestão e visualização de dados do SINAN",
    version="0.1.0",
    lifespan=lifespan 
)


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "API de Monitoramento de Dengue no ar! Acesse /docs para a documentação."}

