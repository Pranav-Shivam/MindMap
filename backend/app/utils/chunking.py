"""
Text chunking utilities with sentence-aware splitting.
"""
import re
from typing import List, Dict, Any
import nltk
from loguru import logger

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


class TextChunker:
    """Sentence-aware text chunking for embeddings."""
    
    def __init__(
        self,
        target_chunk_size: int = 600,
        min_chunk_size: int = 400,
        max_chunk_size: int = 800,
        overlap_size: int = 75
    ):
        """
        Initialize chunker.
        
        Args:
            target_chunk_size: Target size in tokens
            min_chunk_size: Minimum chunk size in tokens
            max_chunk_size: Maximum chunk size in tokens
            overlap_size: Overlap between chunks in tokens
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_text(self, text: str, page_no: int = 0) -> List[Dict[str, Any]]:
        """
        Chunk text into sentence-aware segments.
        
        Args:
            text: Text to chunk
            page_no: Page number for metadata
        
        Returns:
            List of chunk dicts with text, page_no, chunk_index, and token_count
        """
        if not text.strip():
            return []
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_size = self._estimate_tokens(sentence)
            
            # If adding this sentence would exceed max size, finalize current chunk
            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "page_no": page_no,
                    "chunk_index": chunk_index,
                    "token_count": current_size
                })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.overlap_size
                )
                current_chunk = overlap_sentences
                current_size = sum(self._estimate_tokens(s) for s in current_chunk)
                chunk_index += 1
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
            
            # If we've reached target size and have enough content, finalize
            if current_size >= self.target_chunk_size and current_size >= self.min_chunk_size:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "page_no": page_no,
                    "chunk_index": chunk_index,
                    "token_count": current_size
                })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.overlap_size
                )
                current_chunk = overlap_sentences
                current_size = sum(self._estimate_tokens(s) for s in current_chunk)
                chunk_index += 1
        
        # Add remaining sentences as final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            # Only add if it meets minimum size or is the only chunk
            if current_size >= self.min_chunk_size or not chunks:
                chunks.append({
                    "text": chunk_text,
                    "page_no": page_no,
                    "chunk_index": chunk_index,
                    "token_count": current_size
                })
            else:
                # Append to last chunk if too small
                if chunks:
                    chunks[-1]["text"] += " " + chunk_text
                    chunks[-1]["token_count"] += current_size
        
        logger.debug(f"Created {len(chunks)} chunks from page {page_no}")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK."""
        try:
            sentences = nltk.sent_tokenize(text)
            return [s.strip() for s in sentences if s.strip()]
        except Exception as e:
            logger.warning(f"NLTK sentence tokenization failed: {e}, using fallback")
            # Fallback to simple splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough approximation: ~4 characters per token
        # More accurate would use tiktoken, but this is faster
        return len(text) // 4
    
    def _get_overlap_sentences(
        self,
        sentences: List[str],
        overlap_tokens: int
    ) -> List[str]:
        """Get last N sentences that fit within overlap token limit."""
        overlap_sentences = []
        current_tokens = 0
        
        # Iterate from end backwards
        for sentence in reversed(sentences):
            sentence_tokens = self._estimate_tokens(sentence)
            if current_tokens + sentence_tokens <= overlap_tokens:
                overlap_sentences.insert(0, sentence)
                current_tokens += sentence_tokens
            else:
                break
        
        return overlap_sentences


def chunk_page_text(
    text: str,
    page_no: int,
    target_size: int = 600,
    overlap: int = 75
) -> List[Dict[str, Any]]:
    """
    Convenience function to chunk a page's text.
    
    Args:
        text: Page text
        page_no: Page number
        target_size: Target chunk size in tokens
        overlap: Overlap in tokens
    
    Returns:
        List of chunk dicts
    """
    chunker = TextChunker(
        target_chunk_size=target_size,
        overlap_size=overlap
    )
    return chunker.chunk_text(text, page_no=page_no)

