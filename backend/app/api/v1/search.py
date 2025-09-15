"""
Search endpoints for knowledge base queries.
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import SearchQuery, SearchResponse, SearchResult

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_knowledge_base(query: SearchQuery, request: Request):
    """
    Search the knowledge base for relevant documents.
    
    This endpoint searches through the indexed Obsidian vault content
    and returns relevant documents with similarity scores.
    """
    try:
        # Get vector store from app state
        vector_store = request.app.state.vector_store
        
        # Search for documents
        results = await vector_store.search_documents(
            query=query.query,
            limit=query.limit,
            similarity_threshold=query.similarity_threshold
        )
        
        # Convert to response format
        search_results = []
        for doc in results:
            search_results.append(SearchResult(
                id=doc["id"],
                title=doc.get("metadata", {}).get("title", "Untitled"),
                content=doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                similarity_score=doc["similarity_score"],
                metadata=doc.get("metadata", {})
            ))
        
        return SearchResponse(
            results=search_results,
            total_results=len(search_results),
            query=query.query
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{document_id}")
async def find_similar_documents(document_id: str, limit: int = 5, request: Request = None):
    """
    Find documents similar to a specific document.
    """
    try:
        vector_store = request.app.state.vector_store
        
        # Get the document content first
        # Note: This would require implementing a get_document method in VectorStore
        # For now, we'll return a placeholder response
        
        return {
            "similar_documents": [],
            "source_document_id": document_id,
            "message": "Similar document search not yet implemented - requires document retrieval by ID"
        }
        
    except Exception as e:
        logger.error(f"Similar documents search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags")
async def list_tags(request: Request):
    """
    List all tags found in the knowledge base.
    """
    try:
        # This would require aggregating tags from document metadata
        # For now, return a placeholder
        return {
            "tags": [],
            "message": "Tag listing not yet implemented - requires metadata aggregation"
        }
        
    except Exception as e:
        logger.error(f"Tag listing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_search_stats(request: Request):
    """
    Get knowledge base statistics.
    """
    try:
        vector_store = request.app.state.vector_store
        
        total_documents = await vector_store.get_document_count()
        
        return {
            "total_documents": total_documents,
            "index_status": "active" if total_documents > 0 else "empty",
            "last_updated": None  # Would require tracking in VectorStore
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
