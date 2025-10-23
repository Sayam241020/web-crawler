"""
Indexing module for both Elasticsearch and self-implemented indexes
"""
from .base_index import BaseIndex
from .boolean_index import BooleanIndex
from .ranked_index import RankedIndex
from .tfidf_index import TFIDFIndex

# Optional dependencies
_optional_indexes = []

try:
    from .elasticsearch_index import ElasticsearchIndex
    _optional_indexes.append('ElasticsearchIndex')
except ImportError:
    pass

try:
    from .redis_index import RedisIndex
    _optional_indexes.append('RedisIndex')
except ImportError:
    pass

__all__ = ['BaseIndex', 'BooleanIndex', 'RankedIndex', 'TFIDFIndex'] + _optional_indexes
