"""
Server-Sent Events (SSE) utilities for streaming responses.
"""
import json
from typing import Dict, Any, AsyncGenerator
from loguru import logger


def format_sse_message(data: Dict[str, Any]) -> str:
    """
    Format a message for SSE transmission.
    
    Args:
        data: Dictionary to send as JSON
    
    Returns:
        Formatted SSE message string
    """
    return f"data: {json.dumps(data)}\n\n"


async def sse_generator(message_generator: AsyncGenerator) -> AsyncGenerator[str, None]:
    """
    Wrap an async generator to produce SSE-formatted messages.
    
    Args:
        message_generator: Async generator yielding dictionaries
    
    Yields:
        SSE-formatted strings
    """
    try:
        async for message in message_generator:
            if isinstance(message, dict):
                yield format_sse_message(message)
            elif isinstance(message, str):
                # If it's a plain string token, wrap it
                yield format_sse_message({"token": message})
            else:
                logger.warning(f"Unexpected message type in SSE: {type(message)}")
                
    except Exception as e:
        logger.error(f"Error in SSE generator: {e}")
        # Send error message to client
        yield format_sse_message({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Send done signal
        logger.debug("SSE stream completed")


def create_token_message(token: str) -> Dict[str, Any]:
    """Create a token message for streaming."""
    return {"type": "token", "token": token}


def create_done_message(citations: list = None, qa_id: str = None) -> Dict[str, Any]:
    """Create a completion message."""
    message = {"type": "done"}
    if citations:
        message["citations"] = citations
    if qa_id:
        message["qa_id"] = qa_id
    return message


def create_error_message(error: str) -> Dict[str, Any]:
    """Create an error message."""
    return {"type": "error", "message": error}


def create_metadata_message(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create a metadata message."""
    return {"type": "metadata", **metadata}

