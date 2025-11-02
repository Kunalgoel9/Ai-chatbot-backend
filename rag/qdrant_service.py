from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from django.conf import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Service to interact with Qdrant vector database
    """
    
    def __init__(self):
        # Initialize Qdrant client
        if settings.QDRANT_URL and settings.QDRANT_API_KEY:
            # Cloud setup
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
            logger.info("Connected to Qdrant Cloud")
        else:
            # Local setup
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )
            logger.info(f"Connected to local Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        
        # Initialize embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_size = 384  # Dimension for all-MiniLM-L6-v2
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    def generate_embedding(self, text: str) -> list:
        """
        Generate embedding vector for text
        """
        try:
            # Truncate text if too long (model limit is ~512 tokens)
            text = text[:5000]
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def add_document(self, page_id: int, url: str, title: str, content: str) -> str:
        """
        Add a document to Qdrant
        Returns: vector_id (UUID)
        """
        try:
            # Generate embedding from FULL content
            embedding = self.generate_embedding(content)
            
            # Generate unique ID
            vector_id = str(uuid.uuid4())
            
            # Create point with MORE content stored
            point = PointStruct(
                id=vector_id,
                vector=embedding,
                payload={
                    'page_id': page_id,
                    'url': url,
                    'title': title,
                    'content': content[:2000],  # Store more content (2k chars)
                    'content_length': len(content)
                }
            )
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Added document to Qdrant: {title} ({len(content)} chars)")
            return vector_id
            
        except Exception as e:
            logger.error(f"Error adding document to Qdrant: {e}")
            raise
    
    def search(self, query: str, limit: int = 5):
        """
        Search for similar documents
        Returns: list of search results with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search in Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'page_id': result.payload.get('page_id'),
                    'url': result.payload.get('url'),
                    'title': result.payload.get('title'),
                    'content': result.payload.get('content'),
                    'score': result.score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []
    
    def delete_by_page_id(self, page_id: int):
        """Delete vectors by page_id"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "page_id",
                                "match": {"value": page_id}
                            }
                        ]
                    }
                }
            )
            logger.info(f"Deleted vectors for page_id: {page_id}")
        except Exception as e:
            logger.error(f"Error deleting from Qdrant: {e}")