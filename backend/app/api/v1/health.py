"""
Health check endpoints.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Request

from app.models.schemas import HealthCheck
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check(request: Request):
    """
    Comprehensive health check for all services.
    """
    services_status = {}
    overall_status = "healthy"
    
    # Check vector store
    try:
        vector_store = request.app.state.vector_store
        doc_count = await vector_store.get_document_count()
        services_status["vector_store"] = f"healthy ({doc_count} documents)"
    except Exception as e:
        services_status["vector_store"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
    
    # Check OpenAI configuration
    if settings.OPENAI_API_KEY:
        services_status["openai"] = "configured"
    else:
        services_status["openai"] = "not_configured"
        overall_status = "degraded" if overall_status == "healthy" else overall_status
    
    # Check Obsidian watcher
    if hasattr(request.app.state, 'obsidian_watcher'):
        watcher = request.app.state.obsidian_watcher
        if watcher.is_running:
            services_status["obsidian_watcher"] = "running"
        else:
            services_status["obsidian_watcher"] = "stopped"
    else:
        services_status["obsidian_watcher"] = "not_configured"
    
    # Check vault configuration
    if settings.OBSIDIAN_VAULT_PATH:
        services_status["vault_path"] = "configured"
    else:
        services_status["vault_path"] = "not_configured"
    
    return HealthCheck(
        status=overall_status,
        version="0.1.0",
        services=services_status
    )


@router.get("/ready")
async def readiness_check(request: Request):
    """
    Kubernetes-style readiness probe.
    """
    try:
        # Basic checks that the app is ready to serve requests
        vector_store = request.app.state.vector_store
        if not vector_store:
            return {"status": "not_ready", "reason": "vector_store_not_initialized"}
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}
