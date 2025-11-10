"""
Q&A API routes with SSE streaming.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger
from ..auth.jwt_auth import get_current_user
from ..db import couch_client
from ..config import config
from ..utils.llm import get_chat_client
from ..utils.retrieval import retrieve_for_question, RetrievalEngine
from ..utils.sse import format_sse_message
import json


router = APIRouter(prefix="/api", tags=["qa"])


class QuestionRequest(BaseModel):
    """Question request model."""
    question: str
    scope_mode: str = "page"
    llm_provider: Optional[str] = "gpt"
    llm_model: Optional[str] = None
    embedding_provider: Optional[str] = "openai_small"  # Always openai_small (text-embedding-3-small)


@router.post("/documents/{doc_id}/page/{page_no}/qa")
async def ask_question_stream(
    doc_id: str,
    page_no: int,
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ask a question about a page with streaming response (SSE).
    
    Args:
        doc_id: Document ID
        page_no: Page number
        request: Question request data
        current_user: Current authenticated user
    
    Returns:
        SSE stream with tokens and final citations
    """
    try:
        # Verify document ownership
        logger.info(f"QA request for doc_id: {doc_id}, user_id: {current_user.get('_id')}")
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc:
            logger.warning(f"Document {doc_id} not found in {config.documents_db}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        if doc.get("owner_id") != current_user["_id"]:
            logger.warning(f"Authorization failed: doc owner_id={doc.get('owner_id')}, user_id={current_user.get('_id')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        logger.info(f"Document authorization successful for doc_id: {doc_id}")
        
        async def generate_answer():
            """Generator function for SSE streaming."""
            try:
                # Retrieve relevant chunks - ALWAYS use openai_small
                chunks, messages = await retrieve_for_question(
                    question=request.question,
                    doc_id=doc_id,
                    page_no=page_no,
                    scope_mode=request.scope_mode,
                    embedding_provider="openai_small"  # LOCKED to text-embedding-3-small
                )
                
                if not chunks:
                    # Check if document ingestion completed
                    doc_status = couch_client.get_doc(config.documents_db, doc_id)
                    ingestion_completed = doc_status.get("ingestion_completed", False) if doc_status else False
                    
                    if not ingestion_completed:
                        error_msg = "Document ingestion is not complete. Please wait for the document to finish processing, or re-upload the document."
                    else:
                        # Check if any chunks exist for this document at all
                        from ..vector import vector_client
                        from ..utils.embeddings import get_embedding_client
                        try:
                            # Create a dummy embedding just to check if chunks exist
                            embedding_client = get_embedding_client("openai_small")
                            dummy_embedding = await embedding_client.embed(["test"])
                            collection_name = vector_client.get_collection_for_provider("openai_small")
                            
                            # Try a simple search without page filter to see if any chunks exist for this doc
                            test_results = vector_client.search(
                                collection_name=collection_name,
                                query_vector=dummy_embedding[0],
                                limit=1,
                                filter_conditions={"doc_id": doc_id}
                            )
                            if not test_results:
                                error_msg = "No content chunks found for this document. The document may need to be re-ingested. Please try re-uploading the document."
                            else:
                                error_msg = f"No relevant content found on page {page_no + 1} to answer your question. Try asking about a different page or use 'deck' scope to search the entire document."
                        except Exception as e:
                            logger.error(f"Error checking document chunks: {e}")
                            error_msg = "No relevant content found to answer your question. The document may need to be re-ingested."
                    
                    yield format_sse_message({
                        "type": "error",
                        "message": error_msg
                    })
                    return
                
                # Get LLM client
                llm_client = get_chat_client(
                    request.llm_provider,
                    request.llm_model
                )
                
                # Stream answer
                full_answer = ""
                async for token in llm_client.stream_chat(messages):
                    full_answer += token
                    yield format_sse_message({
                        "type": "token",
                        "token": token
                    })
                
                # Extract citations
                retrieval_engine = RetrievalEngine(request.embedding_provider)
                citations = retrieval_engine.extract_citations(full_answer, chunks)
                
                # Save Q&A to CouchDB
                qa_doc = {
                    "type": "qa",
                    "document_id": doc_id,
                    "page_no": page_no,
                    "user_id": current_user["_id"],
                    "question": request.question,
                    "answer": full_answer,
                    "scope_mode": request.scope_mode,
                    "citations": citations,
                    "llm_provider": request.llm_provider,
                    "embedding_provider": request.embedding_provider,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                qa_id = couch_client.save_doc(config.qa_db, qa_doc)
                
                # Send completion message with citations
                yield format_sse_message({
                    "type": "done",
                    "qa_id": qa_id,
                    "citations": citations
                })
                
            except Exception as e:
                logger.error(f"Error in Q&A stream: {e}")
                yield format_sse_message({
                    "type": "error",
                    "message": str(e)
                })
        
        return StreamingResponse(
            generate_answer(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up Q&A stream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get("/documents/{doc_id}/qa")
async def get_document_qa(
    doc_id: str,
    offset: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all Q&A for a document with pagination.
    
    Args:
        doc_id: Document ID
        offset: Number of Q&A records to skip (for pagination)
        limit: Maximum number of Q&A to return
        current_user: Current authenticated user
    
    Returns:
        List of Q&A
    """
    try:
        # Verify document ownership
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc or doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Query Q&A with pagination
        qa_docs = couch_client.find_qa_by_document(config.qa_db, doc_id, offset, limit)
        
        qa_list = []
        for qa_doc in qa_docs:
            qa_list.append({
                "id": qa_doc["_id"],
                "page_no": qa_doc["page_no"],
                "question": qa_doc["question"],
                "answer": qa_doc["answer"],
                "scope_mode": qa_doc.get("scope_mode"),
                "citations": qa_doc.get("citations", []),
                "created_at": qa_doc["created_at"]
            })
        
        return qa_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Q&A for {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Q&A"
        )

