"""
Abstract base class for knowledge sources
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class KnowledgeSource(ABC):
    """Abstract base class for all knowledge sources."""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with the knowledge source."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is working."""
        pass
    
    @abstractmethod
    async def fetch_all_documents(self) -> List[Dict[str, Any]]:
        """Fetch all documents from the source."""
        pass
    
    @abstractmethod
    async def get_document_count(self) -> int:
        """Get total number of documents."""
        pass
    
    @abstractmethod
    def parse_document(self, raw_document: Any) -> Optional[Dict[str, Any]]:
        """Parse a raw document into standard format."""
        pass
    
    def chunk_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split content into overlapping chunks (shared implementation)."""
        if not content or len(content) <= chunk_size:
            return [content] if content else []
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at a sentence boundary
            if end < len(content):
                # Look for sentence endings near the chunk boundary
                for i in range(end, max(end - 100, start), -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
                else:
                    # Look for word boundaries
                    for i in range(end, max(end - 50, start), -1):
                        if content[i].isspace():
                            end = i
                            break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
