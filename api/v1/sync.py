"""
Synchronization endpoints for Obsidian vault management.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from app.models.schemas import VaultSyncStatus
from app.services.obsidian_watcher import ObsidianWatcher
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status", response_model=VaultSyncStatus)
async def get_sync_status(request: Request):
    """
    Get the current synchronization status of the Obsidian vault.
    """
    try:
        vector_store = request.app.state.vector_store
        total_documents = await vector_store.get_document_count()
        
        # Check if watcher is running
        watcher_status = False
        last_sync = None
        
        if hasattr(request.app.state, 'obsidian_watcher'):
            watcher: ObsidianWatcher = request.app.state.obsidian_watcher
            status_info = watcher.get_status()
            watcher_status = status_info.get('is_running', False)
            last_sync = status_info.get('last_sync')
        
        return VaultSyncStatus(
            vault_path=settings.OBSIDIAN_VAULT_PATH,
            is_watching=watcher_status,
            last_sync=last_sync,
            total_documents=total_documents,
            sync_errors=[]  # Would need to implement error tracking
        )
        
    except Exception as e:
        logger.error(f"Sync status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-sync")
async def trigger_full_sync(background_tasks: BackgroundTasks, request: Request):
    """
    Trigger a full synchronization of the Obsidian vault.
    
    This will re-index all documents in the vault.
    """
    try:
        if not hasattr(request.app.state, 'obsidian_watcher'):
            raise HTTPException(
                status_code=400, 
                detail="Obsidian watcher not configured. Check OBSIDIAN_VAULT_PATH setting."
            )
        
        watcher: ObsidianWatcher = request.app.state.obsidian_watcher
        
        # Run sync in background
        background_tasks.add_task(watcher.perform_full_sync)
        
        return {
            "message": "Full synchronization started in background",
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Full sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-watching")
async def start_vault_watching(request: Request):
    """
    Start watching the Obsidian vault for changes.
    """
    try:
        if not settings.OBSIDIAN_VAULT_PATH:
            raise HTTPException(
                status_code=400,
                detail="OBSIDIAN_VAULT_PATH not configured"
            )
        
        if hasattr(request.app.state, 'obsidian_watcher'):
            watcher: ObsidianWatcher = request.app.state.obsidian_watcher
            if watcher.is_running:
                return {"message": "Vault watching is already active", "status": "already_running"}
            
            success = await watcher.start()
            if success:
                return {"message": "Vault watching started successfully", "status": "started"}
            else:
                raise HTTPException(status_code=500, detail="Failed to start vault watching")
        else:
            # Initialize new watcher
            vector_store = request.app.state.vector_store
            watcher = ObsidianWatcher()
            
            if await watcher.initialize(vector_store):
                if await watcher.start():
                    request.app.state.obsidian_watcher = watcher
                    return {"message": "Vault watching initialized and started", "status": "started"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to start vault watching")
            else:
                raise HTTPException(status_code=400, detail="Failed to initialize vault watcher")
                
    except Exception as e:
        logger.error(f"Start watching error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-watching")
async def stop_vault_watching(request: Request):
    """
    Stop watching the Obsidian vault for changes.
    """
    try:
        if not hasattr(request.app.state, 'obsidian_watcher'):
            return {"message": "Vault watching is not active", "status": "not_running"}
        
        watcher: ObsidianWatcher = request.app.state.obsidian_watcher
        await watcher.stop()
        
        return {"message": "Vault watching stopped successfully", "status": "stopped"}
        
    except Exception as e:
        logger.error(f"Stop watching error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure")
async def configure_vault(vault_path: str, request: Request):
    """
    Configure a new Obsidian vault path.
    
    Note: This changes the configuration at runtime but doesn't persist across restarts.
    For permanent configuration, update the .env file.
    """
    try:
        from pathlib import Path
        from app.services.obsidian_parser import ObsidianParser
        
        # Validate the vault path
        path = Path(vault_path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid vault path: path does not exist")
        
        parser = ObsidianParser(str(path))
        if not parser.is_valid_vault():
            raise HTTPException(status_code=400, detail="Invalid Obsidian vault: no markdown files found")
        
        # Stop current watcher if running
        if hasattr(request.app.state, 'obsidian_watcher'):
            watcher: ObsidianWatcher = request.app.state.obsidian_watcher
            await watcher.stop()
        
        # Update configuration (runtime only)
        settings.OBSIDIAN_VAULT_PATH = str(path)
        
        # Initialize new watcher
        vector_store = request.app.state.vector_store
        new_watcher = ObsidianWatcher()
        
        if await new_watcher.initialize(vector_store):
            request.app.state.obsidian_watcher = new_watcher
            
            return {
                "message": f"Vault configured successfully: {vault_path}",
                "status": "configured",
                "vault_path": str(path)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize new vault configuration")
            
    except Exception as e:
        logger.error(f"Configure vault error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
