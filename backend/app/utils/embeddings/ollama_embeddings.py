"""
Ollama embeddings client (local).
"""
from typing import List
import httpx
import json
from loguru import logger
from .exceptions import EmbeddingError
from ...config import config


class OllamaEmbeddingClient:
    """Ollama embeddings client for local models."""
    
    def __init__(self, model: str = "nomic-embed-text"):
        """
        Initialize Ollama embedding client.
        
        Args:
            model: Model name (e.g., 'nomic-embed-text', 'bge-m3')
        """
        self.base_url = config.ollama_base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # Dimension varies by model
        if "nomic-embed-text" in model:
            self.dimension = 768
        elif "bge-m3" in model:
            self.dimension = 1024
        else:
            self.dimension = 768  # Default
        
        logger.info(f"Initialized Ollama embedding client with model: {model}")
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using Ollama."""
        try:
            url = f"{self.base_url}/api/embeddings"
            embeddings = []
            
            # Ollama processes one text at a time
            for text in texts:
                payload = {
                    "model": self.model,
                    "prompt": text
                }
                
                response = await self.client.post(url, json=payload)
                
                if response.status_code != 200:
                    raise EmbeddingError(f"Ollama returned status {response.status_code}")
                
                data = response.json()
                if "embedding" in data:
                    embeddings.append(data["embedding"])
                else:
                    raise EmbeddingError("No embedding in Ollama response")
            
            logger.debug(f"Generated {len(embeddings)} embeddings with Ollama")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating Ollama embeddings: {e}")
            raise EmbeddingError(f"Ollama embedding failed: {str(e)}")
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

