"""
Page-related API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger
from ..auth.jwt_auth import get_current_user
from ..db import couch_client
from ..config import config
from ..utils.fix_summaries import check_missing_summaries, regenerate_summaries

router = APIRouter(prefix="/api", tags=["pages"])


class PageResponse(BaseModel):
    """Page response model."""
    page_no: int
    preview_image_path: Optional[str] = None
    ready: bool = False


class PageDetailResponse(BaseModel):
    """Detailed page response."""
    page_no: int
    text: str
    summary: str
    key_terms: List[str]
    preview_image_path: Optional[str] = None
    ready: bool
    qa: List[dict] = []
    embedding_provider: Optional[str] = "openai_small"  # Embedding provider used for this document


class RegenerateSummariesRequest(BaseModel):
    """Request model for regenerating summaries."""
    page_numbers: Optional[List[int]] = None  # If None, regenerates all missing summaries
    llm_provider: Optional[str] = "gpt"
    llm_model: Optional[str] = "gpt-4o-mini"


@router.get("/documents/{doc_id}/pages", response_model=List[PageResponse])
async def list_pages(
    doc_id: str,
    offset: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    List pages for a document.
    
    Args:
        doc_id: Document ID
        offset: Pagination offset
        limit: Pagination limit
        current_user: Current authenticated user
    
    Returns:
        List of pages
    """
    try:
        # Verify document ownership
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc or doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Query pages
        page_docs = couch_client.find_pages_by_document(config.pages_db, doc_id, offset, limit)
        
        pages = []
        for page_doc in page_docs:
            pages.append(PageResponse(
                page_no=page_doc["page_no"],
                preview_image_path=page_doc.get("preview_image_path"),
                ready=page_doc.get("ready", False)
            ))
        
        return pages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing pages for {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pages"
        )


@router.get("/documents/{doc_id}/page/{page_no}", response_model=PageDetailResponse)
async def get_page(
    doc_id: str,
    page_no: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed page information.
    
    Args:
        doc_id: Document ID
        page_no: Page number
        current_user: Current authenticated user
    
    Returns:
        Page details including past Q&A
    """
    try:
        # Verify document ownership
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc or doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Get page document
        page_id = f"{doc_id}_page_{page_no}"
        page_doc = couch_client.get_doc(config.pages_db, page_id)
        
        if not page_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        
        # Get past Q&A for this page
        qa_docs = couch_client.find_qa_by_page(config.qa_db, doc_id, page_no)
        
        past_qa = []
        for qa_doc in qa_docs:
            past_qa.append({
                "id": qa_doc["_id"],
                "page_no": qa_doc.get("page_no", page_no),  # Include page_no for frontend filtering
                "question": qa_doc["question"],
                "answer": qa_doc["answer"],
                "scope_mode": qa_doc.get("scope_mode"),
                "citations": qa_doc.get("citations", []),
                "created_at": qa_doc["created_at"]
            })
        
        # Get embedding provider from document
        embedding_provider = doc.get("embedding_provider", "openai_small")
        
        return PageDetailResponse(
            page_no=page_doc["page_no"],
            text=page_doc.get("text", ""),
            summary=page_doc.get("summary", ""),
            key_terms=page_doc.get("key_terms", []),
            preview_image_path=page_doc.get("preview_image_path"),
            ready=page_doc.get("ready", False),
            qa=past_qa,
            embedding_provider=embedding_provider
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page {page_no} for {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get page"
        )


@router.get("/documents/{doc_id}/page/{page_no}/preview")
async def get_page_preview(
    doc_id: str,
    page_no: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get page preview image.
    
    Args:
        doc_id: Document ID
        page_no: Page number
        current_user: Current authenticated user
    
    Returns:
        Preview image file
    """
    try:
        # Verify document ownership
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc or doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Get page document
        page_id = f"{doc_id}_page_{page_no}"
        page_doc = couch_client.get_doc(config.pages_db, page_id)
        
        if not page_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        
        preview_path = page_doc.get("preview_image_path")
        if not preview_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preview not available"
            )
        
        return FileResponse(preview_path, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preview for page {page_no}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get preview"
        )


@router.get("/documents/{doc_id}/check-missing-summaries")
async def check_missing_summaries_api(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check which pages are missing summaries for a document.
    
    Args:
        doc_id: Document ID
        current_user: Current authenticated user
    
    Returns:
        List of pages with missing summaries
    """
    try:
        # Verify document ownership
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc or doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Check for missing summaries
        missing = await check_missing_summaries(doc_id)
        
        if doc_id not in missing:
            return {
                "document_id": doc_id,
                "missing_summaries": [],
                "count": 0
            }
        
        return {
            "document_id": doc_id,
            "missing_summaries": missing[doc_id],
            "count": len(missing[doc_id])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking missing summaries for {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check missing summaries"
        )


@router.post("/documents/{doc_id}/regenerate-summaries")
async def regenerate_summaries_api(
    doc_id: str,
    request: RegenerateSummariesRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Regenerate summaries for pages in a document.
    Can regenerate specific pages or all pages with missing summaries.
    
    Args:
        doc_id: Document ID
        request: Regeneration request data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
    
    Returns:
        Status message
    """
    try:
        # Verify document ownership
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc or doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Check what pages need regeneration
        if request.page_numbers:
            pages_to_process = request.page_numbers
            message = f"Regenerating summaries for {len(pages_to_process)} specific pages"
        else:
            missing = await check_missing_summaries(doc_id)
            if doc_id not in missing:
                return {
                    "status": "success",
                    "message": "No pages with missing summaries found",
                    "pages_to_process": 0
                }
            pages_to_process = [p['page_no'] for p in missing[doc_id]]
            message = f"Regenerating summaries for {len(pages_to_process)} pages with missing summaries"
        
        logger.info(f"{message} in document {doc_id}")
        
        # Trigger regeneration in background
        background_tasks.add_task(
            regenerate_summaries,
            doc_id=doc_id,
            page_numbers=request.page_numbers,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model
        )
        
        return {
            "status": "processing",
            "message": message,
            "pages_to_process": len(pages_to_process),
            "page_numbers": pages_to_process
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting summary regeneration for {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start summary regeneration"
        )

