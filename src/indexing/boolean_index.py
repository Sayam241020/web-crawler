"""
Boolean inverted index implementation with document IDs and position IDs
"""
import pickle
import time
import sys
from typing import List, Dict, Any, Set
from collections import defaultdict
from ..preprocessing.text_processor import TextProcessor
from .base_index import BaseIndex


class BooleanIndex(BaseIndex):
    """Boolean inverted index with document IDs and position information"""
    
    def __init__(self, version: str = "v1.0", index_name: str = "boolean_index", 
                 use_stemming: bool = True, use_stopwords: bool = True):
        """
        Initialize boolean index
        
        Args:
            version: Version string
            index_name: Name of the index
            use_stemming: Whether to use stemming
            use_stopwords: Whether to remove stopwords
        """
        super().__init__(version, index_name)
        self.text_processor = TextProcessor(use_stemming, use_stopwords)
        # Inverted index: term -> {doc_id: [positions]}
        self.inverted_index: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        # Document store: doc_id -> {text, metadata}
        self.documents: Dict[str, Dict[str, Any]] = {}
        # Document lengths for normalization
        self.doc_lengths: Dict[str, int] = {}
    
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
        self.documents[doc_id] = {
            'text': text,
            'metadata': metadata or {}
        }
        
        # Tokenize and process text
        tokens = self.text_processor.preprocess(text)
        self.doc_lengths[doc_id] = len(tokens)
        
        # Build inverted index with positions
        for position, term in enumerate(tokens):
            self.inverted_index[term][doc_id].append(position)
            
        self.doc_count += 1
        self.term_count = len(self.inverted_index)
        
        # Update indexing time
        self.metrics['indexing_time'] += (time.time() - start_time)
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search using boolean retrieval
        
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
            if term in self.inverted_index:
                term_docs = set(self.inverted_index[term].keys())
                if result_docs is None:
                    result_docs = term_docs
                else:
                    result_docs &= term_docs
            else:
                # Term not in index, no results
                result_docs = set()
                break
        
        if not result_docs:
            self._record_query_time(time.time() - start_time)
            return []
        
        # Prepare results
        results = []
        for doc_id in list(result_docs)[:top_k]:
            results.append({
                'doc_id': doc_id,
                'text': self.documents[doc_id]['text'],
                'metadata': self.documents[doc_id]['metadata'],
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
        for term in phrase_terms:
            if term in self.inverted_index:
                term_docs = set(self.inverted_index[term].keys())
                if candidate_docs is None:
                    candidate_docs = term_docs
                else:
                    candidate_docs &= term_docs
            else:
                self._record_query_time(time.time() - start_time)
                return []
        
        # Check for exact phrase matches using positions
        results = []
        for doc_id in candidate_docs:
            # Get positions of first term
            first_term_positions = self.inverted_index[phrase_terms[0]][doc_id]
            
            # Check if subsequent terms appear at consecutive positions
            for start_pos in first_term_positions:
                is_phrase_match = True
                for i, term in enumerate(phrase_terms[1:], start=1):
                    expected_pos = start_pos + i
                    if expected_pos not in self.inverted_index[term][doc_id]:
                        is_phrase_match = False
                        break
                
                if is_phrase_match:
                    results.append({
                        'doc_id': doc_id,
                        'text': self.documents[doc_id]['text'],
                        'metadata': self.documents[doc_id]['metadata'],
                        'score': 1.0,
                        'phrase_position': start_pos
                    })
                    break  # Found phrase in this document
        
        self._record_query_time(time.time() - start_time)
        return results
    
    def save(self, path: str):
        """
        Save index to disk using pickle
        
        Args:
            path: Path to save the index
        """
        data = {
            'version': self.version,
            'index_name': self.index_name,
            'inverted_index': dict(self.inverted_index),
            'documents': self.documents,
            'doc_lengths': self.doc_lengths,
            'doc_count': self.doc_count,
            'term_count': self.term_count,
            'metrics': self.metrics
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        # Update index size metric
        self.metrics['index_size'] = sys.getsizeof(pickle.dumps(data))
    
    def load(self, path: str):
        """
        Load index from disk
        
        Args:
            path: Path to load the index from
        """
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.version = data['version']
        self.index_name = data['index_name']
        self.inverted_index = defaultdict(lambda: defaultdict(list), data['inverted_index'])
        self.documents = data['documents']
        self.doc_lengths = data['doc_lengths']
        self.doc_count = data['doc_count']
        self.term_count = data['term_count']
        self.metrics = data['metrics']
    
    def get_posting_list(self, term: str) -> Dict[str, List[int]]:
        """
        Get posting list for a term
        
        Args:
            term: Term to look up
            
        Returns:
            Dictionary mapping doc_id to positions
        """
        processed_term = self.text_processor.preprocess(term)
        if processed_term:
            return dict(self.inverted_index.get(processed_term[0], {}))
        return {}
