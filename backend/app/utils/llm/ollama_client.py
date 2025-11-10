"""
Ollama local LLM client implementation.
"""
from typing import AsyncGenerator, List, Dict, Any
import httpx
import json
from loguru import logger
from .exceptions import LLMError, StreamingError
from ...config import config


class OllamaClient:
    """Ollama chat client with streaming support."""
    
    def __init__(self, model: str = "llama3.1"):
        """
        Initialize Ollama client.
        
        Args:
            model: Model name (e.g., 'llama3.1', 'mistral', 'codellama')
        """
        self.base_url = config.ollama_base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
        
        logger.info(f"Initialized Ollama client with model: {model} at {self.base_url}")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from Ollama."""
        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    **kwargs.get("options", {})
                }
            }
            
            async with self.client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    raise StreamingError(f"Ollama returned status {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                content = data["message"]["content"]
                                if content:
                                    yield content
                            
                            # Check if done
                            if data.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode Ollama response: {line}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error streaming from Ollama: {e}")
            raise StreamingError(f"Ollama streaming failed: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count (rough estimate for Ollama)."""
        # Ollama doesn't provide direct token counting
        # Use rough approximation: ~4 characters per token
        return len(text) // 4
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

