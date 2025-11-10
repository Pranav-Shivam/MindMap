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


def get_embedding_client(provider: str) -> EmbeddingClient:
    """
    Factory function to get an embedding client for the specified provider.
    
    Args:
        provider: Provider name ('openai_small', 'openai_ada002', 'ollama_nomic')
    
    Returns:
        EmbeddingClient instance
    
    Raises:
        ProviderNotAvailableError: If provider is not configured
        EmbeddingError: If client creation fails
    """
    provider = provider.lower()
    
    try:
        if provider == EmbeddingProvider.OPENAI_SMALL:
            if not config.openai_api_key:
                raise ProviderNotAvailableError("OpenAI API key not configured")
            return OpenAIEmbeddingClient(model="text-embedding-3-small")
        
        elif provider == EmbeddingProvider.OPENAI_ADA002:
            if not config.openai_api_key:
                raise ProviderNotAvailableError("OpenAI API key not configured")
            return OpenAIEmbeddingClient(model="text-embedding-ada-002")
        
        elif provider == EmbeddingProvider.OLLAMA_NOMIC:
            if not config.allow_local_ollama:
                raise ProviderNotAvailableError("Ollama is disabled by configuration")
            return OllamaEmbeddingClient(model="nomic-embed-text")
        
        else:
            raise ProviderNotAvailableError(f"Unknown embedding provider: {provider}")
    
    except ProviderNotAvailableError:
        raise
    except Exception as e:
        logger.error(f"Error creating embedding client for {provider}: {e}")
        raise EmbeddingError(f"Failed to create {provider} embedding client: {str(e)}")


def get_available_embedding_providers() -> dict:
    """
    Get list of available embedding providers based on configuration.
    
    Returns:
        Dictionary with provider availability and dimensions
    """
    providers = {}
    
    if config.openai_api_key:
        providers["openai_small"] = {
            "available": True,
            "model": "text-embedding-3-small",
            "dimension": 1536,
            "collection": "chunks_openai_small"
        }
        providers["openai_ada002"] = {
            "available": True,
            "model": "text-embedding-ada-002",
            "dimension": 1536,
            "collection": "chunks_openai_ada"
        }
    
    if config.allow_local_ollama:
        providers["ollama_nomic"] = {
            "available": True,
            "model": "nomic-embed-text",
            "dimension": 768,
            "collection": "chunks_ollama_nomic"
        }
    
    return providers

