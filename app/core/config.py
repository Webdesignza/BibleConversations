"""
Configuration Management
Loads environment variables and application settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # API Security
    API_KEY: str
    
    # Application Settings
    CHROMA_DB_PATH: str = "./chroma_db"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Model Configuration
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.3
    RETRIEVAL_K: int = 3
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance"""
    return Settings()