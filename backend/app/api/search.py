"""
Search API routes for Q&A and page content.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from loguru import logger
from ..auth.jwt_auth import get_current_user
from ..db import couch_client
from ..vector import vector_client
from ..utils.embeddings import get_embedding_client
from ..config import config


router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResult(BaseModel):
    """Search result model."""
    type: str  # "qa" or "page"
    doc_id: str
    page_no: int
    snippet: str
    score: float
    metadata: dict = {}


@router.get("", response_model=List[SearchResult])
async def search(
    q: str = Query(..., min_length=1),
    doc_id: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    Search across Q&A and page content.
    
    Args:
        q: Search query
        doc_id: Optional document ID to limit search
        limit: Maximum number of results
        current_user: Current authenticated user
    
    Returns:
        List of search results
    """
    try:
        results = []
        
        # Search Q&A in CouchDB
        qa_results = _search_qa(q, doc_id, current_user["_id"], limit // 2)
        results.extend(qa_results)
        
        # Search page content (simple text matching for now)
        # Could enhance with vector search later
        page_results = _search_pages(q, doc_id, current_user["_id"], limit // 2)
        results.extend(page_results)
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
        
    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


def _search_qa(
    query: str,
    doc_id: Optional[str],
    user_id: str,
    limit: int
) -> List[SearchResult]:
    """Search Q&A documents."""
    try:
        # Query all Q&A (simple approach - could be optimized)
        if doc_id:
            qa_docs = couch_client.find_qa_by_document(config.qa_db, doc_id, limit=1000)
        else:
            # Get all Q&A for user's documents
            qa_docs = couch_client.find_all_qa(config.qa_db)
        
        search_results = []
        query_lower = query.lower()
        
        for qa_doc in qa_docs:
            
            # Simple text matching
            question = qa_doc.get("question", "").lower()
            answer = qa_doc.get("answer", "").lower()
            
            score = 0.0
            if query_lower in question:
                score += 2.0
            if query_lower in answer:
                score += 1.0
            
            # Word matching
            query_words = query_lower.split()
            for word in query_words:
                if word in question:
                    score += 0.3
                if word in answer:
                    score += 0.1
            
            if score > 0:
                snippet = qa_doc.get("answer", "")[:200]
                search_results.append(SearchResult(
                    type="qa",
                    doc_id=qa_doc["document_id"],
                    page_no=qa_doc["page_no"],
                    snippet=snippet,
                    score=score,
                    metadata={
                        "question": qa_doc.get("question"),
                        "qa_id": qa_doc.get("_id")
                    }
                ))
        
        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results[:limit]
        
    except Exception as e:
        logger.error(f"Error searching Q&A: {e}")
        return []


def _search_pages(
    query: str,
    doc_id: Optional[str],
    user_id: str,
    limit: int
) -> List[SearchResult]:
    """Search page content."""
    try:
        # Query pages
        if doc_id:
            page_docs = couch_client.find_pages_by_document(config.pages_db, doc_id, offset=0, limit=1000)
        else:
            # This would need a better index in production - for now return empty
            page_docs = []
        
        search_results = []
        query_lower = query.lower()
        
        for page_doc in page_docs:
            
            text = page_doc.get("text", "").lower()
            summary = page_doc.get("summary", "").lower()
            
            score = 0.0
            if query_lower in summary:
                score += 1.5
            if query_lower in text:
                score += 0.5
            
            # Word matching
            query_words = query_lower.split()
            for word in query_words:
                if word in summary:
                    score += 0.2
                if word in text:
                    score += 0.1
            
            if score > 0:
                snippet = page_doc.get("summary") or page_doc.get("text", "")[:200]
                search_results.append(SearchResult(
                    type="page",
                    doc_id=page_doc["document_id"],
                    page_no=page_doc["page_no"],
                    snippet=snippet,
                    score=score,
                    metadata={
                        "summary": page_doc.get("summary")
                    }
                ))
        
        search_results.sort(key=lambda x: x.score, reverse=True)
        return search_results[:limit]
        
    except Exception as e:
        logger.error(f"Error searching pages: {e}")
        return []

