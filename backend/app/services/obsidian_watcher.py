"""
File system watcher for Obsidian vault synchronization.
"""
import asyncio
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

from app.core.config import settings
from app.services.obsidian_parser import ObsidianParser
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class ObsidianFileHandler(FileSystemEventHandler):
    """Handler for Obsidian file system events."""
    
    def __init__(self, parser: ObsidianParser, vector_store: VectorStore):
        """Initialize the file handler."""
        super().__init__()
        self.parser = parser
        self.vector_store = vector_store
        self.processing_queue = asyncio.Queue()
        
    def should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed."""
        path = Path(file_path)
        
        # Only process .md files
        if path.suffix != '.md':
            return False
        
        # Skip Obsidian system files
        excluded_patterns = {
            '.obsidian',
            '.trash',
            'node_modules',
            '.git'
        }
        
        return not any(excluded in path.parts for excluded in excluded_patterns)
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            logger.info(f"File created: {event.src_path}")
            asyncio.create_task(self._process_file_change(event.src_path, 'created'))
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            logger.info(f"File modified: {event.src_path}")
            asyncio.create_task(self._process_file_change(event.src_path, 'modified'))
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            logger.info(f"File deleted: {event.src_path}")
            asyncio.create_task(self._process_file_change(event.src_path, 'deleted'))
    
    async def _process_file_change(self, file_path: str, change_type: str):
        """Process file changes asynchronously."""
        try:
            path = Path(file_path)
            doc_id = str(path.relative_to(self.parser.vault_path))
            
            if change_type == 'deleted':
                await self.vector_store.delete_document(doc_id)
                logger.info(f"Removed document {doc_id} from vector store")
                
            elif change_type in ['created', 'modified']:
                # Parse the file
                parsed_doc = self.parser.parse_file(path)
                
                if parsed_doc:
                    # Process chunks
                    for i, chunk in enumerate(parsed_doc['chunks']):
                        chunk_id = f"{doc_id}_chunk_{i}"
                        chunk_metadata = parsed_doc['metadata'].copy()
                        chunk_metadata.update({
                            'chunk_index': i,
                            'parent_document': doc_id,
                            'chunk_content_preview': chunk[:100] + "..." if len(chunk) > 100 else chunk
                        })
                        
                        try:
                            if change_type == 'created':
                                await self.vector_store.add_document(chunk, chunk_metadata, chunk_id)
                            else:  # modified
                                await self.vector_store.update_document(chunk_id, chunk, chunk_metadata)
                                
                        except Exception as e:
                            logger.error(f"Failed to process chunk {chunk_id}: {e}")
                    
                    logger.info(f"Processed {len(parsed_doc['chunks'])} chunks for document {doc_id}")
                else:
                    logger.warning(f"Failed to parse file: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error processing file change for {file_path}: {e}")


class ObsidianWatcher:
    """Obsidian vault file watcher."""
    
    def __init__(self):
        """Initialize the watcher."""
        self.observer: Optional[Observer] = None
        self.parser: Optional[ObsidianParser] = None
        self.vector_store: Optional[VectorStore] = None
        self.is_running = False
        self.last_sync: Optional[datetime] = None
        
    async def initialize(self, vector_store: VectorStore) -> bool:
        """Initialize the watcher with dependencies."""
        if not settings.OBSIDIAN_VAULT_PATH:
            logger.warning("No Obsidian vault path configured")
            return False
        
        vault_path = Path(settings.OBSIDIAN_VAULT_PATH)
        if not vault_path.exists():
            logger.error(f"Obsidian vault path does not exist: {vault_path}")
            return False
        
        self.parser = ObsidianParser(str(vault_path))
        if not self.parser.is_valid_vault():
            logger.error(f"Invalid Obsidian vault: {vault_path}")
            return False
        
        self.vector_store = vector_store
        logger.info(f"Obsidian watcher initialized for vault: {vault_path}")
        return True
    
    async def start(self) -> bool:
        """Start watching the Obsidian vault."""
        if not self.parser or not self.vector_store:
            logger.error("Watcher not properly initialized")
            return False
        
        if self.is_running:
            logger.warning("Watcher is already running")
            return True
        
        try:
            # Perform initial sync
            await self.perform_full_sync()
            
            # Set up file system observer
            event_handler = ObsidianFileHandler(self.parser, self.vector_store)
            self.observer = Observer()
            self.observer.schedule(
                event_handler,
                str(self.parser.vault_path),
                recursive=True
            )
            
            self.observer.start()
            self.is_running = True
            
            logger.info("Obsidian watcher started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Obsidian watcher: {e}")
            return False
    
    async def stop(self):
        """Stop the watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        self.is_running = False
        logger.info("Obsidian watcher stopped")
    
    async def perform_full_sync(self):
        """Perform a full synchronization of the vault."""
        if not self.parser or not self.vector_store:
            logger.error("Cannot perform sync - watcher not initialized")
            return
        
        logger.info("Starting full vault synchronization...")
        start_time = datetime.utcnow()
        
        try:
            # Clear existing documents to avoid duplicates
            await self.vector_store.clear_collection()
            
            # Parse all documents in vault
            documents = self.parser.parse_vault()
            
            # Add documents to vector store
            total_chunks = 0
            for doc in documents:
                doc_id = doc['metadata']['source']
                
                # Process each chunk
                for i, chunk in enumerate(doc['chunks']):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    chunk_metadata = doc['metadata'].copy()
                    chunk_metadata.update({
                        'chunk_index': i,
                        'parent_document': doc_id,
                        'chunk_content_preview': chunk[:100] + "..." if len(chunk) > 100 else chunk
                    })
                    
                    await self.vector_store.add_document(chunk, chunk_metadata, chunk_id)
                    total_chunks += 1
            
            self.last_sync = start_time
            sync_duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Full sync completed: {len(documents)} documents, "
                f"{total_chunks} chunks processed in {sync_duration:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            raise
    
    def get_status(self) -> dict:
        """Get watcher status information."""
        return {
            'is_running': self.is_running,
            'vault_path': settings.OBSIDIAN_VAULT_PATH,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'total_documents': asyncio.create_task(self.vector_store.get_document_count()) if self.vector_store else 0
        }
