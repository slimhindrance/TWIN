"""
Database session and engine setup for async SQLAlchemy.
Builds a PostgreSQL DATABASE_URL from ECS-provided env vars when needed.
"""
import os
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


def _build_database_url() -> Optional[str]:
    """Assemble DATABASE_URL from discrete env vars if not provided.

    Expected env vars (in ECS task):
      - DATABASE_HOST
      - DATABASE_PORT
      - DATABASE_NAME
      - DATABASE_USERNAME (secret)
      - DATABASE_PASSWORD (secret)
    """
    direct = os.getenv("DATABASE_URL")
    if direct:
        return direct

    host = os.getenv("DATABASE_HOST")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME")
    user = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")

    if all([host, port, name, user, password]):
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    return None


DATABASE_URL = _build_database_url()

if not DATABASE_URL:
    # Use a noop in-memory SQLite for local dev if not configured
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

