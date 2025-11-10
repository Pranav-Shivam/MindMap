"""
Custom exceptions for LLM operations.
"""


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class ProviderNotAvailableError(LLMError):
    """Raised when a provider is not configured or available."""
    pass


class StreamingError(LLMError):
    """Raised when streaming fails."""
    pass


class TokenLimitError(LLMError):
    """Raised when token limit is exceeded."""
    pass

