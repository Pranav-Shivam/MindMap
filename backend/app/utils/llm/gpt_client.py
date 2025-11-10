"""
OpenAI GPT client implementation.
"""
from typing import AsyncGenerator, List, Dict, Any
import tiktoken
from openai import AsyncOpenAI
from loguru import logger
from .exceptions import LLMError, StreamingError
from ...config import config


class GPTClient:
    """OpenAI GPT chat client with streaming support."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize GPT client.
        
        Args:
            model: Model name (e.g., 'gpt-4o-mini', 'gpt-4', 'gpt-3.5-turbo')
        """
        if not config.openai_api_key:
            raise LLMError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
        self.model = model
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        logger.info(f"Initialized GPT client with model: {model}")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from OpenAI."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming from GPT: {e}")
            raise StreamingError(f"GPT streaming failed: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            return len(self.encoding.encode(text))
        except:
            # Fallback to rough approximation
            return len(text) // 4

