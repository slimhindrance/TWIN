"""
Chat endpoints for conversational AI.
"""
import logging
from typing import List, Dict
import uuid

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.services.ai_router import AIRouter
from app.services.vector_store import VectorStore
from app.core.auth import get_current_active_user, AuthService
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory conversation storage per user (in production, use Redis or database)
# Structure: {user_id: {conversation_id: [messages]}}
user_conversations: Dict[str, Dict[str, List[ChatMessage]]] = {}


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a chat response using the digital twin AI.
    
    This endpoint:
    1. Searches the knowledge base for relevant context (filtered by user)
    2. Uses the context to inform the AI response
    3. Returns the response with source citations
    """
    try:
        user_id = current_user.id
        
        # Update user usage for chat
        AuthService.update_user_usage(user_id, 1)
        
        # Get services from app state
        vector_store: VectorStore = fastapi_request.app.state.vector_store
        ai_router: AIRouter = fastapi_request.app.state.ai_router
        
        # Initialize user conversations if needed
        if user_id not in user_conversations:
            user_conversations[user_id] = {}
        
        # Get or create conversation for this user
        conversation_id = request.conversation_id or str(uuid.uuid4())
        if conversation_id not in user_conversations[user_id]:
            user_conversations[user_id][conversation_id] = []
        
        # Add user message to conversation
        user_message = ChatMessage(role="user", content=request.message)
        user_conversations[user_id][conversation_id].append(user_message)
        
        # Search for relevant context (filtered by user)
        context_documents = await vector_store.search_documents(
            query=request.message,
            user_id=user_id,  # Filter by user
            limit=5,
            similarity_threshold=0.6
        )
        
        # Generate AI response with smart routing
        response_content, provider_used, complexity = await ai_router.generate_chat_response_with_routing(
            messages=user_conversations[user_id][conversation_id],
            context_documents=context_documents,
            user_tier=getattr(current_user, 'tier', 'free'),  # Default to free tier
            force_provider=request.force_provider,  # Allow forcing provider
            max_tokens=request.max_tokens or 4000,
            temperature=request.temperature or 0.7
        )
        
        # Add assistant response to conversation
        assistant_message = ChatMessage(role="assistant", content=response_content)
        user_conversations[user_id][conversation_id].append(assistant_message)
        
        # Keep conversations from growing too large
        if len(user_conversations[user_id][conversation_id]) > 50:
            user_conversations[user_id][conversation_id] = user_conversations[user_id][conversation_id][-30:]
        
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
                "total_conversation_length": len(user_conversations[user_id][conversation_id]),
                "user_id": user_id,
                "ai_provider": provider_used,
                "query_complexity": complexity.value,
                "user_tier": getattr(current_user, 'tier', 'free')
            }
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get conversation history for current user."""
    user_id = current_user.id
    
    if user_id not in user_conversations:
        user_conversations[user_id] = {}
    
    if conversation_id not in user_conversations[user_id]:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": user_conversations[user_id][conversation_id],
        "message_count": len(user_conversations[user_id][conversation_id]),
        "user_id": user_id
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a conversation for current user."""
    user_id = current_user.id
    
    if user_id not in user_conversations:
        user_conversations[user_id] = {}
    
    if conversation_id not in user_conversations[user_id]:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del user_conversations[user_id][conversation_id]
    return {"message": "Conversation deleted successfully"}


@router.get("/conversations")
async def list_conversations(current_user: User = Depends(get_current_active_user)):
    """List all active conversations for current user."""
    user_id = current_user.id
    
    if user_id not in user_conversations:
        user_conversations[user_id] = {}
    
    conversation_list = []
    for conv_id, messages in user_conversations[user_id].items():
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
        "total_conversations": len(conversation_list),
        "user_id": user_id
    }
