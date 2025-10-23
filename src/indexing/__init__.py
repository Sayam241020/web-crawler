"""
Indexing module for both Elasticsearch and self-implemented indexes
"""
from .base_index import BaseIndex
from .boolean_index import BooleanIndex
from .ranked_index import RankedIndex
from .tfidf_index import TFIDFIndex

__all__ = ['BaseIndex', 'BooleanIndex', 'RankedIndex', 'TFIDFIndex']
