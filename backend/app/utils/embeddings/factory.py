"""
Factory for creating embedding clients.
"""
from typing import Optional
from loguru import logger
from .base import EmbeddingProvider, EmbeddingClient
from .openai_embeddings import OpenAIEmbeddingClient
from .ollama_embeddings import OllamaEmbeddingClient
from .exceptions import ProviderNotAvailableError, EmbeddingError
from ...config import config


def get_embedding_client(provider: str = "openai_small") -> EmbeddingClient:
    """
    Factory function to get THE embedding client (text-embedding-3-small ONLY).
    
    Args:
        provider: Ignored - always returns text-embedding-3-small client
    
    Returns:
        OpenAI text-embedding-3-small client
    
    Raises:
        ProviderNotAvailableError: If OpenAI API key is not configured
        EmbeddingError: If client creation fails
    """
    # ALWAYS use text-embedding-3-small - ignore provider parameter
    try:
        if not config.openai_api_key:
            raise ProviderNotAvailableError("OpenAI API key not configured")
        return OpenAIEmbeddingClient(model="text-embedding-3-small")
    
    except ProviderNotAvailableError:
        raise
    except Exception as e:
        logger.error(f"Error creating text-embedding-3-small client: {e}")
        raise EmbeddingError(f"Failed to create embedding client: {str(e)}")


def get_available_embedding_providers() -> dict:
    """
    Get THE ONLY embedding provider (text-embedding-3-small).
    
    Returns:
        Dictionary with the single embedding provider
    """
    providers = {}
    
    # ONLY one embedding provider - text-embedding-3-small
    if config.openai_api_key:
        providers["openai_small"] = {
            "available": True,
            "model": "text-embedding-3-small",
            "dimension": 1536,
            "collection": "chunks_openai_small",
            "locked": True  # This is the only option
        }
    
    return providers

