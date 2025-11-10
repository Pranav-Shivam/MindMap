"""
Base protocol for embedding clients.
"""
from typing import Protocol, List
from enum import Enum


class EmbeddingProvider(str, Enum):
    """Embedding provider options."""
    OPENAI_SMALL = "openai_small"
    OPENAI_ADA002 = "openai_ada002"
    OLLAMA_NOMIC = "ollama_nomic"


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

