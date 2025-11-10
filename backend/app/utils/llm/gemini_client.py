"""
Google Gemini client implementation.
"""
from typing import AsyncGenerator, List, Dict, Any
import google.generativeai as genai
from loguru import logger
from .exceptions import LLMError, StreamingError
from ...config import config


class GeminiClient:
    """Google Gemini chat client with streaming support."""
    
    def __init__(self, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client.
        
        Args:
            model: Model name (e.g., 'gemini-1.5-flash', 'gemini-1.5-pro')
        """
        if not config.google_api_key:
            raise LLMError("Google API key not configured")
        
        genai.configure(api_key=config.google_api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        
        logger.info(f"Initialized Gemini client with model: {model}")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from Gemini."""
        try:
            # Convert messages to Gemini format
            # Gemini expects alternating user/model messages
            gemini_messages = []
            system_instruction = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                elif msg["role"] == "user":
                    gemini_messages.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
                elif msg["role"] == "assistant":
                    gemini_messages.append({
                        "role": "model",
                        "parts": [msg["content"]]
                    })
            
            # Configure generation
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            # Start chat
            chat = self.model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            
            # Get last user message
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
            
            # Stream response
            response = await chat.send_message_async(
                last_message,
                generation_config=generation_config,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Error streaming from Gemini: {e}")
            raise StreamingError(f"Gemini streaming failed: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count for Gemini."""
        try:
            # Gemini has a count_tokens method
            result = self.model.count_tokens(text)
            return result.total_tokens
        except:
            # Fallback approximation
            return len(text) // 4

