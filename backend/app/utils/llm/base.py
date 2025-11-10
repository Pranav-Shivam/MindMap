"""
Base protocol for LLM chat clients.
"""
from typing import Protocol, AsyncGenerator, List, Dict, Any
from enum import Enum


class LlmProvider(str, Enum):
    """LLM provider options."""
    GPT = "gpt"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    CLAUDE = "claude"


class ChatClient(Protocol):
    """Protocol for chat completion clients."""
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Provider-specific options
        
        Yields:
            Token strings
        """
        ...
    
    def count_tokens(self, text: str) -> int:
        """
        Approximate token count for text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Approximate token count
        """
        ...

