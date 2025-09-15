"""
Configuration settings for the Digital Twin application.
"""
import os
from typing import List, Optional

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Digital Twin"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        """Parse CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Vector Database Settings
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    COLLECTION_NAME: str = "digital_twin_knowledge"
    
    # Obsidian Settings
    OBSIDIAN_VAULT_PATH: Optional[str] = None
    OBSIDIAN_VAULT_NAME: str = "Digital Twin Vault"
    
    # File Processing Settings
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Database Settings (optional for future use)
    DATABASE_URL: Optional[str] = None
    
    # Redis Settings (for caching and background tasks)
    REDIS_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()
