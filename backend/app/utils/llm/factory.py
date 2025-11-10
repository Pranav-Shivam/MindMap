"""
Factory for creating LLM clients.
"""
from typing import Optional
from loguru import logger
from .base import LlmProvider, ChatClient
from .gpt_client import GPTClient
from .ollama_client import OllamaClient
from .gemini_client import GeminiClient
from .claude_client import ClaudeClient
from .exceptions import ProviderNotAvailableError, LLMError
from ...config import config


def get_chat_client(
    provider: str,
    model: Optional[str] = None
) -> ChatClient:
    """
    Factory function to get a chat client for the specified provider.
    
    Args:
        provider: Provider name ('gpt', 'ollama', 'gemini', 'claude')
        model: Optional model name (uses defaults if not provided)
    
    Returns:
        ChatClient instance
    
    Raises:
        ProviderNotAvailableError: If provider is not configured
        LLMError: If client creation fails
    """
    provider = provider.lower()
    
    try:
        if provider == LlmProvider.GPT:
            if not config.openai_api_key:
                raise ProviderNotAvailableError("OpenAI API key not configured")
            model = model or "gpt-4o-mini"
            return GPTClient(model=model)
        
        elif provider == LlmProvider.OLLAMA:
            if not config.allow_local_ollama:
                raise ProviderNotAvailableError("Ollama is disabled by configuration")
            model = model or "llama3.1"
            return OllamaClient(model=model)
        
        elif provider == LlmProvider.GEMINI:
            if not config.google_api_key:
                raise ProviderNotAvailableError("Google API key not configured")
            model = model or "gemini-1.5-flash"
            return GeminiClient(model=model)
        
        elif provider == LlmProvider.CLAUDE:
            if not config.anthropic_api_key:
                raise ProviderNotAvailableError("Anthropic API key not configured")
            model = model or "claude-3-5-sonnet-20241022"
            return ClaudeClient(model=model)
        
        else:
            raise ProviderNotAvailableError(f"Unknown provider: {provider}")
    
    except ProviderNotAvailableError:
        raise
    except Exception as e:
        logger.error(f"Error creating chat client for {provider}: {e}")
        raise LLMError(f"Failed to create {provider} client: {str(e)}")


def get_available_providers() -> dict:
    """
    Get list of available providers based on configuration.
    
    Returns:
        Dictionary with provider availability and default models
    """
    providers = {}
    
    if config.openai_api_key:
        providers["gpt"] = {
            "available": True,
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "default": "gpt-4o-mini"
        }
    
    if config.allow_local_ollama:
        providers["ollama"] = {
            "available": True,
            "models": ["llama3.1", "llama2", "mistral", "codellama", "phi3"],
            "default": "llama3.1"
        }
    
    if config.google_api_key:
        providers["gemini"] = {
            "available": True,
            "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
            "default": "gemini-1.5-flash"
        }
    
    if config.anthropic_api_key:
        providers["claude"] = {
            "available": True,
            "models": [
                "claude-sonnet-4-5",
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307"
            ],
            "default": "claude-3-5-sonnet-20241022"
        }
    
    return providers

