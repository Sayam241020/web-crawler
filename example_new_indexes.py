#!/usr/bin/env python3
"""
Example demonstrating RocksDB and PostgreSQL index usage
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def example_rocksdb():
    """Example using RocksDB index"""
    print("\n" + "="*60)
    print("RocksDB Index Example")
    print("="*60)
    
    try:
        from src.indexing.rocksdb_index import RocksDBIndex
        
        print("\n✓ RocksDB library is available")
        print("\nTo use RocksDB index:")
        print("\n1. Build an index:")
        print("   python main.py --mode build \\")
        print("       --index-type rocksdb \\")
        print("       --data-source wiki \\")
        print("       --max-docs 100 \\")
        print("       --db-path ./rocksdb_data/wiki_index")
        
        print("\n2. Query the index:")
        print("   python main.py --mode query \\")
        print("       --index-type rocksdb \\")
        print("       --data-source wiki \\")
        print("       --query 'machine learning' \\")
        print("       --db-path ./rocksdb_data/wiki_index")
        
        print("\nFeatures:")
        print("  - High-performance key-value storage")
        print("  - Automatic write buffering and compaction")
        print("  - Efficient disk usage with compression")
        print("  - No separate server required")
        
    except ImportError:
        print("\n✗ RocksDB library not installed")
        print("\nTo install:")
        print("   pip install python-rocksdb")
        print("\nNote: RocksDB requires compilation. On some systems you may need:")
        print("   - Build tools: apt-get install build-essential")
        print("   - RocksDB dev: apt-get install librocksdb-dev")


def example_postgresql():
    """Example using PostgreSQL index"""
    print("\n" + "="*60)
    print("PostgreSQL Index Example")
    print("="*60)
    
    try:
        from src.indexing.postgresql_index import PostgreSQLIndex
        
        print("\n✓ PostgreSQL library is available")
        print("\nPrerequisites:")
        print("1. Start PostgreSQL server (Docker example):")
        print("   docker run -d -p 5432:5432 \\")
        print("       -e POSTGRES_PASSWORD=postgres \\")
        print("       -e POSTGRES_DB=search_index \\")
        print("       postgres:latest")
        
        print("\n2. Build an index:")
        print("   python main.py --mode build \\")
        print("       --index-type postgresql \\")
        print("       --data-source wiki \\")
        print("       --max-docs 100 \\")
        print("       --pg-host localhost \\")
        print("       --pg-port 5432 \\")
        print("       --pg-database search_index \\")
        print("       --pg-user postgres \\")
        print("       --pg-password postgres")
        
        print("\n3. Query the index:")
        print("   python main.py --mode query \\")
        print("       --index-type postgresql \\")
        print("       --data-source wiki \\")
        print("       --query 'machine learning' \\")
        print("       --pg-host localhost \\")
        print("       --pg-port 5432 \\")
        print("       --pg-database search_index \\")
        print("       --pg-user postgres \\")
        print("       --pg-password postgres")
        
        print("\nFeatures:")
        print("  - ACID transaction guarantees")
        print("  - SQL-based querying and analytics")
        print("  - GIN indexes for text search")
        print("  - Easy backup and replication")
        print("  - Persistent storage across restarts")
        
    except ImportError:
        print("\n✗ PostgreSQL library not installed")
        print("\nTo install:")
        print("   pip install psycopg2-binary")
        print("\nAlternatively (if you want to build from source):")
        print("   pip install psycopg2")


def comparison():
    """Compare the different index types"""
    print("\n" + "="*60)
    print("Index Type Comparison")
    print("="*60)
    
    print("\n┌─────────────┬──────────────────┬──────────────────┬──────────────────┐")
    print("│ Feature     │ Pickle (Default) │ RocksDB          │ PostgreSQL       │")
    print("├─────────────┼──────────────────┼──────────────────┼──────────────────┤")
    print("│ Setup       │ None             │ None             │ Server required  │")
    print("│ Performance │ Fast (memory)    │ Very fast        │ Fast (network)   │")
    print("│ Scalability │ Limited          │ Excellent        │ Excellent        │")
    print("│ Persistence │ File-based       │ LSM tree         │ ACID database    │")
    print("│ Queries     │ Python only      │ Python only      │ SQL + Python     │")
    print("│ Concurrent  │ No               │ Limited          │ Yes              │")
    print("│ ACID        │ No               │ No               │ Yes              │")
    print("│ Best for    │ Small datasets   │ High performance │ Enterprise apps  │")
    print("└─────────────┴──────────────────┴──────────────────┴──────────────────┘")
    
    print("\nRecommendations:")
    print("  • Pickle: Quick prototyping, small datasets (<10K docs)")
    print("  • RocksDB: High-performance apps, large datasets (>100K docs)")
    print("  • PostgreSQL: Enterprise apps, need SQL, concurrent access")


def main():
    """Run all examples"""
    print("="*60)
    print("RocksDB and PostgreSQL Index Examples")
    print("="*60)
    
    example_rocksdb()
    example_postgresql()
    comparison()
    
    print("\n" + "="*60)
    print("For more information, see:")
    print("  - README.md")
    print("  - USAGE_GUIDE.md")
    print("  - python main.py --help")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
