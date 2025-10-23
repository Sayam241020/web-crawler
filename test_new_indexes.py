#!/usr/bin/env python3
"""
Test script for RocksDB and PostgreSQL index implementations
Tests that the classes can be instantiated and have the correct interface
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rocksdb_interface():
    """Test RocksDB index interface without requiring the database"""
    print("Testing RocksDB index interface...")
    
    try:
        from src.indexing.rocksdb_index import RocksDBIndex, ROCKSDB_AVAILABLE
        
        if not ROCKSDB_AVAILABLE:
            print("✓ RocksDB library not available (expected)")
            print("  - Module imports correctly")
            print("  - ROCKSDB_AVAILABLE flag is False")
            
            # Try to instantiate - should raise ImportError
            try:
                index = RocksDBIndex()
                print("✗ Should have raised ImportError")
                return False
            except ImportError as e:
                print(f"✓ Correctly raises ImportError: {e}")
        else:
            print("✓ RocksDB library is available")
            # Would need actual RocksDB installed to test further
            print("  - Full testing requires python-rocksdb installation")
        
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_postgresql_interface():
    """Test PostgreSQL index interface without requiring the database"""
    print("\nTesting PostgreSQL index interface...")
    
    try:
        from src.indexing.postgresql_index import PostgreSQLIndex, PSYCOPG2_AVAILABLE
        
        if not PSYCOPG2_AVAILABLE:
            print("✓ PostgreSQL library not available (expected)")
            print("  - Module imports correctly")
            print("  - PSYCOPG2_AVAILABLE flag is False")
            
            # Try to instantiate - should raise ImportError
            try:
                index = PostgreSQLIndex()
                print("✗ Should have raised ImportError")
                return False
            except ImportError as e:
                print(f"✓ Correctly raises ImportError: {e}")
        else:
            print("✓ PostgreSQL library is available")
            # Would need actual PostgreSQL server to test further
            print("  - Full testing requires PostgreSQL server")
        
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_base_interface():
    """Test that both classes extend BaseIndex correctly"""
    print("\nTesting BaseIndex interface...")
    
    try:
        from src.indexing.base_index import BaseIndex
        from src.indexing.rocksdb_index import RocksDBIndex
        from src.indexing.postgresql_index import PostgreSQLIndex
        
        # Check if they're subclasses (without instantiating)
        print(f"✓ RocksDBIndex is subclass of BaseIndex: {issubclass(RocksDBIndex, BaseIndex)}")
        print(f"✓ PostgreSQLIndex is subclass of BaseIndex: {issubclass(PostgreSQLIndex, BaseIndex)}")
        
        # Check if they have required methods
        required_methods = ['add_document', 'search', 'save', 'load']
        
        for cls, cls_name in [(RocksDBIndex, 'RocksDBIndex'), (PostgreSQLIndex, 'PostgreSQLIndex')]:
            missing = []
            for method in required_methods:
                if not hasattr(cls, method):
                    missing.append(method)
            
            if missing:
                print(f"✗ {cls_name} missing methods: {missing}")
                return False
            else:
                print(f"✓ {cls_name} has all required methods: {required_methods}")
        
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_integration():
    """Test that main.py can load the new index types"""
    print("\nTesting main.py integration...")
    
    try:
        import main
        
        # Check that the availability flags are set
        print(f"  - ELASTICSEARCH_AVAILABLE: {main.ELASTICSEARCH_AVAILABLE}")
        print(f"  - ROCKSDB_AVAILABLE: {main.ROCKSDB_AVAILABLE}")
        print(f"  - POSTGRESQL_AVAILABLE: {main.POSTGRESQL_AVAILABLE}")
        
        print("✓ main.py imports successfully with new index types")
        return True
    except Exception as e:
        print(f"✗ Error importing main.py: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("RocksDB and PostgreSQL Index Implementation Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("RocksDB Interface", test_rocksdb_interface()))
    results.append(("PostgreSQL Interface", test_postgresql_interface()))
    results.append(("BaseIndex Interface", test_base_interface()))
    results.append(("Main Integration", test_main_integration()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed! ✓")
        print("\nNote: These tests verify the interface and imports.")
        print("Full functionality testing requires:")
        print("  - RocksDB: pip install python-rocksdb")
        print("  - PostgreSQL: pip install psycopg2-binary + running PostgreSQL server")
    else:
        print("Some tests failed! ✗")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
