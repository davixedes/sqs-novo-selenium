from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configurações gerais da aplicação.
    """
    DATABASE_URL: str
    AWS_SQS_QUEUE_URL: str
    CAPMONSTER_CLIENT_KEY: str  # Chave de cliente do CapMonster
    CAPMONSTER_ENDPOINT: str = "https://api.capmonster.cloud"  # Endpoint da API do CapMonster

    class Config:
        env_file = ".env"

settings = Settings()