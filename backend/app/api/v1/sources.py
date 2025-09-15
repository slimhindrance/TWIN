"""
Knowledge source management endpoints
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel

from app.services.knowledge_manager import knowledge_manager, SourceType

logger = logging.getLogger(__name__)

router = APIRouter()


class NotionCredentials(BaseModel):
    """Notion API credentials."""
    notion_api_token: str


class ObsidianCredentials(BaseModel):
    """Obsidian vault credentials."""
    vault_path: str


class SourceStatus(BaseModel):
    """Knowledge source status."""
    type: str
    connected: bool
    document_count: int
    configured: bool = True
    last_synced: Optional[str] = None
    error: Optional[str] = None


class SourceSyncResult(BaseModel):
    """Result of source synchronization."""
    total_documents: int
    sources_synced: int
    errors: List[str]


@router.post("/notion/connect")
async def connect_notion(credentials: NotionCredentials, request: Request):
    """Connect user's Notion workspace."""
    try:
        # TODO: Get actual user ID from authentication
        user_id = "current_user"  # Placeholder
        
        success = await knowledge_manager.add_source(
            SourceType.NOTION, 
            {"notion_api_token": credentials.notion_api_token},
            user_id
        )
        
        if success:
            return {
                "message": "Notion workspace connected successfully", 
                "status": "connected",
                "source_type": "notion"
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to connect to Notion. Please check your API token and permissions."
            )
            
    except Exception as e:
        logger.error(f"Error connecting Notion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/obsidian/connect")
async def connect_obsidian(credentials: ObsidianCredentials, request: Request):
    """Connect user's Obsidian vault."""
    try:
        # TODO: Get actual user ID from authentication
        user_id = "current_user"  # Placeholder
        
        success = await knowledge_manager.add_source(
            SourceType.OBSIDIAN,
            {"vault_path": credentials.vault_path},
            user_id
        )
        
        if success:
            return {
                "message": "Obsidian vault connected successfully",
                "status": "connected", 
                "source_type": "obsidian"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid Obsidian vault path. Please ensure the path exists and contains markdown files."
            )
            
    except Exception as e:
        logger.error(f"Error connecting Obsidian: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{source_type}/disconnect")
async def disconnect_source(source_type: str, request: Request):
    """Disconnect a knowledge source."""
    try:
        # TODO: Get actual user ID from authentication
        user_id = "current_user"  # Placeholder
        
        if source_type not in ["notion", "obsidian"]:
            raise HTTPException(status_code=400, detail="Unsupported source type")
        
        source_enum = SourceType.NOTION if source_type == "notion" else SourceType.OBSIDIAN
        success = knowledge_manager.remove_source(source_enum, user_id)
        
        if success:
            return {
                "message": f"{source_type.title()} disconnected successfully",
                "status": "disconnected",
                "source_type": source_type
            }
        else:
            raise HTTPException(status_code=404, detail=f"{source_type.title()} source not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting {source_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=List[SourceStatus])
async def get_sources_status(request: Request):
    """Get status of all knowledge sources for the current user."""
    try:
        # TODO: Get actual user ID from authentication
        user_id = "current_user"  # Placeholder
        
        statuses = await knowledge_manager.get_source_status(user_id)
        
        return [SourceStatus(**status) for status in statuses]
        
    except Exception as e:
        logger.error(f"Error getting sources status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=SourceSyncResult)
async def sync_all_sources(background_tasks: BackgroundTasks, request: Request):
    """Sync all connected knowledge sources."""
    try:
        # TODO: Get actual user ID from authentication  
        user_id = "current_user"  # Placeholder
        
        # Get vector store from app state
        vector_store = request.app.state.vector_store
        
        # Run sync in background
        background_tasks.add_task(
            knowledge_manager.sync_all_sources, 
            user_id, 
            vector_store
        )
        
        return SourceSyncResult(
            total_documents=0,  # Will be updated after background sync
            sources_synced=len([k for k in knowledge_manager.sources.keys() if k.startswith(user_id)]),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported")
async def get_supported_sources():
    """Get list of supported knowledge source types."""
    return {
        "sources": [
            {
                "type": "obsidian",
                "name": "Obsidian",
                "description": "Local Obsidian vault with markdown files",
                "requires_credentials": ["vault_path"],
                "free": True
            },
            {
                "type": "notion", 
                "name": "Notion",
                "description": "Notion workspace with pages and databases",
                "requires_credentials": ["notion_api_token"],
                "free": True,
                "setup_url": "https://developers.notion.com/docs/create-a-notion-integration"
            }
        ]
    }


@router.get("/{source_type}/test")
async def test_source_connection(source_type: str, request: Request):
    """Test connection to a specific knowledge source."""
    try:
        # TODO: Get actual user ID from authentication
        user_id = "current_user"  # Placeholder
        
        if source_type not in ["notion", "obsidian"]:
            raise HTTPException(status_code=400, detail="Unsupported source type")
        
        source_enum = SourceType.NOTION if source_type == "notion" else SourceType.OBSIDIAN
        source = knowledge_manager.get_source(source_enum, user_id)
        
        if not source:
            raise HTTPException(
                status_code=404, 
                detail=f"{source_type.title()} source not configured"
            )
        
        is_connected = await source.test_connection()
        doc_count = await source.get_document_count() if is_connected else 0
        
        return {
            "source_type": source_type,
            "connected": is_connected,
            "document_count": doc_count,
            "message": f"{source_type.title()} connection {'successful' if is_connected else 'failed'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing {source_type} connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
