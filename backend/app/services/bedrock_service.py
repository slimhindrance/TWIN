"""
AWS Bedrock integration service for chat completions and embeddings.
"""
import json
import logging
from typing import List, Dict, Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.models.schemas import ChatMessage

logger = logging.getLogger(__name__)


class BedrockService:
    """Service for interacting with AWS Bedrock API."""
    
    def __init__(self):
        """Initialize the Bedrock service."""
        self.client: Optional[boto3.client] = None
        
    async def initialize(self) -> None:
        """Initialize Bedrock client."""
        try:
            # Initialize boto3 client
            session = boto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            self.client = session.client(
                service_name='bedrock-runtime',
                region_name=settings.AWS_REGION
            )
            
            logger.info("AWS Bedrock service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock service: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (rough estimate for Claude)."""
        # Claude roughly follows 4 chars per token
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
    
    def _build_claude_messages(self, messages: List[ChatMessage], system_prompt: str) -> tuple:
        """Build Claude message format with system prompt."""
        # Claude format: separate system prompt from messages
        claude_messages = []
        
        for msg in messages[-10:]:  # Keep last 10 messages for context
            claude_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return system_prompt, claude_messages
    
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        context_documents: List[Dict[str, Any]] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """Generate a chat response using AWS Bedrock Claude."""
        if not self.client:
            return "I'm sorry, but I'm not properly configured to generate responses. Please check the AWS credentials."
        
        try:
            # Build system prompt with context
            system_prompt = self.build_system_prompt(context_documents or [])
            system_prompt, claude_messages = self._build_claude_messages(messages, system_prompt)
            
            # Prepare request body for Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "system": system_prompt,
                "messages": claude_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # Make the request
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_MODEL,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            # Parse response
            result = json.loads(response['body'].read())
            
            if result.get('content') and len(result['content']) > 0:
                return result['content'][0].get('text', '')
            else:
                return "I'm sorry, I couldn't generate a proper response."
            
        except ClientError as e:
            logger.error(f"AWS Client error in chat response: {e}")
            return f"I encountered an AWS error: {str(e)}"
        except Exception as e:
            logger.error(f"Failed to generate chat response with Bedrock: {e}")
            return f"I encountered an error while generating a response: {str(e)}"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Amazon Titan."""
        if not self.client:
            raise ValueError("Bedrock client not initialized")
        
        try:
            body = {
                "inputText": text
            }
            
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_EMBEDDING_MODEL,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            result = json.loads(response['body'].read())
            return result.get('embedding', [])
            
        except Exception as e:
            logger.error(f"Failed to generate embedding with Bedrock: {e}")
            raise
    
    async def summarize_text(self, text: str, max_tokens: int = 500) -> str:
        """Generate a summary of the given text."""
        if not self.client:
            return text[:1000] + "..." if len(text) > 1000 else text
        
        try:
            system_prompt = "You are a helpful assistant that creates concise summaries."
            messages = [ChatMessage(role="user", content=f"Please provide a concise summary of the following text:\n\n{text}")]
            
            return await self.generate_chat_response(
                messages=messages,
                context_documents=[],
                max_tokens=max_tokens,
                temperature=0.3
            )
            
        except Exception as e:
            logger.error(f"Failed to summarize text with Bedrock: {e}")
            return text
