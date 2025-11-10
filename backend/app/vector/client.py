"""
ChromaDB vector database client for semantic search.
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
from ..config import config


class VectorDBClient:
    """ChromaDB client wrapper for vector operations."""
    
    # ONLY ONE COLLECTION - text-embedding-3-small (1536 dims)
    COLLECTION_OPENAI_SMALL = "chunks_openai_small"  # 1536 dims - ONLY EMBEDDING MODEL
    
    def __init__(self):
        """Initialize ChromaDB client."""
        self.client = None
        self.collections = {}
        self._connect()
    
    def _connect(self):
        """Establish connection to ChromaDB."""
        try:
            # Use persistent client with local storage
            self.client = chromadb.PersistentClient(
                path=config.chroma_persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"Successfully connected to ChromaDB at {config.chroma_persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
    
    def create_collection_if_not_exists(self, collection_name: str, vector_size: int):
        """Create a collection if it doesn't exist."""
        try:
            # Try to get existing collection
            try:
                collection = self.client.get_collection(name=collection_name)
                self.collections[collection_name] = collection
                logger.info(f"Collection already exists: {collection_name}")
            except:
                # Create new collection
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine", "dimension": vector_size}
                )
                self.collections[collection_name] = collection
                logger.info(f"Created collection: {collection_name} (size: {vector_size})")
                
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise
    
    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """
        Upsert chunks with their embeddings.
        
        Args:
            collection_name: Target collection
            chunks: List of chunk metadata dicts with keys: doc_id, page_no, chunk_index, text
            embeddings: List of embedding vectors
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                collection = self.client.get_collection(name=collection_name)
                self.collections[collection_name] = collection
            
            ids = []
            metadatas = []
            documents = []
            
            for chunk, embedding in zip(chunks, embeddings):
                point_id = f"{chunk['doc_id']}_{chunk['page_no']}_{chunk['chunk_index']}"
                ids.append(point_id)
                
                metadatas.append({
                    "doc_id": chunk["doc_id"],
                    "page_no": chunk["page_no"],
                    "chunk_index": chunk["chunk_index"],
                    "token_count": chunk.get("metadata", {}).get("token_count", 0)
                })
                
                documents.append(chunk["text"])
            
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            
            logger.info(f"Upserted {len(ids)} chunks to {collection_name}")
            
        except Exception as e:
            logger.error(f"Error upserting chunks to {collection_name}: {e}")
            raise
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 6,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Number of results to return
            filter_conditions: Optional filters (e.g., {"doc_id": "...", "page_no": 1})
        
        Returns:
            List of search results with score, id, and payload
        """
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                collection = self.client.get_collection(name=collection_name)
                self.collections[collection_name] = collection
            
            # Build where filter if conditions provided
            where_filter = None
            if filter_conditions:
                logger.debug(f"Building filter for conditions: {filter_conditions}")
                if len(filter_conditions) == 1:
                    # Single condition
                    key, value = next(iter(filter_conditions.items()))
                    where_filter = {key: {"$eq": value}}
                else:
                    # Multiple conditions with AND
                    where_filter = {
                        "$and": [
                            {key: {"$eq": value}} 
                            for key, value in filter_conditions.items()
                        ]
                    }
                logger.debug(f"Built where filter: {where_filter}")
            
            # Perform search
            logger.debug(f"Querying collection {collection_name} with limit={limit}, where={where_filter}")
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )
            
            logger.debug(f"Raw query results: {len(results.get('ids', [[]])[0]) if results.get('ids') else 0} results")
            
            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    try:
                        metadata = results['metadatas'][0][i]
                        formatted_results.append({
                            "id": results['ids'][0][i],
                            "score": 1.0 - results['distances'][0][i],  # Convert distance to similarity
                            "doc_id": metadata["doc_id"],
                            "page_no": metadata["page_no"],
                            "chunk_index": metadata["chunk_index"],
                            "text": results['documents'][0][i],
                            "metadata": {"token_count": metadata.get("token_count", 0)}
                        })
                    except Exception as e:
                        logger.error(f"Error formatting result {i}: {e}, metadata: {results['metadatas'][0][i] if results.get('metadatas') else 'N/A'}")
                        continue
            
            logger.debug(f"Formatted {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching {collection_name}: {e}", exc_info=True)
            return []
    
    def delete_document_chunks(self, collection_name: str, doc_id: str):
        """Delete all chunks for a document."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                try:
                    collection = self.client.get_collection(name=collection_name)
                    self.collections[collection_name] = collection
                except Exception:
                    # Collection doesn't exist, nothing to delete
                    logger.debug(f"Collection {collection_name} doesn't exist, skipping deletion")
                    return
            
            # ChromaDB delete by where filter
            # First, get all IDs for this document
            results = collection.get(
                where={"doc_id": doc_id},
                include=["metadatas"]
            )
            
            if results and results.get("ids") and len(results["ids"]) > 0:
                # Delete by IDs
                collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {doc_id} from {collection_name}")
            else:
                logger.debug(f"No chunks found for document {doc_id} in {collection_name}")
            
        except Exception as e:
            logger.error(f"Error deleting chunks for {doc_id} from {collection_name}: {e}")
            # Don't raise - allow deletion to continue even if vector deletion fails
    
    def get_collection_for_provider(self, provider: str = "openai_small") -> str:
        """Get collection name - ALWAYS returns openai_small collection (text-embedding-3-small)."""
        # Ignore provider parameter - we only use openai_small
        return self.COLLECTION_OPENAI_SMALL
    
    def get_vector_size_for_provider(self, provider: str = "openai_small") -> int:
        """Get vector dimension - ALWAYS returns 1536 (text-embedding-3-small)."""
        # Ignore provider parameter - we only use 1536-dim embeddings
        return 1536


# Global client instance
vector_client = VectorDBClient()


def initialize_collections():
    """Initialize the ONLY vector collection (text-embedding-3-small)."""
    vector_client.create_collection_if_not_exists(
        VectorDBClient.COLLECTION_OPENAI_SMALL, 1536
    )
    logger.info("Vector collection initialized: chunks_openai_small (text-embedding-3-small)")

