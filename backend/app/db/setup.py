"""
Database setup and initialization.
Creates databases using simple direct queries (no design documents).
"""
from loguru import logger
from .client import couch_client
from ..config import config


def setup_databases():
    """Initialize all databases - simple approach without design documents."""
    
    logger.info("Setting up CouchDB databases...")
    
    # Create databases
    couch_client.get_or_create_db(config.users_db)
    couch_client.get_or_create_db(config.documents_db)
    couch_client.get_or_create_db(config.pages_db)
    couch_client.get_or_create_db(config.qa_db)
    couch_client.get_or_create_db(config.annotations_db)
    
    logger.info("Database setup complete!")




if __name__ == "__main__":
    setup_databases()

