"""
Digital Twin FastAPI Application
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.services.vector_store import VectorStore
from app.services.obsidian_watcher import ObsidianWatcher


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Initialize services
    vector_store = VectorStore()
    await vector_store.initialize()
    
    # Start Obsidian watcher if vault path is configured
    if settings.OBSIDIAN_VAULT_PATH:
        obsidian_watcher = ObsidianWatcher()
        await obsidian_watcher.start()
        app.state.obsidian_watcher = obsidian_watcher
    
    app.state.vector_store = vector_store
    
    yield
    
    # Cleanup
    if hasattr(app.state, 'obsidian_watcher'):
        await app.state.obsidian_watcher.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A digital twin that learns from your Obsidian vault to create a conversational AI with your knowledge",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Digital Twin API",
        "version": "0.1.0",
        "status": "active"
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
