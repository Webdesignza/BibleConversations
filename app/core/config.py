"""
Configuration settings for the RAG FastAPI application
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    OPENAI_API_KEY: str
    GROQ_API_KEY: str = ""
    
    # Model Configuration
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "llama-3.1-70b-versatile"
    
    # Groq API
    GROQ_API_BASE: str = "https://api.groq.com/openai/v1"
    
    # RAG Configuration
    CHROMA_DB_PATH: str = "./chroma_db"
    RETRIEVAL_K: int = 3
    TEMPERATURE: float = 0.7
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8007
    
    # Security
    API_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()