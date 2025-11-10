"""
Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from .config import config
from .db.setup import setup_databases
from .vector import initialize_collections


# Create FastAPI app
app = FastAPI(
    title="PDF Study App",
    description="Page-scoped PDF study application with AI-powered Q&A",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize databases and services on startup."""
    logger.info("Starting PDF Study App...")
    
    try:
        # Setup databases
        setup_databases()
        
        # Initialize vector collections
        initialize_collections()
        
        logger.info("Application startup complete!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PDF Study App API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/readyz")
async def readiness_check():
    """Readiness check - verifies all services are available."""
    from .db import couch_client
    from .vector import vector_client
    
    checks = {
        "couchdb": False,
        "chromadb": False,
    }
    
    # Check CouchDB
    try:
        _ = couch_client.server.version()
        checks["couchdb"] = True
    except:
        pass
    
    # Check ChromaDB
    try:
        _ = vector_client.client.heartbeat()
        checks["chromadb"] = True
    except:
        pass
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "services": checks
    }


# Include API routers
from .api import auth, documents, pages, qa, search

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(pages.router)
app.include_router(qa.router)
app.include_router(search.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

