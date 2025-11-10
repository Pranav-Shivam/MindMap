"""
Hybrid retrieval with vector search and citation extraction.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from loguru import logger
from ..vector import vector_client
from ..db import couch_client
from ..utils.embeddings import get_embedding_client


class ScopeMode(str, Enum):
    """Retrieval scope modes."""
    PAGE = "page"  # Current page only
    NEAR = "near"  # ±2 pages
    DECK = "deck"  # Entire deck


class RetrievalEngine:
    """Hybrid retrieval combining vector search and text search."""
    
    def __init__(self, embedding_provider: str = "openai_small"):
        """
        Initialize retrieval engine.
        
        Args:
            embedding_provider: Embedding provider for queries
        """
        self.embedding_provider = embedding_provider
        self.embedding_client = get_embedding_client(embedding_provider)
        self.collection_name = vector_client.get_collection_for_provider(embedding_provider)
    
    async def retrieve(
        self,
        query: str,
        doc_id: str,
        page_no: int,
        scope_mode: ScopeMode = ScopeMode.PAGE,
        top_k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            doc_id: Document ID
            page_no: Current page number
            scope_mode: Scope of retrieval (page/near/deck)
            top_k: Number of results to return
        
        Returns:
            List of relevant chunks with metadata
        """
        logger.info(f"Retrieving chunks for query: '{query[:50]}...' (scope: {scope_mode}, doc_id: {doc_id}, page_no: {page_no})")
        
        # Embed the query
        query_embedding = await self._embed_query(query)
        
        # Determine page filter based on scope
        page_filter = self._get_page_filter(doc_id, page_no, scope_mode)
        logger.debug(f"Page filter: {page_filter}")
        
        # Vector search in ChromaDB
        vector_results = await self._vector_search(
            query_embedding,
            page_filter,
            top_k=top_k * 2  # Get more candidates for potential reranking
        )
        
        # Optionally enhance with keyword search (CouchDB full-text)
        # For now, we'll use vector search as primary
        
        # Take top K results
        final_results = vector_results[:top_k]
        
        logger.info(f"Retrieved {len(final_results)} chunks")
        
        # If no results, log warning with details
        if not final_results:
            logger.warning(f"No chunks found for doc_id={doc_id}, page_no={page_no}, scope={scope_mode}, collection={self.collection_name}")
        
        return final_results
    
    async def _embed_query(self, query: str) -> List[float]:
        """Embed the query using the configured embedding provider."""
        embeddings = await self.embedding_client.embed([query])
        return embeddings[0]
    
    def _get_page_filter(
        self,
        doc_id: str,
        page_no: int,
        scope_mode: ScopeMode
    ) -> Dict[str, Any]:
        """
        Build page filter based on scope mode.
        
        Args:
            doc_id: Document ID
            page_no: Current page number
            scope_mode: Scope mode
        
        Returns:
            Filter conditions for Qdrant
        """
        filter_conditions = {"doc_id": doc_id}
        
        if scope_mode == ScopeMode.PAGE:
            # Single page only
            filter_conditions["page_no"] = page_no
        
        elif scope_mode == ScopeMode.NEAR:
            # ±2 pages - we'll need to handle this differently
            # Qdrant doesn't support range queries directly in the same way
            # We'll retrieve from all pages and filter in post-processing
            # For now, use page-only as fallback
            filter_conditions["page_no"] = page_no
            # TODO: Implement multi-page retrieval
        
        elif scope_mode == ScopeMode.DECK:
            # Entire document - just filter by doc_id
            pass
        
        return filter_conditions
    
    async def _vector_search(
        self,
        query_embedding: List[float],
        filter_conditions: Dict[str, Any],
        top_k: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Perform vector search in ChromaDB.
        
        Args:
            query_embedding: Query embedding vector
            filter_conditions: Filter conditions
            top_k: Number of results
        
        Returns:
            List of search results
        """
        logger.debug(f"Vector search with filter: {filter_conditions}, collection: {self.collection_name}")
        
        results = vector_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            filter_conditions=filter_conditions
        )
        
        logger.debug(f"Vector search returned {len(results)} results")
        
        # If no results with filter, try without page_no filter (fallback)
        if not results and filter_conditions.get("page_no") is not None:
            logger.warning(f"No results with page filter, trying without page_no filter")
            fallback_filter = {"doc_id": filter_conditions["doc_id"]}
            results = vector_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k * 2,  # Get more to filter manually
                filter_conditions=fallback_filter
            )
            
            # Filter by page_no manually
            if results:
                results = [r for r in results if r.get("page_no") == filter_conditions["page_no"]]
                logger.info(f"Fallback search found {len(results)} results after manual page filtering")
        
        return results
    
    def build_context_prompt(
        self,
        chunks: List[Dict[str, Any]],
        question: str
    ) -> List[Dict[str, str]]:
        """
        Build a context-only prompt for the LLM.
        
        Args:
            chunks: Retrieved chunks
            question: User question
        
        Returns:
            List of messages for LLM
        """
        # Build context section
        context_parts = []
        for chunk in chunks:
            chunk_ref = f"[page:{chunk['page_no']}, chunk:{chunk['chunk_index']}]"
            context_parts.append(f"{chunk_ref} {chunk['text']}")
        
        context = "\n\n".join(context_parts)
        
        # System message
        system_message = """You are a teaching assistant for MTech slides. Answer ONLY using the provided context chunks.
Each chunk has a page number and chunk ID. If the answer isn't in the context, say "I don't know."
Cite the page:chunk IDs you used in your answer.

Provide:
1. A concise, clear explanation
2. A "Deeper dive" section if needed with more details
3. Sources: List the [page:X, chunk:Y] citations you used

Keep your answer focused and educational."""
        
        # User message with context
        user_message = f"""Context:
{context}

Question: {question}"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        return messages
    
    def extract_citations(
        self,
        response_text: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract citations from LLM response.
        
        Args:
            response_text: LLM response text
            chunks: Original chunks that were provided
        
        Returns:
            List of citation objects
        """
        import re
        
        # Pattern to match [page:X, chunk:Y] or [pX:cY]
        patterns = [
            r'\[page:(\d+),\s*chunk:(\d+)\]',
            r'\[p(\d+):c(\d+)\]'
        ]
        
        citations = []
        seen_citations = set()
        
        for pattern in patterns:
            matches = re.finditer(pattern, response_text, re.IGNORECASE)
            for match in matches:
                page_no = int(match.group(1))
                chunk_index = int(match.group(2))
                
                citation_key = (page_no, chunk_index)
                if citation_key in seen_citations:
                    continue
                
                seen_citations.add(citation_key)
                
                # Find matching chunk
                for chunk in chunks:
                    if chunk['page_no'] == page_no and chunk['chunk_index'] == chunk_index:
                        citations.append({
                            "page_no": page_no,
                            "chunk_index": chunk_index,
                            "chunk_id": chunk['id'],
                            "text": chunk['text'][:200]  # First 200 chars
                        })
                        break
        
        logger.debug(f"Extracted {len(citations)} citations from response")
        return citations


async def retrieve_for_question(
    question: str,
    doc_id: str,
    page_no: int,
    scope_mode: str = "page",
    embedding_provider: str = "openai_small",
    top_k: int = 6
) -> tuple:
    """
    Convenience function to retrieve chunks and build prompt.
    
    Args:
        question: User question
        doc_id: Document ID
        page_no: Page number
        scope_mode: Retrieval scope
        embedding_provider: Embedding provider
        top_k: Number of chunks
    
    Returns:
        Tuple of (chunks, messages)
    """
    engine = RetrievalEngine(embedding_provider)
    
    # Convert scope mode string to enum
    scope = ScopeMode(scope_mode.lower())
    
    # Retrieve chunks
    chunks = await engine.retrieve(
        query=question,
        doc_id=doc_id,
        page_no=page_no,
        scope_mode=scope,
        top_k=top_k
    )
    
    # Build prompt
    messages = engine.build_context_prompt(chunks, question)
    
    return chunks, messages

