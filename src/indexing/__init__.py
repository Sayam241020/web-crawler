"""
Indexing module for both Elasticsearch and self-implemented indexes
"""
from .base_index import BaseIndex
from .boolean_index import BooleanIndex
from .ranked_index import RankedIndex
from .tfidf_index import TFIDFIndex

# Optional dependencies
_available = ['BaseIndex', 'BooleanIndex', 'RankedIndex', 'TFIDFIndex']

try:
    from .elasticsearch_index import ElasticsearchIndex
    _available.append('ElasticsearchIndex')
except ImportError:
    pass

try:
    from .rocksdb_index import RocksDBIndex
    _available.append('RocksDBIndex')
except ImportError:
    pass

try:
    from .postgresql_index import PostgreSQLIndex
    _available.append('PostgreSQLIndex')
except ImportError:
    pass

__all__ = _available
