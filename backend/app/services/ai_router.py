"""
Smart AI provider router for intelligent query routing based on complexity and cost.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from app.core.config import settings
from app.models.schemas import ChatMessage
from app.services.openai_service import OpenAIService
from app.services.bedrock_service import BedrockService
from app.services.together_service import TogetherService

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Available AI providers."""
    OPENAI = "openai"
    BEDROCK = "bedrock"
    TOGETHER = "together"


class QueryComplexity(Enum):
    """Query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class AIRouter:
    """Smart router for AI providers based on query complexity and cost optimization."""
    
    def __init__(self):
        """Initialize the AI router with all providers."""
        self.openai_service = OpenAIService()
        self.bedrock_service = BedrockService()
        self.together_service = TogetherService()
        
        self.simple_patterns = [
            r'\b(what|when|where|who|how many)\b',
            r'\b(hello|hi|hey|thanks|thank you|ok|okay|yes|no)\b',
            r'\b(define|explain)\s+\w+$',
            r'^\w+\?$',  # Single word questions
        ]
        
        self.complex_indicators = [
            r'\b(analyze|compare|evaluate|synthesize|create|generate)\b',
            r'\b(why|how)\b.*\b(because|complex|relationship|connection)\b',
            r'\b(strategy|plan|approach|methodology)\b',
            r'\b(implications|consequences|impact)\b',
            r'\bmulti[- ]step\b',
            r'\bcomplex\b',
        ]
        
        logger.info("AI Router initialized")
    
    async def initialize(self) -> None:
        """Initialize all AI provider services."""
        try:
            await self.openai_service.initialize()
            await self.bedrock_service.initialize()
            await self.together_service.initialize()
            logger.info("All AI providers initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI providers: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources."""
        if hasattr(self.together_service, 'cleanup'):
            await self.together_service.cleanup()
    
    def analyze_query_complexity(self, query: str, context_documents: List[Dict] = None) -> QueryComplexity:
        """Analyze query complexity to determine optimal provider."""
        query_lower = query.lower().strip()
        word_count = len(query.split())
        
        # Simple query indicators
        if word_count <= settings.SIMPLE_QUERY_MAX_WORDS:
            # Check for simple patterns
            for pattern in self.simple_patterns:
                if re.search(pattern, query_lower):
                    return QueryComplexity.SIMPLE
        
        # Complex query indicators
        for pattern in self.complex_indicators:
            if re.search(pattern, query_lower):
                return QueryComplexity.COMPLEX
        
        # Check for reasoning indicators
        reasoning_words = ['because', 'therefore', 'however', 'although', 'despite', 'moreover']
        if any(word in query_lower for word in reasoning_words):
            return QueryComplexity.COMPLEX
        
        # Long queries are typically more complex
        if len(query) > 200 or word_count > 30:
            return QueryComplexity.COMPLEX
        
        # Context-heavy queries might be complex
        if context_documents and len(context_documents) > 3:
            return QueryComplexity.MODERATE
        
        # Default to moderate for middle ground
        return QueryComplexity.MODERATE
    
    def choose_provider(self, 
                       complexity: QueryComplexity,
                       user_tier: str = "free",
                       force_provider: Optional[AIProvider] = None) -> AIProvider:
        """Choose optimal AI provider based on complexity and user tier."""
        
        if force_provider:
            return force_provider
        
        # Provider selection logic
        if complexity == QueryComplexity.SIMPLE:
            # Use cheapest option for simple queries
            if settings.AI_PRIMARY_PROVIDER == "together":
                return AIProvider.TOGETHER
            elif settings.AI_PRIMARY_PROVIDER == "bedrock":
                return AIProvider.BEDROCK
            else:
                return AIProvider.OPENAI
                
        elif complexity == QueryComplexity.COMPLEX:
            # Use most capable option for complex queries
            if user_tier in ["pro", "enterprise"]:
                # Premium users get the best
                if settings.AI_FALLBACK_PROVIDER == "bedrock":
                    return AIProvider.BEDROCK
                else:
                    return AIProvider.OPENAI
            else:
                # Free users still get good quality but cost-optimized
                if settings.AI_FALLBACK_PROVIDER == "bedrock":
                    return AIProvider.BEDROCK
                else:
                    return AIProvider.TOGETHER
        
        else:  # MODERATE complexity
            # Use primary provider for moderate queries
            if settings.AI_PRIMARY_PROVIDER == "together":
                return AIProvider.TOGETHER
            elif settings.AI_PRIMARY_PROVIDER == "bedrock":
                return AIProvider.BEDROCK
            else:
                return AIProvider.OPENAI
    
    async def generate_chat_response_with_routing(
        self,
        messages: List[ChatMessage],
        context_documents: List[Dict[str, Any]] = None,
        user_tier: str = "free",
        force_provider: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Tuple[str, str, QueryComplexity]:
        """
        Generate chat response with smart routing.
        
        Returns:
            Tuple of (response, provider_used, complexity_detected)
        """
        
        # Get the latest user message for complexity analysis
        latest_message = messages[-1].content if messages else ""
        
        # Analyze complexity
        complexity = self.analyze_query_complexity(latest_message, context_documents)
        
        # Choose provider
        provider_enum = None
        if force_provider:
            try:
                provider_enum = AIProvider(force_provider.lower())
            except ValueError:
                logger.warning(f"Invalid force_provider: {force_provider}, using auto-selection")
        
        if not provider_enum:
            provider_enum = self.choose_provider(complexity, user_tier)
        
        provider_name = provider_enum.value
        logger.info(f"Routing query (complexity: {complexity.value}) to {provider_name}")
        
        # Adjust parameters based on provider
        if provider_enum == AIProvider.TOGETHER:
            # Together AI works better with smaller contexts
            max_tokens = min(max_tokens, 2000)
        
        # Route to selected provider with fallback
        try:
            if provider_enum == AIProvider.TOGETHER:
                response = await self.together_service.generate_chat_response(
                    messages, context_documents, max_tokens, temperature
                )
            elif provider_enum == AIProvider.BEDROCK:
                response = await self.bedrock_service.generate_chat_response(
                    messages, context_documents, max_tokens, temperature
                )
            else:  # OpenAI
                response = await self.openai_service.generate_chat_response(
                    messages, context_documents, max_tokens, temperature
                )
            
            return response, provider_name, complexity
            
        except Exception as e:
            logger.error(f"Primary provider {provider_name} failed: {e}")
            
            # Fallback logic
            fallback_provider = AIProvider(settings.AI_FALLBACK_PROVIDER)
            if fallback_provider != provider_enum:
                logger.info(f"Falling back to {fallback_provider.value}")
                
                try:
                    if fallback_provider == AIProvider.BEDROCK:
                        response = await self.bedrock_service.generate_chat_response(
                            messages, context_documents, max_tokens, temperature
                        )
                    elif fallback_provider == AIProvider.OPENAI:
                        response = await self.openai_service.generate_chat_response(
                            messages, context_documents, max_tokens, temperature
                        )
                    else:  # Together
                        response = await self.together_service.generate_chat_response(
                            messages, context_documents, min(max_tokens, 2000), temperature
                        )
                    
                    return response, f"{fallback_provider.value} (fallback)", complexity
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback provider also failed: {fallback_error}")
            
            return f"I'm sorry, all AI providers are currently unavailable. Error: {str(e)}", "error", complexity
    
    async def generate_embedding_with_routing(self, text: str, force_provider: Optional[str] = None) -> List[float]:
        """Generate embedding with provider routing."""
        provider_enum = None
        if force_provider:
            try:
                provider_enum = AIProvider(force_provider.lower())
            except ValueError:
                pass
        
        if not provider_enum:
            # For embeddings, prefer the primary provider
            provider_enum = AIProvider(settings.AI_PRIMARY_PROVIDER)
        
        try:
            if provider_enum == AIProvider.TOGETHER:
                return await self.together_service.generate_embedding(text)
            elif provider_enum == AIProvider.BEDROCK:
                return await self.bedrock_service.generate_embedding(text)
            else:
                return await self.openai_service.generate_embedding(text)
                
        except Exception as e:
            logger.error(f"Primary embedding provider {provider_enum.value} failed: {e}")
            
            # Fallback for embeddings
            fallback_provider = AIProvider(settings.AI_FALLBACK_PROVIDER)
            if fallback_provider != provider_enum:
                try:
                    if fallback_provider == AIProvider.BEDROCK:
                        return await self.bedrock_service.generate_embedding(text)
                    elif fallback_provider == AIProvider.OPENAI:
                        return await self.openai_service.generate_embedding(text)
                    else:
                        return await self.together_service.generate_embedding(text)
                except Exception as fallback_error:
                    logger.error(f"Fallback embedding provider also failed: {fallback_error}")
                    raise fallback_error
            
            raise e
