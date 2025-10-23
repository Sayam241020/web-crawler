"""
Redis-based inverted index implementation
Uses Redis as a datastore for distributed/persistent indexing
"""
import pickle
import time
import sys
import json
from typing import List, Dict, Any, Set, Optional
from collections import defaultdict
from ..preprocessing.text_processor import TextProcessor
from .base_index import BaseIndex

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisIndex(BaseIndex):
    """Redis-based inverted index with document IDs and position information"""
    
    def __init__(self, version: str = "v1.0", index_name: str = "redis_index", 
                 use_stemming: bool = True, use_stopwords: bool = True,
                 redis_host: str = "localhost", redis_port: int = 6379,
                 redis_db: int = 0, redis_password: Optional[str] = None):
        """
        Initialize Redis index
        
        Args:
            version: Version string
            index_name: Name of the index
            use_stemming: Whether to use stemming
            use_stopwords: Whether to remove stopwords
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            redis_password: Redis password (if required)
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis package not installed. Install with: pip install redis")
        
        super().__init__(version, index_name)
        self.text_processor = TextProcessor(use_stemming, use_stopwords)
        
        # Connect to Redis
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=False  # We'll handle encoding/decoding ourselves
        )
        
        # Test connection
        try:
            self.redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis at {redis_host}:{redis_port}. "
                                f"Make sure Redis is running. Error: {e}")
        
        # Key prefixes for different data types
        self.prefix = f"{index_name}:"
        self.inverted_index_prefix = f"{self.prefix}inv:"
        self.doc_prefix = f"{self.prefix}doc:"
        self.doc_length_prefix = f"{self.prefix}len:"
        self.metadata_key = f"{self.prefix}metadata"
        
        # Load or initialize metadata
        self._load_metadata()
    
    def _load_metadata(self):
        """Load index metadata from Redis"""
        metadata = self.redis_client.get(self.metadata_key)
        if metadata:
            data = json.loads(metadata)
            self.doc_count = data.get('doc_count', 0)
            self.term_count = data.get('term_count', 0)
            self.version = data.get('version', self.version)
    
    def _save_metadata(self):
        """Save index metadata to Redis"""
        metadata = {
            'doc_count': self.doc_count,
            'term_count': self.term_count,
            'version': self.version,
            'index_name': self.index_name
        }
        self.redis_client.set(self.metadata_key, json.dumps(metadata))
    
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        """
        Add a document to the Redis index
        
        Args:
            doc_id: Unique document identifier
            text: Document text content
            metadata: Optional document metadata
        """
        start_time = time.time()
        
        # Store document
        doc_data = {
            'text': text,
            'metadata': metadata or {}
        }
        self.redis_client.set(f"{self.doc_prefix}{doc_id}", json.dumps(doc_data))
        
        # Tokenize and process text
        tokens = self.text_processor.preprocess(text)
        doc_length = len(tokens)
        
        # Store document length
        self.redis_client.set(f"{self.doc_length_prefix}{doc_id}", doc_length)
        
        # Build inverted index with positions
        term_doc_positions = defaultdict(list)
        for position, term in enumerate(tokens):
            term_doc_positions[term].append(position)
        
        # Store inverted index entries in Redis
        for term, positions in term_doc_positions.items():
            # Store positions as a JSON list in a hash
            term_key = f"{self.inverted_index_prefix}{term}"
            self.redis_client.hset(term_key, doc_id, json.dumps(positions))
        
        self.doc_count += 1
        
        # Update term count (this is expensive, so we do it periodically)
        # Get all inverted index keys to count unique terms
        self.term_count = len(self.redis_client.keys(f"{self.inverted_index_prefix}*"))
        
        # Save metadata
        self._save_metadata()
        
        # Update indexing time
        self.metrics['indexing_time'] += (time.time() - start_time)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search using boolean retrieval with Redis backend
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of matching documents
        """
        start_time = time.time()
        
        # Process query terms
        query_terms = self.text_processor.preprocess(query)
        
        if not query_terms:
            return []
        
        # Find documents containing all query terms (AND semantics)
        result_docs = None
        for term in query_terms:
            term_key = f"{self.inverted_index_prefix}{term}"
            # Get all doc_ids for this term
            term_docs = set(self.redis_client.hkeys(term_key))
            term_docs = {doc_id.decode('utf-8') if isinstance(doc_id, bytes) else doc_id 
                        for doc_id in term_docs}
            
            if result_docs is None:
                result_docs = term_docs
            else:
                result_docs &= term_docs
            
            if not result_docs:
                # No intersection, no results
                break
        
        if not result_docs:
            self._record_query_time(time.time() - start_time)
            return []
        
        # Prepare results
        results = []
        for doc_id in list(result_docs)[:top_k]:
            doc_data_json = self.redis_client.get(f"{self.doc_prefix}{doc_id}")
            if doc_data_json:
                doc_data = json.loads(doc_data_json)
                results.append({
                    'doc_id': doc_id,
                    'text': doc_data['text'],
                    'metadata': doc_data['metadata'],
                    'score': 1.0  # Boolean retrieval, all matches have same score
                })
        
        self._record_query_time(time.time() - start_time)
        return results
    
    def phrase_search(self, phrase: str) -> List[Dict[str, Any]]:
        """
        Search for exact phrase matches
        
        Args:
            phrase: Exact phrase to search
            
        Returns:
            List of matching documents
        """
        start_time = time.time()
        
        # Process phrase
        phrase_terms = self.text_processor.preprocess(phrase)
        
        if not phrase_terms:
            return []
        
        # Find documents containing all terms
        candidate_docs = None
        term_positions = {}
        
        for term in phrase_terms:
            term_key = f"{self.inverted_index_prefix}{term}"
            term_docs = set(self.redis_client.hkeys(term_key))
            term_docs = {doc_id.decode('utf-8') if isinstance(doc_id, bytes) else doc_id 
                        for doc_id in term_docs}
            
            if candidate_docs is None:
                candidate_docs = term_docs
            else:
                candidate_docs &= term_docs
            
            if not candidate_docs:
                self._record_query_time(time.time() - start_time)
                return []
            
            # Store positions for later use
            term_positions[term] = {}
            for doc_id in candidate_docs:
                positions_json = self.redis_client.hget(term_key, doc_id)
                if positions_json:
                    term_positions[term][doc_id] = json.loads(positions_json)
        
        # Check for exact phrase matches using positions
        results = []
        for doc_id in candidate_docs:
            # Get positions of first term
            first_term_positions = term_positions[phrase_terms[0]].get(doc_id, [])
            
            # Check if subsequent terms appear at consecutive positions
            for start_pos in first_term_positions:
                is_phrase_match = True
                for i, term in enumerate(phrase_terms[1:], start=1):
                    expected_pos = start_pos + i
                    if expected_pos not in term_positions[term].get(doc_id, []):
                        is_phrase_match = False
                        break
                
                if is_phrase_match:
                    doc_data_json = self.redis_client.get(f"{self.doc_prefix}{doc_id}")
                    if doc_data_json:
                        doc_data = json.loads(doc_data_json)
                        results.append({
                            'doc_id': doc_id,
                            'text': doc_data['text'],
                            'metadata': doc_data['metadata'],
                            'score': 1.0,
                            'phrase_position': start_pos
                        })
                    break  # Found phrase in this document
        
        self._record_query_time(time.time() - start_time)
        return results
    
    def save(self, path: str):
        """
        Save index metadata to disk
        Note: Actual data is in Redis, this just saves metadata
        
        Args:
            path: Path to save the metadata
        """
        metadata = {
            'version': self.version,
            'index_name': self.index_name,
            'doc_count': self.doc_count,
            'term_count': self.term_count,
            'metrics': self.metrics
        }
        
        with open(path, 'wb') as f:
            pickle.dump(metadata, f)
        
        # Also save to Redis
        self._save_metadata()
        
        # Update index size metric (approximate)
        self.metrics['index_size'] = sys.getsizeof(pickle.dumps(metadata))
    
    def load(self, path: str):
        """
        Load index metadata from disk
        Note: Actual data is in Redis
        
        Args:
            path: Path to load the metadata from
        """
        with open(path, 'rb') as f:
            metadata = pickle.load(f)
        
        self.version = metadata['version']
        self.index_name = metadata['index_name']
        self.doc_count = metadata['doc_count']
        self.term_count = metadata['term_count']
        self.metrics = metadata['metrics']
        
        # Also load from Redis
        self._load_metadata()
    
    def clear(self):
        """Clear all index data from Redis"""
        # Delete all keys with our prefix
        keys = self.redis_client.keys(f"{self.prefix}*")
        if keys:
            self.redis_client.delete(*keys)
        
        self.doc_count = 0
        self.term_count = 0
        self._save_metadata()
    
    def get_posting_list(self, term: str) -> Dict[str, List[int]]:
        """
        Get posting list for a term
        
        Args:
            term: Term to look up
            
        Returns:
            Dictionary mapping doc_id to positions
        """
        processed_term = self.text_processor.preprocess(term)
        if not processed_term:
            return {}
        
        term_key = f"{self.inverted_index_prefix}{processed_term[0]}"
        result = {}
        
        # Get all doc_ids and their positions for this term
        term_data = self.redis_client.hgetall(term_key)
        for doc_id, positions_json in term_data.items():
            doc_id = doc_id.decode('utf-8') if isinstance(doc_id, bytes) else doc_id
            result[doc_id] = json.loads(positions_json)
        
        return result
    
    def __del__(self):
        """Close Redis connection when object is destroyed"""
        if hasattr(self, 'redis_client'):
            self.redis_client.close()
