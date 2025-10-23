"""
Query processing implementations (Term-at-a-time and Document-at-a-time)
"""
from typing import List, Dict, Any, Set
from collections import defaultdict
import time


class QueryProcessor:
    """Query processing with different strategies"""
    
    def __init__(self, index):
        """
        Initialize query processor
        
        Args:
            index: Index to query
        """
        self.index = index
    
    def term_at_a_time(self, query_terms: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Term-at-a-time (TAAT) query processing
        Processes one query term at a time and accumulates scores
        
        Args:
            query_terms: List of preprocessed query terms
            top_k: Number of results to return
            
        Returns:
            List of ranked documents
        """
        start_time = time.time()
        
        doc_scores = defaultdict(float)
        
        # Process each term sequentially
        for term in query_terms:
            if hasattr(self.index, 'inverted_index') and term in self.index.inverted_index:
                # Get posting list for term
                posting_list = self.index.inverted_index[term]
                
                # Accumulate scores for all documents containing this term
                for doc_id, data in posting_list.items():
                    if isinstance(data, tuple):
                        # Ranked or TF-IDF index
                        tf = data[0]
                        doc_length = self.index.doc_lengths.get(doc_id, 1)
                        
                        # Calculate score based on index type
                        if hasattr(self.index, 'doc_freq'):
                            # TF-IDF index
                            idf = self.index._calculate_idf(term)
                            score = self.index._calculate_tfidf(tf, doc_length, idf)
                        else:
                            # Ranked index (TF only)
                            score = tf / doc_length
                        
                        doc_scores[doc_id] += score
                    else:
                        # Boolean index
                        doc_scores[doc_id] += 1.0
        
        # Sort and return top k
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_id, score in ranked_docs:
            results.append({
                'doc_id': doc_id,
                'text': self.index.documents[doc_id]['text'],
                'metadata': self.index.documents[doc_id]['metadata'],
                'score': score
            })
        
        query_time = time.time() - start_time
        self.index._record_query_time(query_time)
        
        return results
    
    def document_at_a_time(self, query_terms: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Document-at-a-time (DAAT) query processing
        Processes all query terms for one document at a time
        
        Args:
            query_terms: List of preprocessed query terms
            top_k: Number of results to return
            
        Returns:
            List of ranked documents
        """
        start_time = time.time()
        
        # Get all documents that contain at least one query term
        candidate_docs = set()
        for term in query_terms:
            if hasattr(self.index, 'inverted_index') and term in self.index.inverted_index:
                candidate_docs.update(self.index.inverted_index[term].keys())
        
        # Process each document
        doc_scores = {}
        for doc_id in candidate_docs:
            score = 0.0
            doc_length = self.index.doc_lengths.get(doc_id, 1)
            
            # Calculate score for this document across all query terms
            for term in query_terms:
                if hasattr(self.index, 'inverted_index') and term in self.index.inverted_index:
                    if doc_id in self.index.inverted_index[term]:
                        data = self.index.inverted_index[term][doc_id]
                        
                        if isinstance(data, tuple):
                            # Ranked or TF-IDF index
                            tf = data[0]
                            
                            # Calculate score based on index type
                            if hasattr(self.index, 'doc_freq'):
                                # TF-IDF index
                                idf = self.index._calculate_idf(term)
                                score += self.index._calculate_tfidf(tf, doc_length, idf)
                            else:
                                # Ranked index (TF only)
                                score += tf / doc_length
                        else:
                            # Boolean index
                            score += 1.0
            
            doc_scores[doc_id] = score
        
        # Sort and return top k
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_id, score in ranked_docs:
            results.append({
                'doc_id': doc_id,
                'text': self.index.documents[doc_id]['text'],
                'metadata': self.index.documents[doc_id]['metadata'],
                'score': score
            })
        
        query_time = time.time() - start_time
        self.index._record_query_time(query_time)
        
        return results
