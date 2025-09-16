"""
Pydantic models for request/response schemas.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    max_tokens: Optional[int] = Field(4000, description="Maximum tokens in response")
    temperature: Optional[float] = Field(0.7, description="Response creativity (0-1)")
    force_provider: Optional[str] = Field(None, description="Force specific AI provider (openai/bedrock/together)")


class ChatResponse(BaseModel):
    """Chat response schema."""
    message: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[str] = Field(default_factory=list, description="Source documents used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentUpload(BaseModel):
    """Document upload schema."""
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    tags: List[str] = Field(default_factory=list, description="Document tags")


class SearchQuery(BaseModel):
    """Search query schema."""
    query: str = Field(..., description="Search query")
    limit: int = Field(10, description="Maximum results to return", ge=1, le=100)
    similarity_threshold: float = Field(0.7, description="Minimum similarity score", ge=0.0, le=1.0)


class SearchResult(BaseModel):
    """Search result schema."""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content excerpt")
    similarity_score: float = Field(..., description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class SearchResponse(BaseModel):
    """Search response schema."""
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")


class VaultSyncStatus(BaseModel):
    """Vault synchronization status."""
    vault_path: Optional[str] = Field(None, description="Path to Obsidian vault")
    is_watching: bool = Field(False, description="Whether file watching is active")
    last_sync: Optional[datetime] = Field(None, description="Last synchronization time")
    total_documents: int = Field(0, description="Total documents in the knowledge base")
    sync_errors: List[str] = Field(default_factory=list, description="Recent sync errors")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict, description="Service status details")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
