from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas do .env
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    SYNC_INTERVAL_MINUTES: int = 60
    PYSUS_CACHE_DIR: str = "./.pysus_cache"
    MAP_OUTPUT_DIR: str = "./map_exports"

# Instância única para ser usada na aplicação
settings = Settings()