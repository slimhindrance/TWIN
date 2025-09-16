"""
Together AI integration service for chat completions and embeddings.
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional

import aiohttp

from app.core.config import settings
from app.models.schemas import ChatMessage

logger = logging.getLogger(__name__)


class TogetherService:
    """Service for interacting with Together AI API."""
    
    def __init__(self):
        """Initialize the Together service."""
        self.base_url = "https://api.together.xyz/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize Together AI service."""
        if not settings.TOGETHER_API_KEY:
            logger.warning("Together AI API key not provided")
            return
        
        try:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=60)
            )
            logger.info("Together AI service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Together AI service: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup the aiohttp session."""
        if self.session:
            await self.session.close()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (rough estimate)."""
        # Rough estimate: 4 chars per token
        return len(text) // 4
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        max_chars = max_tokens * 4  # Rough estimate
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
    
    def build_system_prompt(self, context_documents: List[Dict[str, Any]]) -> str:
        """Build system prompt with context from knowledge base."""
        base_prompt = """You are a digital twin AI assistant that has access to the user's personal knowledge base. You have perfect memory of everything in their data and can help them recall information, make connections, and discuss their previous work and thoughts.

Key instructions:
1. Use the provided context from their data to inform your responses
2. When referencing specific information, mention which source it came from
3. Help them connect ideas across different data sources and time periods
4. If they ask about something not in your knowledge base, be honest about it
5. Maintain the user's voice and perspective when discussing their data
6. Be conversational and helpful, as if you are their augmented memory
7. Keep responses concise and focused

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
            # Ensure we don't exceed token limits - Together AI has smaller context
            return self.truncate_text(full_prompt, 4000)  # Smaller context for Llama
        else:
            return base_prompt + "\n\n(No relevant context found in knowledge base)"
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        context_documents: List[Dict[str, Any]] = None,
        max_tokens: int = 2000,  # Smaller default for cost
        temperature: float = 0.7
    ) -> str:
        """Generate a chat response using Together AI."""
        if not self.session or not settings.TOGETHER_API_KEY:
            return "I'm sorry, but I'm not properly configured to generate responses. Please check the Together AI API key."
        
        try:
            # Build system prompt with context
            system_prompt = self.build_system_prompt(context_documents or [])
            
            # Convert messages to Together AI format (OpenAI-compatible)
            api_messages = [{"role": "system", "content": system_prompt}]
            
            for msg in messages[-8:]:  # Keep fewer messages for smaller models
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Calculate token usage
            total_tokens = sum(self.count_tokens(msg["content"]) for msg in api_messages)
            if total_tokens > 6000:  # Conservative limit
                logger.warning(f"Token count ({total_tokens}) is high, truncating conversation")
                # Keep system message and last few user messages
                api_messages = [api_messages[0]] + api_messages[-4:]
            
            # Prepare request
            payload = {
                "model": settings.TOGETHER_MODEL,
                "messages": api_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.7,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "stop": ["<|eot_id|>", "<|end_of_text|>"]  # Llama stop tokens
            }
            
            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Together AI API error ({response.status}): {error_text}")
                    return f"I encountered an API error: {response.status}"
                
                result = await response.json()
                
                if result.get('choices') and len(result['choices']) > 0:
                    content = result['choices'][0]['message'].get('content', '')
                    return content.strip()
                else:
                    return "I'm sorry, I couldn't generate a proper response."
            
        except asyncio.TimeoutError:
            logger.error("Together AI request timed out")
            return "I'm sorry, the request timed out. Please try again."
        except Exception as e:
            logger.error(f"Failed to generate chat response with Together AI: {e}")
            return f"I encountered an error while generating a response: {str(e)}"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Together AI."""
        if not self.session or not settings.TOGETHER_API_KEY:
            raise ValueError("Together AI client not initialized")
        
        try:
            payload = {
                "model": settings.TOGETHER_EMBEDDING_MODEL,
                "input": text
            }
            
            async with self.session.post(f"{self.base_url}/embeddings", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Together AI embedding error ({response.status}): {error_text}")
                    raise ValueError(f"Embedding API error: {response.status}")
                
                result = await response.json()
                
                if result.get('data') and len(result['data']) > 0:
                    return result['data'][0]['embedding']
                else:
                    raise ValueError("No embedding data in response")
            
        except Exception as e:
            logger.error(f"Failed to generate embedding with Together AI: {e}")
            raise
    
    async def summarize_text(self, text: str, max_tokens: int = 300) -> str:
        """Generate a summary of the given text."""
        if not self.session:
            return text[:1000] + "..." if len(text) > 1000 else text
        
        try:
            messages = [ChatMessage(role="user", content=f"Please provide a concise summary of the following text:\n\n{text}")]
            
            return await self.generate_chat_response(
                messages=messages,
                context_documents=[],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
        except Exception as e:
            logger.error(f"Failed to summarize text with Together AI: {e}")
            return text
