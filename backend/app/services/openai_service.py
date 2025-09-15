"""
OpenAI integration service for chat completions and embeddings.
"""
import logging
from typing import List, Dict, Any, Optional

from openai import OpenAI
import tiktoken

from app.core.config import settings
from app.models.schemas import ChatMessage

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.client: Optional[OpenAI] = None
        self.encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
        
    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not provided")
            return
        
        try:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Failed to count tokens: {e}")
            # Fallback: rough estimate
            return len(text) // 4
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        try:
            tokens = self.encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text
            
            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
            
        except Exception as e:
            logger.error(f"Failed to truncate text: {e}")
            # Fallback: rough character-based truncation
            return text[:max_tokens * 4]
    
    def build_system_prompt(self, context_documents: List[Dict[str, Any]]) -> str:
        """Build system prompt with context from knowledge base."""
        base_prompt = """You are a digital twin AI assistant that has access to the user's personal knowledge base from their Obsidian vault. You have perfect memory of everything in their notes and can help them recall information, make connections, and discuss their previous work and thoughts.

Key instructions:
1. Use the provided context from their notes to inform your responses
2. When referencing specific information, mention which note or source it came from
3. Help them connect ideas across different notes and time periods
4. If they ask about something not in your knowledge base, be honest about it
5. Maintain the user's voice and perspective when discussing their work
6. Be conversational and helpful, as if you are their augmented memory

Context from your knowledge base:"""

        # Add document context
        context_parts = []
        for i, doc in enumerate(context_documents, 1):
            title = doc.get("metadata", {}).get("title", f"Document {i}")
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "Unknown")
            
            context_parts.append(f"\n--- {title} (from {source}) ---\n{content}")
        
        if context_parts:
            full_prompt = base_prompt + "\n".join(context_parts)
            # Ensure we don't exceed token limits
            return self.truncate_text(full_prompt, 6000)  # Leave room for conversation
        else:
            return base_prompt + "\n\n(No relevant context found in knowledge base)"
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        context_documents: List[Dict[str, Any]] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """Generate a chat response using OpenAI."""
        if not self.client:
            return "I'm sorry, but I'm not properly configured to generate responses. Please check the OpenAI API key."
        
        try:
            # Build system prompt with context
            system_prompt = self.build_system_prompt(context_documents or [])
            
            # Convert messages to OpenAI format
            openai_messages = [{"role": "system", "content": system_prompt}]
            
            for msg in messages[-10:]:  # Keep last 10 messages for context
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Calculate token usage
            total_tokens = sum(self.count_tokens(msg["content"]) for msg in openai_messages)
            if total_tokens > 12000:  # Leave room for response
                logger.warning(f"Token count ({total_tokens}) is high, truncating conversation")
                # Keep system message and last few user messages
                openai_messages = [openai_messages[0]] + openai_messages[-5:]
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error(f"Failed to generate chat response: {e}")
            return f"I encountered an error while generating a response: {str(e)}"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            response = self.client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def summarize_text(self, text: str, max_tokens: int = 500) -> str:
        """Generate a summary of the given text."""
        if not self.client:
            return text[:1000] + "..." if len(text) > 1000 else text
        
        try:
            prompt = f"Please provide a concise summary of the following text:\n\n{text}"
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
            return response.choices[0].message.content or text
            
        except Exception as e:
            logger.error(f"Failed to summarize text: {e}")
            return text
