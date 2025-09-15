"""
Main API router for v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import chat, search, sync, health

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
