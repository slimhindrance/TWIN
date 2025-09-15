"""
Vector database service using ChromaDB.
"""
import logging
from typing import List, Optional, Dict, Any
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings
import openai
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector database service for storing and retrieving document embeddings."""
    
    def __init__(self):
        """Initialize the vector store."""
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None
        self.openai_client: Optional[OpenAI] = None
        
    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Initialize ChromaDB
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Initialize OpenAI client
            if settings.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                logger.warning("OpenAI API key not provided - embedding functionality will be limited")
            
            logger.info(f"Vector store initialized with collection: {settings.COLLECTION_NAME}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            response = self.openai_client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> str:
        """Add a document to the vector store."""
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        if not doc_id:
            doc_id = str(uuid.uuid4())
        
        try:
            # Generate embedding
            if self.openai_client:
                embedding = await self.generate_embedding(content)
                
                self.collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id],
                    embeddings=[embedding]
                )
            else:
                # Add without custom embedding (ChromaDB will use default)
                self.collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            
            logger.info(f"Added document {doc_id} to vector store")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        try:
            # Generate query embedding if OpenAI is available
            if self.openai_client:
                query_embedding = await self.generate_embedding(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
            
            # Process results
            documents = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    score = results["distances"][0][i] if results["distances"] else 0.0
                    # Convert distance to similarity (lower distance = higher similarity)
                    similarity = 1.0 - score if score <= 1.0 else 0.0
                    
                    if similarity >= similarity_threshold:
                        documents.append({
                            "id": results["ids"][0][i],
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                            "similarity_score": similarity
                        })
            
            logger.info(f"Found {len(documents)} documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise
    
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update an existing document."""
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        try:
            # Generate new embedding
            if self.openai_client:
                embedding = await self.generate_embedding(content)
                
                self.collection.update(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[metadata],
                    embeddings=[embedding]
                )
            else:
                self.collection.update(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[metadata]
                )
            
            logger.info(f"Updated document {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            raise
    
    async def delete_document(self, doc_id: str) -> None:
        """Delete a document from the vector store."""
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    async def get_document_count(self) -> int:
        """Get the total number of documents in the collection."""
        if not self.collection:
            return 0
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0
    
    async def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        try:
            # Get all document IDs and delete them
            results = self.collection.get()
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
            
            logger.info("Cleared all documents from collection")
            
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise
