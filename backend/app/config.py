"""
Configuration module using dataclasses and os.getenv.
Per user preference: dataclasses instead of Pydantic BaseSettings.
"""
import os
from dataclasses import dataclass
from typing import Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration using environment variables."""
    
    # CouchDB
    couchdb_url: str
    couchdb_user: str
    couchdb_password: str
    
    # Database Names
    users_db: str
    documents_db: str
    pages_db: str
    qa_db: str
    annotations_db: str
    
    # ChromaDB
    chroma_persist_directory: str
    
    # LLM Provider API Keys
    openai_api_key: Optional[str]
    anthropic_api_key: Optional[str]
    google_api_key: Optional[str]
    ollama_base_url: str
    
    # Feature Flags
    use_reranker: bool
    allow_deck_scope: bool
    allow_local_ollama: bool
    
    # App Settings
    jwt_secret: str
    upload_dir: str
    preview_dir: str
    
    # Defaults
    default_llm_provider: str
    # Embedding is LOCKED to openai_small (text-embedding-3-small) - no other options

    # Ingestion
    ingestion_concurrency: int
    page_batch_size: int
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        
        # CouchDB
        couchdb_url = os.getenv("COUCHDB_URL", "http://localhost:5984")
        couchdb_user = os.getenv("COUCHDB_USER", "root")
        couchdb_password = os.getenv("COUCHDB_PASSWORD", "root")
        
        # Database Names
        users_db = os.getenv("USERS_DB", "mp_users")
        documents_db = os.getenv("DOCUMENTS_DB", "mp_documents")
        pages_db = os.getenv("PAGES_DB", "mp_pages")
        qa_db = os.getenv("QA_DB", "mp_qa")
        annotations_db = os.getenv("ANNOTATIONS_DB", "mp_annotations")
        
        # ChromaDB
        chroma_persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        # LLM Providers
        openai_api_key = os.getenv("OPENAI_API_KEY")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Feature Flags
        use_reranker = os.getenv("USE_RERANKER", "false").lower() == "true"
        allow_deck_scope = os.getenv("ALLOW_DECK_SCOPE", "true").lower() == "true"
        allow_local_ollama = os.getenv("ALLOW_LOCAL_OLLAMA", "true").lower() == "true"
        
        # App Settings
        jwt_secret = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        preview_dir = os.getenv("PREVIEW_DIR", "./previews")
        
        # Defaults
        default_llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "gpt")
        # Embedding is LOCKED to openai_small - ignore any env var

        # Ingestion
        ingestion_concurrency = int(os.getenv("INGESTION_CONCURRENCY", "4"))
        page_batch_size = int(os.getenv("PAGE_BATCH_SIZE", "10"))
        
        # Create directories if they don't exist
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(preview_dir, exist_ok=True)
        
        # Log warnings for missing API keys
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not set - OpenAI provider will be disabled")
        if not anthropic_api_key:
            logger.warning("ANTHROPIC_API_KEY not set - Claude provider will be disabled")
        if not google_api_key:
            logger.warning("GOOGLE_API_KEY not set - Gemini provider will be disabled")
        
        return cls(
            couchdb_url=couchdb_url,
            couchdb_user=couchdb_user,
            couchdb_password=couchdb_password,
            users_db=users_db,
            documents_db=documents_db,
            pages_db=pages_db,
            qa_db=qa_db,
            annotations_db=annotations_db,
            chroma_persist_directory=chroma_persist_directory,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            google_api_key=google_api_key,
            ollama_base_url=ollama_base_url,
            use_reranker=use_reranker,
            allow_deck_scope=allow_deck_scope,
            allow_local_ollama=allow_local_ollama,
            jwt_secret=jwt_secret,
            upload_dir=upload_dir,
            preview_dir=preview_dir,
            default_llm_provider=default_llm_provider,
            ingestion_concurrency=ingestion_concurrency,
            page_batch_size=page_batch_size,
        )


# Global config instance
config = Config.from_env()


# Configure Loguru
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)

