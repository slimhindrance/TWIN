"""
Multi-source knowledge management
"""
import logging
from typing import Dict, List, Any, Optional
from enum import Enum

from app.services.obsidian_parser import ObsidianParser
from app.services.notion_parser import NotionParser
from app.services.knowledge_source import KnowledgeSource

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Supported knowledge source types."""
    OBSIDIAN = "obsidian"
    NOTION = "notion"


class KnowledgeManager:
    """Manages multiple knowledge sources for users."""
    
    def __init__(self):
        """Initialize the knowledge manager."""
        self.sources: Dict[str, KnowledgeSource] = {}
    
    def _get_source_key(self, user_id: str, source_type: SourceType) -> str:
        """Generate a unique key for a user's knowledge source."""
        return f"{user_id}_{source_type.value}"
    
    async def add_source(self, source_type: SourceType, credentials: Dict[str, str], user_id: str) -> bool:
        """Add a new knowledge source for a user."""
        source_key = self._get_source_key(user_id, source_type)
        
        try:
            if source_type == SourceType.OBSIDIAN:
                vault_path = credentials.get('vault_path', '')
                if not vault_path:
                    logger.error("No vault path provided for Obsidian")
                    return False
                
                source = ObsidianParser(vault_path)
                is_valid = source.is_valid_vault()
                
            elif source_type == SourceType.NOTION:
                source = NotionParser()
                is_valid = await source.authenticate(credentials)
                
            else:
                logger.error(f"Unsupported source type: {source_type}")
                return False
            
            if is_valid:
                self.sources[source_key] = source
                logger.info(f"Successfully added {source_type.value} source for user {user_id}")
                return True
            else:
                logger.error(f"Invalid credentials for {source_type.value} source")
                return False
                
        except Exception as e:
            logger.error(f"Error adding {source_type.value} source for user {user_id}: {e}")
            return False
    
    def remove_source(self, source_type: SourceType, user_id: str) -> bool:
        """Remove a knowledge source for a user."""
        source_key = self._get_source_key(user_id, source_type)
        
        if source_key in self.sources:
            del self.sources[source_key]
            logger.info(f"Removed {source_type.value} source for user {user_id}")
            return True
        
        return False
    
    def get_source(self, source_type: SourceType, user_id: str) -> Optional[KnowledgeSource]:
        """Get a specific knowledge source for a user."""
        source_key = self._get_source_key(user_id, source_type)
        return self.sources.get(source_key)
    
    def has_source(self, source_type: SourceType, user_id: str) -> bool:
        """Check if user has a specific knowledge source configured."""
        source_key = self._get_source_key(user_id, source_type)
        return source_key in self.sources
    
    async def get_all_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get documents from all sources for a user."""
        all_documents = []
        
        for source_key, source in self.sources.items():
            if source_key.startswith(user_id):
                try:
                    if isinstance(source, ObsidianParser):
                        documents = source.parse_vault()
                    else:
                        documents = await source.fetch_all_documents()
                    
                    all_documents.extend(documents)
                    logger.info(f"Retrieved {len(documents)} documents from {source_key}")
                    
                except Exception as e:
                    logger.error(f"Error fetching documents from {source_key}: {e}")
        
        logger.info(f"Total documents retrieved for user {user_id}: {len(all_documents)}")
        return all_documents
    
    async def get_source_status(self, user_id: str) -> List[Dict[str, Any]]:
        """Get status of all configured sources for a user."""
        statuses = []
        
        for source_type in SourceType:
            source_key = self._get_source_key(user_id, source_type)
            source = self.sources.get(source_key)
            
            if source:
                try:
                    is_connected = await source.test_connection()
                    doc_count = await source.get_document_count()
                    
                    statuses.append({
                        "type": source_type.value,
                        "connected": is_connected,
                        "document_count": doc_count,
                        "last_synced": None  # TODO: Track sync times
                    })
                except Exception as e:
                    logger.error(f"Error getting status for {source_key}: {e}")
                    statuses.append({
                        "type": source_type.value,
                        "connected": False,
                        "document_count": 0,
                        "error": str(e)
                    })
            else:
                statuses.append({
                    "type": source_type.value,
                    "connected": False,
                    "document_count": 0,
                    "configured": False
                })
        
        return statuses
    
    async def sync_all_sources(self, user_id: str, vector_store) -> Dict[str, Any]:
        """Sync all documents from all sources to the vector store."""
        sync_results = {
            "total_documents": 0,
            "sources_synced": 0,
            "errors": []
        }
        
        try:
            # Get all documents from all sources
            all_documents = await self.get_all_documents(user_id)
            
            # Clear existing documents for this user
            # TODO: Implement user-specific collection clearing
            
            # Add all documents to vector store
            for doc in all_documents:
                try:
                    for i, chunk in enumerate(doc['chunks']):
                        chunk_id = f"{user_id}_{doc['metadata']['source']}_chunk_{i}"
                        chunk_metadata = doc['metadata'].copy()
                        chunk_metadata.update({
                            'chunk_index': i,
                            'parent_document': doc['metadata']['source'],
                            'user_id': user_id,
                            'chunk_content_preview': chunk[:100] + "..." if len(chunk) > 100 else chunk
                        })
                        
                        await vector_store.add_document(chunk, chunk_metadata, chunk_id)
                        sync_results["total_documents"] += 1
                        
                except Exception as e:
                    logger.error(f"Error syncing document {doc.get('metadata', {}).get('source', 'unknown')}: {e}")
                    sync_results["errors"].append(str(e))
            
            sync_results["sources_synced"] = len([k for k in self.sources.keys() if k.startswith(user_id)])
            
        except Exception as e:
            logger.error(f"Error during sync for user {user_id}: {e}")
            sync_results["errors"].append(str(e))
        
        return sync_results


# Global knowledge manager instance
knowledge_manager = KnowledgeManager()
