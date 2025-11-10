"""
OpenAI embeddings client.
"""
from typing import List
from openai import AsyncOpenAI
from loguru import logger
from .exceptions import EmbeddingError
from ...config import config


class OpenAIEmbeddingClient:
    """OpenAI embeddings client."""
    
    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding client.
        
        Args:
            model: Model name ('text-embedding-3-small' or 'text-embedding-ada-002')
        """
        if not config.openai_api_key:
            raise EmbeddingError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
        self.model = model
        
        # Set dimension based on model
        if model == "text-embedding-3-small":
            self.dimension = 1536
        elif model == "text-embedding-ada-002":
            self.dimension = 1536
        else:
            self.dimension = 1536  # Default
        
        logger.info(f"Initialized OpenAI embedding client with model: {model}")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using OpenAI."""
        try:
            # OpenAI API handles batching internally
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            
            logger.debug(f"Generated {len(embeddings)} embeddings with OpenAI")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}")
            raise EmbeddingError(f"OpenAI embedding failed: {str(e)}")
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension

