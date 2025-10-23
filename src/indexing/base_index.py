"""
Base index interface for all index implementations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set
import time


class BaseIndex(ABC):
    """Abstract base class for all index implementations"""
    
    def __init__(self, version: str, index_name: str):
        """
        Initialize base index
        
        Args:
            version: Version string (e.g., "v1.0")
            index_name: Name of the index
        """
        self.version = version
        self.index_name = index_name
        self.doc_count = 0
        self.term_count = 0
        self.metrics = {
            'indexing_time': 0.0,
            'query_times': [],
            'memory_usage': 0,
            'index_size': 0
        }
    
    @abstractmethod
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        """
        Add a document to the index
        
        Args:
            doc_id: Unique document identifier
            text: Document text content
            metadata: Optional document metadata
        """
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search the index with a query
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with scores
        """
        pass
    
    @abstractmethod
    def save(self, path: str):
        """
        Persist index to disk
        
        Args:
            path: Path to save the index
        """
        pass
    
    @abstractmethod
    def load(self, path: str):
        """
        Load index from disk
        
        Args:
            path: Path to load the index from
        """
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Returns:
            Dictionary of metrics
        """
        avg_query_time = sum(self.metrics['query_times']) / len(self.metrics['query_times']) if self.metrics['query_times'] else 0
        p95_query_time = sorted(self.metrics['query_times'])[int(0.95 * len(self.metrics['query_times']))] if len(self.metrics['query_times']) > 0 else 0
        p99_query_time = sorted(self.metrics['query_times'])[int(0.99 * len(self.metrics['query_times']))] if len(self.metrics['query_times']) > 0 else 0
        
        return {
            'version': self.version,
            'index_name': self.index_name,
            'doc_count': self.doc_count,
            'term_count': self.term_count,
            'indexing_time': self.metrics['indexing_time'],
            'avg_query_time': avg_query_time,
            'p95_query_time': p95_query_time,
            'p99_query_time': p99_query_time,
            'memory_usage_mb': self.metrics['memory_usage'] / (1024 * 1024),
            'index_size_mb': self.metrics['index_size'] / (1024 * 1024)
        }
    
    def _record_query_time(self, query_time: float):
        """Record query execution time"""
        self.metrics['query_times'].append(query_time)
