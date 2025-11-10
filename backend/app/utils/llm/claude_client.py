"""
Anthropic Claude client implementation.
"""
from typing import AsyncGenerator, List, Dict, Any
from anthropic import AsyncAnthropic
from loguru import logger
from .exceptions import LLMError, StreamingError
from ...config import config


class ClaudeClient:
    """Anthropic Claude chat client with streaming support."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Claude client.
        
        Args:
            model: Model name (e.g., 'claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307')
        """
        if not config.anthropic_api_key:
            raise LLMError("Anthropic API key not configured")
        
        self.client = AsyncAnthropic(api_key=config.anthropic_api_key)
        self.model = model
        
        logger.info(f"Initialized Claude client with model: {model}")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from Claude."""
        try:
            # Extract system message if present
            system_message = None
            claude_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Build request params
            params = {
                "model": self.model,
                "messages": claude_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            if system_message:
                params["system"] = system_message
            
            # Stream response
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield text
                        
        except Exception as e:
            logger.error(f"Error streaming from Claude: {e}")
            raise StreamingError(f"Claude streaming failed: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count for Claude."""
        try:
            # Claude uses similar tokenization to GPT
            # Rough approximation: ~4 characters per token
            return len(text) // 4
        except:
            return len(text) // 4

