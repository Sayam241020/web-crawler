"""
TF-IDF inverted index implementation
"""
import pickle
import time
import sys
import math
from typing import List, Dict, Any
from collections import defaultdict
from ..preprocessing.text_processor import TextProcessor
from .base_index import BaseIndex


class TFIDFIndex(BaseIndex):
    """Inverted index with TF-IDF scoring"""
    
    def __init__(self, version: str = "v1.0", index_name: str = "tfidf_index",
                 use_stemming: bool = True, use_stopwords: bool = True):
        """
        Initialize TF-IDF index
        
        Args:
            version: Version string
            index_name: Name of the index
            use_stemming: Whether to use stemming
            use_stopwords: Whether to remove stopwords
        """
        super().__init__(version, index_name)
        self.text_processor = TextProcessor(use_stemming, use_stopwords)
        # Inverted index: term -> {doc_id: (tf, [positions])}
        self.inverted_index: Dict[str, Dict[str, tuple]] = defaultdict(lambda: defaultdict(lambda: (0, [])))
        # Document store
        self.documents: Dict[str, Dict[str, Any]] = {}
        # Document lengths
        self.doc_lengths: Dict[str, int] = {}
        # Document frequency: term -> number of documents containing term
        self.doc_freq: Dict[str, int] = defaultdict(int)
        # IDF cache
        self.idf_cache: Dict[str, float] = {}
    
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
        
        # Build inverted index
        term_positions = defaultdict(list)
        for position, term in enumerate(tokens):
            term_positions[term].append(position)
        
        for term, positions in term_positions.items():
            tf = len(positions)
            self.inverted_index[term][doc_id] = (tf, positions)
            self.doc_freq[term] += 1
        
        self.doc_count += 1
        self.term_count = len(self.inverted_index)
        
        # Clear IDF cache as document collection changed
        self.idf_cache.clear()
        
        # Update indexing time
        self.metrics['indexing_time'] += (time.time() - start_time)
    
    def _calculate_idf(self, term: str) -> float:
        """
        Calculate IDF for a term
        
        Args:
            term: Term to calculate IDF for
            
        Returns:
            IDF value
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        if term not in self.doc_freq:
            return 0.0
        
        # IDF = log(N / df)
        idf = math.log(self.doc_count / self.doc_freq[term])
        self.idf_cache[term] = idf
        return idf
    
    def _calculate_tfidf(self, tf: int, doc_length: int, idf: float) -> float:
        """
        Calculate TF-IDF score
        
        Args:
            tf: Term frequency
            doc_length: Document length
            idf: IDF value
            
        Returns:
            TF-IDF score
        """
        # Normalized TF-IDF
        # TF = term_freq / doc_length (normalized)
        # TF-IDF = TF * IDF
        normalized_tf = tf / doc_length if doc_length > 0 else 0
        return normalized_tf * idf
    
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
        
        # Calculate TF-IDF scores for documents
        doc_scores = defaultdict(float)
        
        for term in query_terms:
            if term in self.inverted_index:
                idf = self._calculate_idf(term)
                
                for doc_id, (tf, _) in self.inverted_index[term].items():
                    tfidf_score = self._calculate_tfidf(tf, self.doc_lengths[doc_id], idf)
                    doc_scores[doc_id] += tfidf_score
        
        # Sort by score and get top k
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Prepare results
        results = []
        for doc_id, score in ranked_docs:
            results.append({
                'doc_id': doc_id,
                'text': self.documents[doc_id]['text'],
                'metadata': self.documents[doc_id]['metadata'],
                'score': score
            })
        
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
            'doc_freq': dict(self.doc_freq),
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
        self.inverted_index = defaultdict(lambda: defaultdict(lambda: (0, [])), data['inverted_index'])
        self.documents = data['documents']
        self.doc_lengths = data['doc_lengths']
        self.doc_freq = defaultdict(int, data['doc_freq'])
        self.doc_count = data['doc_count']
        self.term_count = data['term_count']
        self.metrics = data['metrics']
        self.idf_cache.clear()
