"""
Chat endpoints for conversational AI.
"""
import logging
from typing import List
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.services.openai_service import OpenAIService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory conversation storage (in production, use Redis or database)
conversations: dict[str, List[ChatMessage]] = {}


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, fastapi_request: Request):
    """
    Generate a chat response using the digital twin AI.
    
    This endpoint:
    1. Searches the knowledge base for relevant context
    2. Uses the context to inform the AI response
    3. Returns the response with source citations
    """
    try:
        # Get services from app state
        vector_store: VectorStore = fastapi_request.app.state.vector_store
        openai_service = OpenAIService()
        await openai_service.initialize()
        
        # Get or create conversation
        conversation_id = request.conversation_id or str(uuid.uuid4())
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Add user message to conversation
        user_message = ChatMessage(role="user", content=request.message)
        conversations[conversation_id].append(user_message)
        
        # Search for relevant context
        context_documents = await vector_store.search_documents(
            query=request.message,
            limit=5,
            similarity_threshold=0.6
        )
        
        # Generate AI response
        response_content = await openai_service.generate_chat_response(
            messages=conversations[conversation_id],
            context_documents=context_documents,
            max_tokens=request.max_tokens or 4000,
            temperature=request.temperature or 0.7
        )
        
        # Add assistant response to conversation
        assistant_message = ChatMessage(role="assistant", content=response_content)
        conversations[conversation_id].append(assistant_message)
        
        # Keep conversations from growing too large
        if len(conversations[conversation_id]) > 50:
            conversations[conversation_id] = conversations[conversation_id][-30:]
        
        # Extract source information
        sources = []
        for doc in context_documents:
            source_info = doc.get("metadata", {}).get("source", "Unknown")
            if source_info not in sources:
                sources.append(source_info)
        
        return ChatResponse(
            message=response_content,
            conversation_id=conversation_id,
            sources=sources,
            metadata={
                "context_documents_used": len(context_documents),
                "total_conversation_length": len(conversations[conversation_id])
            }
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id],
        "message_count": len(conversations[conversation_id])
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations[conversation_id]
    return {"message": "Conversation deleted successfully"}


@router.get("/conversations")
async def list_conversations():
    """List all active conversations."""
    conversation_list = []
    for conv_id, messages in conversations.items():
        if messages:
            last_message = messages[-1]
            conversation_list.append({
                "conversation_id": conv_id,
                "message_count": len(messages),
                "last_message_time": last_message.timestamp,
                "last_message_preview": last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content
            })
    
    return {
        "conversations": conversation_list,
        "total_conversations": len(conversation_list)
    }
