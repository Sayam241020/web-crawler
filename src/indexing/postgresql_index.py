"""
PostgreSQL-backed inverted index implementation
Uses PostgreSQL with GIN index for efficient text search
"""
import json
import time
import sys
from typing import List, Dict, Any, Set
from collections import defaultdict
try:
    import psycopg2
    from psycopg2.extras import Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
from ..preprocessing.text_processor import TextProcessor
from .base_index import BaseIndex


class PostgreSQLIndex(BaseIndex):
    """Inverted index backed by PostgreSQL for persistent storage"""
    
    def __init__(self, version: str = "v1.0", index_name: str = "postgresql_index",
                 use_stemming: bool = True, use_stopwords: bool = True,
                 db_config: Dict[str, str] = None):
        """
        Initialize PostgreSQL index
        
        Args:
            version: Version string
            index_name: Name of the index
            use_stemming: Whether to use stemming
            use_stopwords: Whether to remove stopwords
            db_config: PostgreSQL connection config
                      {host, port, database, user, password}
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is not available. Install with: pip install psycopg2-binary")
        
        super().__init__(version, index_name)
        self.text_processor = TextProcessor(use_stemming, use_stopwords)
        
        # PostgreSQL connection
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'search_index',
            'user': 'postgres',
            'password': 'postgres'
        }
        
        self.conn = None
        self.table_prefix = index_name.replace('-', '_').replace(' ', '_')
        
        # Connect and initialize schema
        self._connect()
        self._init_schema()
        self._load_metadata()
    
    def _connect(self):
        """Establish PostgreSQL connection"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
        except Exception as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")
    
    def _init_schema(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        
        # Documents table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_prefix}_documents (
                doc_id VARCHAR(255) PRIMARY KEY,
                text TEXT NOT NULL,
                metadata JSONB,
                doc_length INTEGER
            )
        """)
        
        # Inverted index table with GIN index
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_prefix}_inverted_index (
                term VARCHAR(255) NOT NULL,
                doc_id VARCHAR(255) NOT NULL,
                tf INTEGER NOT NULL,
                positions INTEGER[] NOT NULL,
                PRIMARY KEY (term, doc_id),
                FOREIGN KEY (doc_id) REFERENCES {self.table_prefix}_documents(doc_id)
            )
        """)
        
        # Create GIN index on term for fast lookups
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS {self.table_prefix}_term_idx 
            ON {self.table_prefix}_inverted_index USING btree (term)
        """)
        
        # Metadata table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_prefix}_metadata (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT
            )
        """)
        
        self.conn.commit()
        cursor.close()
    
    def _load_metadata(self):
        """Load index metadata from PostgreSQL"""
        cursor = self.conn.cursor()
        
        cursor.execute(f"""
            SELECT key, value FROM {self.table_prefix}_metadata
            WHERE key IN ('doc_count', 'term_count', 'version', 'index_name')
        """)
        
        metadata = dict(cursor.fetchall())
        self.doc_count = int(metadata.get('doc_count', 0))
        self.term_count = int(metadata.get('term_count', 0))
        
        cursor.close()
    
    def _save_metadata(self):
        """Save index metadata to PostgreSQL"""
        cursor = self.conn.cursor()
        
        metadata = {
            'doc_count': str(self.doc_count),
            'term_count': str(self.term_count),
            'version': self.version,
            'index_name': self.index_name
        }
        
        for key, value in metadata.items():
            cursor.execute(f"""
                INSERT INTO {self.table_prefix}_metadata (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """, (key, value))
        
        self.conn.commit()
        cursor.close()
    
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None):
        """
        Add a document to the index
        
        Args:
            doc_id: Unique document identifier
            text: Document text content
            metadata: Optional document metadata
        """
        start_time = time.time()
        
        cursor = self.conn.cursor()
        
        # Tokenize and process text
        tokens = self.text_processor.preprocess(text)
        doc_length = len(tokens)
        
        # Store document
        cursor.execute(f"""
            INSERT INTO {self.table_prefix}_documents (doc_id, text, metadata, doc_length)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (doc_id) DO UPDATE 
            SET text = EXCLUDED.text, 
                metadata = EXCLUDED.metadata,
                doc_length = EXCLUDED.doc_length
        """, (doc_id, text, Json(metadata or {}), doc_length))
        
        # Build inverted index with positions
        term_positions = defaultdict(list)
        for position, term in enumerate(tokens):
            term_positions[term].append(position)
        
        # Store inverted index entries
        for term, positions in term_positions.items():
            tf = len(positions)
            cursor.execute(f"""
                INSERT INTO {self.table_prefix}_inverted_index (term, doc_id, tf, positions)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (term, doc_id) DO UPDATE 
                SET tf = EXCLUDED.tf, positions = EXCLUDED.positions
            """, (term, doc_id, tf, positions))
        
        self.conn.commit()
        
        self.doc_count += 1
        
        # Update term count
        cursor.execute(f"""
            SELECT COUNT(DISTINCT term) FROM {self.table_prefix}_inverted_index
        """)
        self.term_count = cursor.fetchone()[0]
        
        cursor.close()
        
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
        
        cursor = self.conn.cursor()
        
        # Build SQL query for TF-IDF scoring
        # Calculate IDF for each term and aggregate scores
        query_sql = f"""
            WITH term_df AS (
                SELECT term, COUNT(DISTINCT doc_id) as df
                FROM {self.table_prefix}_inverted_index
                WHERE term = ANY(%s)
                GROUP BY term
            ),
            doc_scores AS (
                SELECT 
                    i.doc_id,
                    SUM(
                        (i.tf::float / d.doc_length) * 
                        LN(%s::float / NULLIF(tdf.df, 0))
                    ) as score
                FROM {self.table_prefix}_inverted_index i
                JOIN {self.table_prefix}_documents d ON i.doc_id = d.doc_id
                JOIN term_df tdf ON i.term = tdf.term
                WHERE i.term = ANY(%s)
                GROUP BY i.doc_id
            )
            SELECT ds.doc_id, ds.score, d.text, d.metadata
            FROM doc_scores ds
            JOIN {self.table_prefix}_documents d ON ds.doc_id = d.doc_id
            ORDER BY ds.score DESC
            LIMIT %s
        """
        
        cursor.execute(query_sql, (query_terms, self.doc_count, query_terms, top_k))
        
        results = []
        for row in cursor.fetchall():
            doc_id, score, text, metadata = row
            results.append({
                'doc_id': doc_id,
                'score': float(score) if score else 0.0,
                'text': text,
                'metadata': metadata or {}
            })
        
        cursor.close()
        
        # Record query time
        query_time = time.time() - start_time
        self._record_query_time(query_time)
        
        return results
    
    def save(self, path: str):
        """
        Save is handled automatically by PostgreSQL
        
        Args:
            path: Not used, kept for interface compatibility
        """
        # Save final metadata
        self._save_metadata()
        print(f"PostgreSQL index data is stored in database: {self.db_config['database']}")
        print(f"Tables: {self.table_prefix}_documents, {self.table_prefix}_inverted_index")
    
    def load(self, path: str):
        """
        Load is handled automatically by PostgreSQL on init
        
        Args:
            path: Not used, kept for interface compatibility
        """
        # Data is automatically loaded on initialization
        self._load_metadata()
        print(f"PostgreSQL index loaded from database: {self.db_config['database']}")
    
    def close(self):
        """Close the PostgreSQL connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
