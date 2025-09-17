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
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.db.models import ConversationORM, MessageORM

logger = logging.getLogger(__name__)

router = APIRouter()

# Conversations and messages are persisted in the database


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    fastapi_request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
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
        await AuthService.update_user_usage(user_id, 1, session)
        
        # Get services from app state
        vector_store: VectorStore = fastapi_request.app.state.vector_store
        ai_router: AIRouter = fastapi_request.app.state.ai_router
        
        # Get or create conversation for this user
        conversation_id = request.conversation_id or str(uuid.uuid4())
        if request.conversation_id:
            # Verify conversation belongs to user
            existing = await session.execute(
                select(ConversationORM).where(
                    ConversationORM.id == conversation_id,
                    ConversationORM.user_id == user_id,
                )
            )
            if existing.scalar_one_or_none() is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create conversation
            conv = ConversationORM(id=conversation_id, user_id=user_id)
            session.add(conv)
            await session.commit()

        # Persist user message
        user_msg_id = str(uuid.uuid4())
        user_message = ChatMessage(role="user", content=request.message)
        session.add(
            MessageORM(
                id=user_msg_id,
                conversation_id=conversation_id,
                user_id=user_id,
                role=user_message.role,
                content=user_message.content,
                timestamp=user_message.timestamp,
            )
        )
        # Update conversation updated_at
        from sqlalchemy import update as sql_update
        from datetime import datetime
        await session.execute(
            sql_update(ConversationORM).where(ConversationORM.id == conversation_id).values(updated_at=datetime.utcnow())
        )
        await session.commit()

        # Search for relevant context (filtered by user)
        context_documents = await vector_store.search_documents(
            query=request.message,
            user_id=user_id,  # Filter by user
            limit=5,
            similarity_threshold=0.6
        )
        
        # Fetch prior messages to build context for AI
        result = await session.execute(
            select(MessageORM).where(MessageORM.conversation_id == conversation_id).order_by(MessageORM.timestamp.asc())
        )
        prior_msgs = result.scalars().all()
        history: List[ChatMessage] = [
            ChatMessage(role=m.role, content=m.content, timestamp=m.timestamp) for m in prior_msgs
        ]

        # Generate AI response with smart routing
        response_content, provider_used, complexity = await ai_router.generate_chat_response_with_routing(
            messages=history,
            context_documents=context_documents,
            user_tier=getattr(current_user, 'tier', 'free'),  # Default to free tier
            force_provider=request.force_provider,  # Allow forcing provider
            max_tokens=request.max_tokens or 4000,
            temperature=request.temperature or 0.7
        )
        
        # Persist assistant response
        assistant_message = ChatMessage(role="assistant", content=response_content)
        session.add(
            MessageORM(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                user_id=user_id,
                role=assistant_message.role,
                content=assistant_message.content,
                timestamp=assistant_message.timestamp,
            )
        )
        await session.execute(
            sql_update(ConversationORM).where(ConversationORM.id == conversation_id).values(updated_at=datetime.utcnow())
        )
        await session.commit()
        
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
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get conversation history for current user."""
    user_id = current_user.id
    # Verify belongs to user
    conv = await session.execute(
        select(ConversationORM).where(ConversationORM.id == conversation_id, ConversationORM.user_id == user_id)
    )
    if conv.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Fetch messages
    result = await session.execute(
        select(MessageORM).where(MessageORM.conversation_id == conversation_id).order_by(MessageORM.timestamp.asc())
    )
    msgs = result.scalars().all()
    messages = [ChatMessage(role=m.role, content=m.content, timestamp=m.timestamp) for m in msgs]
    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "message_count": len(messages),
        "user_id": user_id,
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a conversation for current user."""
    user_id = current_user.id
    # Verify belongs to user
    conv = await session.execute(
        select(ConversationORM).where(ConversationORM.id == conversation_id, ConversationORM.user_id == user_id)
    )
    if conv.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Delete messages then conversation
    await session.execute(delete(MessageORM).where(MessageORM.conversation_id == conversation_id))
    await session.execute(delete(ConversationORM).where(ConversationORM.id == conversation_id))
    await session.commit()
    return {"message": "Conversation deleted successfully"}


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """List all active conversations for current user."""
    user_id = current_user.id
    # Fetch conversations
    convs = await session.execute(
        select(ConversationORM).where(ConversationORM.user_id == user_id).order_by(ConversationORM.updated_at.desc())
    )
    conv_rows = convs.scalars().all()
    conversations = []
    for conv in conv_rows:
        # Count and last message
        count_result = await session.execute(
            select(func.count()).select_from(MessageORM).where(MessageORM.conversation_id == conv.id)
        )
        msg_count = count_result.scalar_one()
        last_result = await session.execute(
            select(MessageORM).where(MessageORM.conversation_id == conv.id).order_by(MessageORM.timestamp.desc()).limit(1)
        )
        last = last_result.scalar_one_or_none()
        last_time = last.timestamp if last else None
        last_preview = (last.content[:100] + "...") if last and len(last.content) > 100 else (last.content if last else "")
        conversations.append({
            "conversation_id": conv.id,
            "message_count": int(msg_count or 0),
            "last_message_time": last_time,
            "last_message_preview": last_preview,
        })
    return {
        "conversations": conversations,
        "total_conversations": len(conversations),
        "user_id": user_id,
    }
