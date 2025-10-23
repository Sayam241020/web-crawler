"""
Elasticsearch index wrapper (ESIndex-v1.0)
"""
import time
import sys
from typing import List, Dict, Any
from .base_index import BaseIndex

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    print("Warning: Elasticsearch library not installed. Install with: pip install elasticsearch")


class ElasticsearchIndex(BaseIndex):
    """Elasticsearch index wrapper"""
    
    def __init__(self, version: str = "v1.0", index_name: str = "es_index",
                 host: str = "localhost", port: int = 9200):
        """
        Initialize Elasticsearch index
        
        Args:
            version: Version string
            index_name: Name of the index
            host: Elasticsearch host
            port: Elasticsearch port
        """
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("Elasticsearch library is required. Install with: pip install elasticsearch")
        
        super().__init__(version, index_name)
        
        # Connect to Elasticsearch
        self.es = Elasticsearch([f"http://{host}:{port}"])
        self.es_index_name = index_name.lower().replace(" ", "_")
        
        # Create index if it doesn't exist
        if not self.es.indices.exists(index=self.es_index_name):
            self.es.indices.create(
                index=self.es_index_name,
                body={
                    "mappings": {
                        "properties": {
                            "text": {"type": "text"},
                            "doc_id": {"type": "keyword"},
                            "metadata": {"type": "object"}
                        }
                    }
                }
            )
    
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        """
        Add a document to Elasticsearch
        
        Args:
            doc_id: Unique document identifier
            text: Document text content
            metadata: Optional document metadata
        """
        start_time = time.time()
        
        doc = {
            "doc_id": doc_id,
            "text": text,
            "metadata": metadata or {}
        }
        
        # Index document
        self.es.index(
            index=self.es_index_name,
            id=doc_id,
            body=doc
        )
        
        self.doc_count += 1
        self.metrics['indexing_time'] += (time.time() - start_time)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search using Elasticsearch
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        start_time = time.time()
        
        # Build Elasticsearch query
        es_query = {
            "query": {
                "match": {
                    "text": query
                }
            },
            "size": top_k
        }
        
        # Execute search
        response = self.es.search(
            index=self.es_index_name,
            body=es_query
        )
        
        # Parse results
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            results.append({
                'doc_id': source['doc_id'],
                'text': source['text'],
                'metadata': source['metadata'],
                'score': hit['_score']
            })
        
        self._record_query_time(time.time() - start_time)
        return results
    
    def boolean_search(self, query: str, operator: str = "AND", top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Boolean search with Elasticsearch
        
        Args:
            query: Search query (space-separated terms)
            operator: Boolean operator (AND or OR)
            top_k: Number of results
            
        Returns:
            List of search results
        """
        start_time = time.time()
        
        es_query = {
            "query": {
                "match": {
                    "text": {
                        "query": query,
                        "operator": operator.lower()
                    }
                }
            },
            "size": top_k
        }
        
        response = self.es.search(
            index=self.es_index_name,
            body=es_query
        )
        
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            results.append({
                'doc_id': source['doc_id'],
                'text': source['text'],
                'metadata': source['metadata'],
                'score': hit['_score']
            })
        
        self._record_query_time(time.time() - start_time)
        return results
    
    def phrase_search(self, phrase: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Phrase search with Elasticsearch
        
        Args:
            phrase: Exact phrase to search
            top_k: Number of results
            
        Returns:
            List of search results
        """
        start_time = time.time()
        
        es_query = {
            "query": {
                "match_phrase": {
                    "text": phrase
                }
            },
            "size": top_k
        }
        
        response = self.es.search(
            index=self.es_index_name,
            body=es_query
        )
        
        results = []
        for hit in response['hits']['hits']:
            source = hit['_source']
            results.append({
                'doc_id': source['doc_id'],
                'text': source['text'],
                'metadata': source['metadata'],
                'score': hit['_score']
            })
        
        self._record_query_time(time.time() - start_time)
        return results
    
    def save(self, path: str):
        """
        Elasticsearch indexes are stored on ES server, not locally.
        This method is here for API compatibility.
        
        Args:
            path: Path (not used for ES)
        """
        print(f"Elasticsearch index '{self.es_index_name}' is stored on ES server")
        print(f"To backup, use Elasticsearch snapshot and restore API")
    
    def load(self, path: str):
        """
        Load is not needed for Elasticsearch as data is on server.
        This method is here for API compatibility.
        
        Args:
            path: Path (not used for ES)
        """
        # Check if index exists
        if self.es.indices.exists(index=self.es_index_name):
            # Get document count
            count_response = self.es.count(index=self.es_index_name)
            self.doc_count = count_response['count']
            print(f"Connected to existing ES index '{self.es_index_name}' with {self.doc_count} documents")
        else:
            print(f"ES index '{self.es_index_name}' does not exist")
    
    def delete_index(self):
        """Delete the Elasticsearch index"""
        if self.es.indices.exists(index=self.es_index_name):
            self.es.indices.delete(index=self.es_index_name)
            print(f"Deleted ES index '{self.es_index_name}'")
    
    def refresh(self):
        """Refresh the index to make recent changes searchable"""
        self.es.indices.refresh(index=self.es_index_name)
