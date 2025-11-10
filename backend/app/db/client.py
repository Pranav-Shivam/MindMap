"""
CouchDB client and connection management.
"""
import couchdb
from typing import Optional, Dict, Any, List
from loguru import logger
from ..config import config


class CouchDBClient:
    """CouchDB client wrapper with connection pooling and error handling."""
    
    def __init__(self):
        """Initialize CouchDB connection."""
        self.server = None
        self.databases = {}
        self._connect()
    
    def _connect(self):
        """Establish connection to CouchDB server."""
        try:
            # Parse CouchDB URL to extract credentials if embedded
            url = config.couchdb_url
            
            # Connect with basic auth
            self.server = couchdb.Server(url)
            
            # Try to authenticate if credentials provided separately
            if config.couchdb_user and config.couchdb_password:
                self.server.resource.credentials = (
                    config.couchdb_user,
                    config.couchdb_password
                )
            
            # Test connection
            _ = self.server.version()
            logger.info("Successfully connected to CouchDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to CouchDB: {e}")
            raise
    
    def get_or_create_db(self, db_name: str):
        """Get database or create if it doesn't exist."""
        if db_name in self.databases:
            return self.databases[db_name]
        
        try:
            if db_name in self.server:
                db = self.server[db_name]
                logger.info(f"Using existing database: {db_name}")
            else:
                db = self.server.create(db_name)
                logger.info(f"Created new database: {db_name}")
            
            self.databases[db_name] = db
            return db
            
        except Exception as e:
            logger.error(f"Error getting/creating database {db_name}: {e}")
            raise
    
    def create_design_doc(self, db_name: str, design_doc_id: str, views: Dict[str, Dict[str, str]]):
        """Create or update a design document with views."""
        db = self.get_or_create_db(db_name)
        
        design_doc = {
            "_id": f"_design/{design_doc_id}",
            "views": views
        }
        
        try:
            # Check if design doc already exists
            existing = db.get(design_doc["_id"])
            if existing:
                design_doc["_rev"] = existing["_rev"]
                logger.info(f"Updating existing design document: {design_doc_id} in {db_name}")
            else:
                logger.info(f"Creating new design document: {design_doc_id} in {db_name}")
            
            db.save(design_doc)
            logger.info(f"Successfully created/updated design document: {design_doc_id} in {db_name}")
            
            # Verify the design document was created successfully
            verification = db.get(design_doc["_id"])
            if not verification:
                raise Exception(f"Design document {design_doc_id} was not found after creation")
            
            logger.info(f"Verified design document {design_doc_id} exists in {db_name}")
            
        except Exception as e:
            logger.error(f"Error creating design document {design_doc_id} in {db_name}: {e}")
            raise
    
    def save_doc(self, db_name: str, doc: Dict[str, Any]) -> str:
        """Save a document to the database."""
        db = self.get_or_create_db(db_name)
        
        try:
            doc_id, doc_rev = db.save(doc)
            return doc_id
        except Exception as e:
            logger.error(f"Error saving document to {db_name}: {e}")
            raise
    
    def get_doc(self, db_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        db = self.get_or_create_db(db_name)
        
        try:
            return db.get(doc_id)
        except Exception as e:
            logger.error(f"Error getting document {doc_id} from {db_name}: {e}")
            return None
    
    def update_doc(self, db_name: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document with new fields."""
        db = self.get_or_create_db(db_name)
        
        try:
            doc = db.get(doc_id)
            if not doc:
                return False
            
            doc.update(updates)
            db.save(doc)
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id} in {db_name}: {e}")
            return False
    
    def delete_doc(self, db_name: str, doc_id: str) -> bool:
        """Delete a document."""
        db = self.get_or_create_db(db_name)
        
        try:
            doc = db.get(doc_id)
            if doc:
                db.delete(doc)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id} from {db_name}: {e}")
            return False
    
    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email address using simple document iteration."""
        db = self.get_or_create_db(config.users_db)
        
        try:
            # Iterate through all documents to find user by email
            for doc_id in db:
                if doc_id.startswith('_design'):
                    continue
                    
                doc = db.get(doc_id)
                if doc and doc.get('type') == 'user' and doc.get('email') == email:
                    return doc
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None
    
    def find_documents_by_owner(self, db_name: str, owner_id: str) -> List[Dict[str, Any]]:
        """Find all documents by owner_id using simple iteration."""
        db = self.get_or_create_db(db_name)
        results = []
        
        try:
            for doc_id in db:
                if doc_id.startswith('_design'):
                    continue
                    
                doc = db.get(doc_id)
                if doc and doc.get('type') == 'document' and doc.get('owner_id') == owner_id:
                    results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding documents by owner in {db_name}: {e}")
            return []
    
    def find_pages_by_document(self, db_name: str, document_id: str, offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Find all pages for a document using simple iteration."""
        db = self.get_or_create_db(db_name)
        results = []
        
        try:
            for doc_id in db:
                if doc_id.startswith('_design'):
                    continue
                    
                doc = db.get(doc_id)
                if doc and doc.get('type') == 'page' and doc.get('document_id') == document_id:
                    results.append(doc)
            
            # Sort by page_no and apply pagination
            results.sort(key=lambda x: x.get('page_no', 0))
            return results[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Error finding pages by document in {db_name}: {e}")
            return []
    
    def find_qa_by_document(self, db_name: str, document_id: str, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Find all Q&A for a document using simple iteration."""
        db = self.get_or_create_db(db_name)
        results = []
        
        try:
            for doc_id in db:
                if doc_id.startswith('_design'):
                    continue
                    
                doc = db.get(doc_id)
                if doc and doc.get('type') == 'qa' and doc.get('document_id') == document_id:
                    results.append(doc)
            
            # Sort by created_at descending and apply offset + limit
            results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return results[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Error finding Q&A by document in {db_name}: {e}")
            return []
    
    def find_all_qa(self, db_name: str) -> List[Dict[str, Any]]:
        """Find all Q&A documents using simple iteration."""
        db = self.get_or_create_db(db_name)
        results = []
        
        try:
            for doc_id in db:
                if doc_id.startswith('_design'):
                    continue
                    
                doc = db.get(doc_id)
                if doc and doc.get('type') == 'qa':
                    results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding all Q&A in {db_name}: {e}")
            return []
    
    def find_qa_by_page(self, db_name: str, document_id: str, page_no: int) -> List[Dict[str, Any]]:
        """Find all Q&A for a specific page using simple iteration."""
        db = self.get_or_create_db(db_name)
        results = []
        
        try:
            for doc_id in db:
                if doc_id.startswith('_design'):
                    continue
                    
                doc = db.get(doc_id)
                if (doc and doc.get('type') == 'qa' and 
                    doc.get('document_id') == document_id and 
                    doc.get('page_no') == page_no):
                    results.append(doc)
            
            # Sort by created_at descending
            results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error finding Q&A by page in {db_name}: {e}")
            return []
    
    def query_view(
        self,
        db_name: str,
        design_doc: str,
        view_name: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Query a view and return results."""
        db = self.get_or_create_db(db_name)
        
        try:
            view_path = f"{design_doc}/{view_name}"
            results = db.view(view_path, **kwargs)
            return [{"id": row.id, "key": row.key, "value": row.value, "doc": getattr(row, 'doc', None)} 
                    for row in results]
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error querying view {view_path} in {db_name}: {e}")
            
            # Check if this is a missing design document error
            if "not_found" in error_msg and "Document is missing attachment" in error_msg:
                logger.warning(f"Design document {design_doc} appears to be missing in {db_name}. "
                             f"This may indicate the database setup was not completed properly.")
                logger.info(f"Consider running the database setup to recreate missing design documents.")
            
            return []


# Global client instance
couch_client = CouchDBClient()

