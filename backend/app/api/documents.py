"""
Document management API routes.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger
from ..auth.jwt_auth import get_current_user
from ..db import couch_client
from ..workers.background_tasks import enqueue_ingestion
from ..config import config
from ..utils.llm.factory import get_available_providers
from ..utils.embeddings.factory import get_available_embedding_providers


router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    title: str
    page_count: Optional[int] = None
    created_at: str
    ingestion_completed: bool = False
    embedding_provider: Optional[str] = None


class UploadResponse(BaseModel):
    """Upload response model."""
    doc_id: str
    job_id: str
    message: str


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    summary_llm_provider: str = Form("gpt"),
    summary_llm_model: str = Form("gpt-4o-mini"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a PDF document and start ingestion.
    
    Args:
        file: PDF file
        summary_llm_provider: LLM provider for summarization
        summary_llm_model: LLM model for summarization
        current_user: Current authenticated user
    
    Returns:
        Document ID and job ID
    
    Note:
        Embedding provider is ALWAYS openai_small (text-embedding-3-small) - no configuration needed
    """
    try:
        # Log received parameters for debugging
        logger.info(f"Upload request received - LLM Provider: {summary_llm_provider}, Model: {summary_llm_model}, Embedding: openai_small (text-embedding-3-small)")
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Generate unique document ID
        doc_id = f"doc_{datetime.utcnow().timestamp()}_{current_user['_id']}"
        
        # Save file
        upload_dir = Path(config.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{doc_id}.pdf"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        doc = {
            "_id": doc_id,
            "type": "document",
            "owner_id": current_user["_id"],
            "title": file.filename,
            "file_path": str(file_path),
            "page_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "ingestion_completed": False
        }
        
        couch_client.save_doc(config.documents_db, doc)
        
        # ALWAYS use openai_small (text-embedding-3-small) - no other options
        EMBEDDING_PROVIDER = "openai_small"
        logger.info(f"Using embedding provider: {EMBEDDING_PROVIDER} (text-embedding-3-small)")
        
        # Enqueue ingestion job as background task
        job_id = enqueue_ingestion(
            background_tasks=background_tasks,
            doc_id=doc_id,
            embedding_provider=EMBEDDING_PROVIDER,
            summary_llm_provider=summary_llm_provider,
            summary_llm_model=summary_llm_model
        )
        
        logger.info(f"Document uploaded: {doc_id}, job: {job_id}")
        
        return UploadResponse(
            doc_id=doc_id,
            job_id=job_id,
            message="Document uploaded successfully. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    List all documents for the current user.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        List of documents
    """
    try:
        docs = couch_client.find_documents_by_owner(config.documents_db, current_user["_id"])
        
        documents = []
        for doc in docs:
            documents.append(DocumentResponse(
                id=doc["_id"],
                title=doc["title"],
                page_count=doc.get("page_count"),
                created_at=doc["created_at"],
                ingestion_completed=doc.get("ingestion_completed", False),
                embedding_provider=doc.get("embedding_provider")
            ))
        
        return documents
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


@router.get("/providers")
async def get_providers(current_user: dict = Depends(get_current_user)):
    """
    Get available LLM and embedding providers.
    
    Returns:
        Dictionary with available providers and their models
    """
    try:
        llm_providers = get_available_providers()
        embedding_providers = get_available_embedding_providers()
        
        return {
            "llm_providers": llm_providers,
            "embedding_providers": embedding_providers
        }
        
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get providers"
        )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific document.
    
    Args:
        doc_id: Document ID
        current_user: Current authenticated user
    
    Returns:
        Document details
    """
    try:
        doc = couch_client.get_doc(config.documents_db, doc_id)
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify ownership
        if doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )
        
        return DocumentResponse(
            id=doc["_id"],
            title=doc["title"],
            page_count=doc.get("page_count"),
            created_at=doc["created_at"],
            ingestion_completed=doc.get("ingestion_completed", False),
            embedding_provider=doc.get("embedding_provider")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document"
        )


@router.get("/{doc_id}/pdf")
async def get_document_pdf(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the original PDF file.
    
    Args:
        doc_id: Document ID
        current_user: Current authenticated user
    
    Returns:
        Original PDF file
    """
    try:
        logger.info(f"PDF endpoint called for doc_id: {doc_id}")
        logger.info(f"Using database: {config.documents_db}")
        doc = couch_client.get_doc(config.documents_db, doc_id)
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify ownership
        if doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )
        
        file_path = doc["file_path"]
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file not found"
            )
        
        return FileResponse(
            file_path, 
            media_type="application/pdf",
            filename=f"{doc['title']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF for document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get PDF file"
        )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a document and all associated data.
    
    Args:
        doc_id: Document ID
        current_user: Current authenticated user
    
    Returns:
        Success message with deletion summary
    """
    try:
        doc = couch_client.get_doc(config.documents_db, doc_id)
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify ownership
        if doc["owner_id"] != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this document"
            )
        
        deletion_summary = {
            "document": False,
            "pages": 0,
            "qa_records": 0,
            "vector_chunks": 0,
            "preview_images": 0,
            "pdf_file": False
        }
        
        # 1. Delete all pages and their preview images
        pages = couch_client.find_pages_by_document(config.pages_db, doc_id, offset=0, limit=10000)
        for page in pages:
            page_id = page.get("_id")
            if page_id:
                # Delete preview image if it exists
                preview_path = page.get("preview_image_path")
                if preview_path and os.path.exists(preview_path):
                    try:
                        os.remove(preview_path)
                        deletion_summary["preview_images"] += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete preview image {preview_path}: {e}")
                
                # Delete page document
                if couch_client.delete_doc(config.pages_db, page_id):
                    deletion_summary["pages"] += 1
        
        # Delete preview directory if it exists
        preview_dir = Path(config.preview_dir) / doc_id
        if preview_dir.exists():
            try:
                import shutil
                shutil.rmtree(preview_dir)
                logger.info(f"Deleted preview directory: {preview_dir}")
            except Exception as e:
                logger.warning(f"Failed to delete preview directory {preview_dir}: {e}")
        
        # 2. Delete all QA records
        qa_records = couch_client.find_qa_by_document(config.qa_db, doc_id, limit=10000)
        for qa in qa_records:
            qa_id = qa.get("_id")
            if qa_id and couch_client.delete_doc(config.qa_db, qa_id):
                deletion_summary["qa_records"] += 1
        
        # 3. Delete vector embeddings from the ONLY collection
        from ..vector import vector_client
        try:
            vector_client.delete_document_chunks(vector_client.COLLECTION_OPENAI_SMALL, doc_id)
            deletion_summary["vector_chunks"] = 1
            logger.info(f"Deleted vector chunks from {vector_client.COLLECTION_OPENAI_SMALL}")
        except Exception as e:
            logger.warning(f"Failed to delete chunks for {doc_id}: {e}")
        
        # 4. Delete PDF file
        file_path = doc.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                deletion_summary["pdf_file"] = True
            except Exception as e:
                logger.warning(f"Failed to delete PDF file {file_path}: {e}")
        
        # 5. Delete document record
        if couch_client.delete_doc(config.documents_db, doc_id):
            deletion_summary["document"] = True
        
        logger.info(f"Deleted document {doc_id}: {deletion_summary}")
        
        return {
            "message": "Document and all associated data deleted successfully",
            "deletion_summary": deletion_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

