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
    
    # AI Provider Settings
    AI_PRIMARY_PROVIDER: str = "together"  # together, bedrock, openai
    AI_FALLBACK_PROVIDER: str = "bedrock"
    
    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # AWS Bedrock Settings
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    BEDROCK_MODEL: str = "anthropic.claude-3-haiku-20240307-v1:0"
    BEDROCK_EMBEDDING_MODEL: str = "amazon.titan-embed-text-v1"
    
    # Together AI Settings
    TOGETHER_API_KEY: Optional[str] = None
    TOGETHER_MODEL: str = "meta-llama/Llama-3.1-8B-Instruct-Turbo"
    TOGETHER_EMBEDDING_MODEL: str = "togethercomputer/m2-bert-80M-8k-retrieval"
    
    # Smart Routing Settings
    SIMPLE_QUERY_MAX_WORDS: int = 15
    SIMPLE_QUERY_PATTERNS: List[str] = ["what", "when", "where", "who", "how many", "hello", "hi", "thanks"]
    COMPLEX_QUERY_THRESHOLD: int = 50  # chars for reasoning detection
    
    # Vector Database Settings
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    COLLECTION_NAME: str = "digital_twin_knowledge"
    
    # Obsidian Settings (legacy - now handled per user)
    OBSIDIAN_VAULT_PATH: Optional[str] = None
    OBSIDIAN_VAULT_NAME: str = "Digital Twin Vault"
    
    # Notion Settings (user-provided credentials - stored per user)
    NOTION_API_TOKEN: Optional[str] = None  # Global fallback, users provide their own
    
    # Knowledge Sources Settings
    SUPPORTED_SOURCES: List[str] = ["obsidian", "notion"]
    MAX_SOURCES_PER_USER: int = 10
    
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
    SECRET_KEY: str = "change-this-in-production"  # Override via environment variable in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()