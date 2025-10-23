"""
RocksDB-backed inverted index implementation
"""
import json
import time
import sys
from typing import List, Dict, Any, Set
from collections import defaultdict
try:
    import rocksdb
    ROCKSDB_AVAILABLE = True
except ImportError:
    ROCKSDB_AVAILABLE = False
from ..preprocessing.text_processor import TextProcessor
from .base_index import BaseIndex


class RocksDBIndex(BaseIndex):
    """Inverted index backed by RocksDB for persistent storage"""
    
    def __init__(self, version: str = "v1.0", index_name: str = "rocksdb_index",
                 use_stemming: bool = True, use_stopwords: bool = True,
                 db_path: str = None):
        """
        Initialize RocksDB index
        
        Args:
            version: Version string
            index_name: Name of the index
            use_stemming: Whether to use stemming
            use_stopwords: Whether to remove stopwords
            db_path: Path to RocksDB database directory
        """
        if not ROCKSDB_AVAILABLE:
            raise ImportError("RocksDB is not available. Install with: pip install python-rocksdb")
        
        super().__init__(version, index_name)
        self.text_processor = TextProcessor(use_stemming, use_stopwords)
        
        # RocksDB setup
        self.db_path = db_path or f"./rocksdb_data/{index_name}"
        opts = rocksdb.Options()
        opts.create_if_missing = True
        opts.max_open_files = 300000
        opts.write_buffer_size = 67108864
        opts.max_write_buffer_number = 3
        opts.target_file_size_base = 67108864
        
        self.db = rocksdb.DB(self.db_path, opts)
        
        # Load metadata
        self._load_metadata()
    
    def _load_metadata(self):
        """Load index metadata from RocksDB"""
        metadata_bytes = self.db.get(b'__metadata__')
        if metadata_bytes:
            metadata = json.loads(metadata_bytes.decode('utf-8'))
            self.doc_count = metadata.get('doc_count', 0)
            self.term_count = metadata.get('term_count', 0)
        else:
            self.doc_count = 0
            self.term_count = 0
    
    def _save_metadata(self):
        """Save index metadata to RocksDB"""
        metadata = {
            'doc_count': self.doc_count,
            'term_count': self.term_count,
            'version': self.version,
            'index_name': self.index_name
        }
        self.db.put(b'__metadata__', json.dumps(metadata).encode('utf-8'))
    
    def _get_key(self, prefix: str, key: str) -> bytes:
        """Generate a key with prefix"""
        return f"{prefix}:{key}".encode('utf-8')
    
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        """
        Add a document to the index
        
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
        self.db.put(self._get_key('doc', doc_id), json.dumps(doc_data).encode('utf-8'))
        
        # Tokenize and process text
        tokens = self.text_processor.preprocess(text)
        
        # Store document length
        self.db.put(self._get_key('doclen', doc_id), str(len(tokens)).encode('utf-8'))
        
        # Build inverted index with positions and term frequency
        term_positions = defaultdict(list)
        for position, term in enumerate(tokens):
            term_positions[term].append(position)
        
        # Store inverted index entries
        batch = rocksdb.WriteBatch()
        for term, positions in term_positions.items():
            # Get existing posting list
            posting_key = self._get_key('term', term)
            existing_bytes = self.db.get(posting_key)
            
            if existing_bytes:
                posting_list = json.loads(existing_bytes.decode('utf-8'))
            else:
                posting_list = {}
            
            # Add this document to posting list
            posting_list[doc_id] = {
                'tf': len(positions),
                'positions': positions
            }
            
            # Update posting list
            batch.put(posting_key, json.dumps(posting_list).encode('utf-8'))
        
        # Write batch
        self.db.write(batch)
        
        self.doc_count += 1
        
        # Update term count
        it = self.db.iterkeys()
        it.seek(b'term:')
        term_count = 0
        for key in it:
            if not key.startswith(b'term:'):
                break
            term_count += 1
        self.term_count = term_count
        
        # Save metadata
        self._save_metadata()
        
        # Update indexing time
        self.metrics['indexing_time'] += (time.time() - start_time)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search using TF-IDF ranking
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of ranked documents
        """
        start_time = time.time()
        
        # Process query
        query_terms = self.text_processor.preprocess(query)
        
        if not query_terms:
            return []
        
        # Calculate scores for documents
        doc_scores = defaultdict(float)
        
        for term in query_terms:
            posting_key = self._get_key('term', term)
            posting_bytes = self.db.get(posting_key)
            
            if posting_bytes:
                posting_list = json.loads(posting_bytes.decode('utf-8'))
                
                # Calculate IDF
                df = len(posting_list)
                idf = 0
                if df > 0 and self.doc_count > 0:
                    import math
                    idf = math.log(self.doc_count / df)
                
                # Calculate TF-IDF for each document
                for doc_id, doc_info in posting_list.items():
                    tf = doc_info['tf']
                    
                    # Get document length
                    doclen_bytes = self.db.get(self._get_key('doclen', doc_id))
                    doc_length = int(doclen_bytes.decode('utf-8')) if doclen_bytes else 1
                    
                    # Calculate normalized TF-IDF
                    normalized_tf = tf / doc_length if doc_length > 0 else 0
                    tfidf_score = normalized_tf * idf
                    doc_scores[doc_id] += tfidf_score
        
        # Sort by score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Format results
        results = []
        for doc_id, score in sorted_docs:
            doc_bytes = self.db.get(self._get_key('doc', doc_id))
            if doc_bytes:
                doc_data = json.loads(doc_bytes.decode('utf-8'))
                results.append({
                    'doc_id': doc_id,
                    'score': score,
                    'text': doc_data['text'],
                    'metadata': doc_data['metadata']
                })
        
        # Record query time
        query_time = time.time() - start_time
        self._record_query_time(query_time)
        
        return results
    
    def save(self, path: str):
        """
        Save is handled automatically by RocksDB
        
        Args:
            path: Not used, kept for interface compatibility
        """
        # Save final metadata
        self._save_metadata()
        # RocksDB handles persistence automatically
        print(f"RocksDB index data is stored in: {self.db_path}")
    
    def load(self, path: str):
        """
        Load is handled automatically by RocksDB on init
        
        Args:
            path: Not used, kept for interface compatibility
        """
        # Data is automatically loaded on initialization
        self._load_metadata()
        print(f"RocksDB index loaded from: {self.db_path}")
    
    def close(self):
        """Close the RocksDB connection"""
        if hasattr(self, 'db') and self.db:
            del self.db
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
