"""
Base protocol for embedding clients.
"""
from typing import Protocol, List
from enum import Enum


class EmbeddingProvider(str, Enum):
    """Embedding provider - ONLY ONE option: text-embedding-3-small."""
    OPENAI_SMALL = "openai_small"  # text-embedding-3-small (1536 dims) - ONLY OPTION


class EmbeddingClient(Protocol):
    """Protocol for embedding clients."""
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors
        """
        ...
    
    def get_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        ...

