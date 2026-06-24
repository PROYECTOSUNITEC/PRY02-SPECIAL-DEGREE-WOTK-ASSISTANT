import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Secure RAG BFF Gateway"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENV: str = os.getenv("ENV", "development")  # "development" o "production"
    
    # JWT & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_unsecure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # RAG Internal Config (simulado o apuntando a un servicio interno)
    RAG_INTERNAL_WS_URL: str = os.getenv("RAG_INTERNAL_WS_URL", "ws://localhost:8001/v1/chat")

    class Config:
        case_sensitive = True

    def __init__(self, **values):
        super().__init__(**values)
        # Salvaguarda de seguridad en producción
        if self.ENV == "production" and self.SECRET_KEY == "dev_secret_key_unsecure":
            raise ValueError(
                "¡ERROR CRÍTICO DE CONFIGURACIÓN! En entorno de producción (ENV='production'), "
                "se DEBE configurar la variable de entorno 'SECRET_KEY' con una clave fuerte y secreta."
            )

settings = Settings()
