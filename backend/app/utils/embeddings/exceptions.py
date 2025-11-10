"""
Custom exceptions for embedding operations.
"""


class EmbeddingError(Exception):
    """Base exception for embedding-related errors."""
    pass


class ProviderNotAvailableError(EmbeddingError):
    """Raised when an embedding provider is not configured or available."""
    pass

