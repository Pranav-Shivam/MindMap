"""
Background task system using FastAPI BackgroundTasks (no Redis/RQ needed).
"""
from typing import Dict
from datetime import datetime
from loguru import logger
from .ingestion import ingest_document


# In-memory job tracking
_jobs: Dict[str, Dict] = {}


def get_job_status(job_id: str) -> dict:
    """
    Get status of a background job.
    
    Args:
        job_id: Job ID
    
    Returns:
        Dict with job status information
    """
    job = _jobs.get(job_id, {})
    return {
        "id": job_id,
        "status": job.get("status", "unknown"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
    }


async def run_ingestion_task(
    job_id: str,
    doc_id: str,
    embedding_provider: str = "openai_small",
    summary_llm_provider: str = "gpt",
    summary_llm_model: str = "gpt-4o-mini"
):
    """
    Run ingestion task in background.
    
    Args:
        job_id: Unique job ID
        doc_id: Document ID
        embedding_provider: Embedding provider
        summary_llm_provider: LLM provider for summaries
        summary_llm_model: LLM model for summaries
    """
    _jobs[job_id] = {
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": datetime.utcnow().isoformat(),
    }
    
    try:
        logger.info(f"Starting background ingestion task {job_id} for document {doc_id}")
        await ingest_document(
            doc_id=doc_id,
            embedding_provider=embedding_provider,
            summary_llm_provider=summary_llm_provider,
            summary_llm_model=summary_llm_model
        )
        
        _jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
        })
        logger.info(f"Background ingestion task {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Background ingestion task {job_id} failed: {e}")
        _jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        })


def enqueue_ingestion(
    background_tasks,
    doc_id: str,
    embedding_provider: str = "openai_small",
    summary_llm_provider: str = "gpt",
    summary_llm_model: str = "gpt-4o-mini"
) -> str:
    """
    Enqueue a document ingestion job as a background task.
    
    Args:
        background_tasks: FastAPI BackgroundTasks instance
        doc_id: Document ID
        embedding_provider: Embedding provider
        summary_llm_provider: LLM provider for summaries
        summary_llm_model: LLM model for summaries
    
    Returns:
        Job ID string
    """
    import uuid
    job_id = str(uuid.uuid4())
    
    # Add task to FastAPI background tasks
    background_tasks.add_task(
        run_ingestion_task,
        job_id=job_id,
        doc_id=doc_id,
        embedding_provider=embedding_provider,
        summary_llm_provider=summary_llm_provider,
        summary_llm_model=summary_llm_model
    )
    
    logger.info(f"Enqueued ingestion job {job_id} for document {doc_id}")
    return job_id

