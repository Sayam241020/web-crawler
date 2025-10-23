"""
Example usage of Redis index implementation
Demonstrates Redis-based indexing and querying
"""
import time
from src.indexing.redis_index import RedisIndex
from src.utils.data_loader import DataLoader


def main():
    print("=" * 80)
    print("Redis Index Example")
    print("=" * 80)
    print("\nNote: This example requires Redis to be running.")
    print("Start Redis with: docker run -d -p 6379:6379 redis:latest")
    print("Or install locally: https://redis.io/docs/getting-started/")
    print()
    
    try:
        # Create Redis index
        print("1. Creating Redis index...")
        index = RedisIndex(
            version="v1.0",
            index_name="demo_redis_index",
            redis_host="localhost",
            redis_port=6379
        )
        
        # Clear any existing data
        print("   Clearing existing data...")
        index.clear()
        
        # Add sample documents
        print("\n2. Adding sample documents...")
        sample_docs = [
            {
                "doc_id": "doc1",
                "text": "Artificial intelligence and machine learning are transforming technology",
                "metadata": {"source": "tech", "year": 2024}
            },
            {
                "doc_id": "doc2",
                "text": "Machine learning algorithms require large datasets for training",
                "metadata": {"source": "tech", "year": 2024}
            },
            {
                "doc_id": "doc3",
                "text": "Natural language processing is a subfield of artificial intelligence",
                "metadata": {"source": "tech", "year": 2024}
            },
            {
                "doc_id": "doc4",
                "text": "Deep learning neural networks have achieved remarkable results",
                "metadata": {"source": "tech", "year": 2024}
            },
            {
                "doc_id": "doc5",
                "text": "Computer vision applications use deep learning for image recognition",
                "metadata": {"source": "tech", "year": 2024}
            }
        ]
        
        for doc in sample_docs:
            index.add_document(doc["doc_id"], doc["text"], doc["metadata"])
            print(f"   Added: {doc['doc_id']}")
        
        print(f"\n   Total documents indexed: {index.doc_count}")
        print(f"   Total unique terms: {index.term_count}")
        
        # Perform searches
        print("\n3. Performing searches...")
        
        queries = [
            "machine learning",
            "artificial intelligence",
            "deep learning",
            "computer vision"
        ]
        
        for query in queries:
            print(f"\n   Query: '{query}'")
            start_time = time.time()
            results = index.search(query, top_k=5)
            query_time = (time.time() - start_time) * 1000
            
            print(f"   Found {len(results)} results in {query_time:.2f}ms")
            for i, result in enumerate(results[:3], 1):
                print(f"      {i}. {result['doc_id']}: {result['text'][:60]}...")
        
        # Phrase search
        print("\n4. Performing phrase search...")
        phrase = "machine learning"
        print(f"   Phrase: '{phrase}'")
        
        start_time = time.time()
        results = index.phrase_search(phrase)
        query_time = (time.time() - start_time) * 1000
        
        print(f"   Found {len(results)} results in {query_time:.2f}ms")
        for i, result in enumerate(results, 1):
            print(f"      {i}. {result['doc_id']}: {result['text'][:60]}...")
        
        # Get posting list
        print("\n5. Getting posting list for term 'learning'...")
        posting_list = index.get_posting_list("learning")
        print(f"   Term 'learning' appears in {len(posting_list)} documents:")
        for doc_id, positions in list(posting_list.items())[:3]:
            print(f"      {doc_id}: positions {positions}")
        
        # Show metrics
        print("\n6. Performance metrics:")
        metrics = index.get_metrics()
        print(f"   Indexing time: {metrics['indexing_time']:.4f}s")
        print(f"   Documents indexed: {metrics['doc_count']}")
        print(f"   Unique terms: {metrics['term_count']}")
        if metrics['avg_query_time'] > 0:
            print(f"   Average query time: {metrics['avg_query_time']*1000:.2f}ms")
        
        # Test with Wiki data (small sample)
        print("\n7. Testing with Wikipedia data...")
        print("   Loading 50 Wikipedia documents...")
        
        wiki_index = RedisIndex(
            version="v1.0",
            index_name="wiki_redis_demo",
            redis_host="localhost",
            redis_port=6379
        )
        wiki_index.clear()
        
        data_loader = DataLoader()
        doc_count = 0
        for doc in data_loader.load_wiki_data(max_docs=50):
            wiki_index.add_document(doc['doc_id'], doc['text'], doc['metadata'])
            doc_count += 1
            if doc_count % 10 == 0:
                print(f"   Indexed {doc_count} documents...")
        
        print(f"\n   Indexed {wiki_index.doc_count} Wikipedia documents")
        print(f"   Unique terms: {wiki_index.term_count}")
        
        # Query Wikipedia index
        test_queries = ["python programming", "machine learning", "data science"]
        print("\n   Running test queries...")
        for query in test_queries:
            results = wiki_index.search(query, top_k=3)
            print(f"   '{query}': {len(results)} results")
        
        print("\n" + "=" * 80)
        print("Redis Index Example Complete!")
        print("=" * 80)
        print("\nKey features demonstrated:")
        print("  ✓ Redis-based persistent storage")
        print("  ✓ Fast inverted index lookups")
        print("  ✓ Boolean search with AND semantics")
        print("  ✓ Phrase search with position tracking")
        print("  ✓ Distributed/external storage capability")
        print("\nAdvantages of Redis index:")
        print("  • Data persists across Python sessions")
        print("  • Can be shared across multiple processes")
        print("  • Supports distributed deployments")
        print("  • Built-in Redis reliability and persistence")
        
    except ImportError as e:
        print(f"\nError: {e}")
        print("Install redis package: pip install redis")
    except ConnectionError as e:
        print(f"\nError: {e}")
        print("\nTo start Redis:")
        print("  • Using Docker: docker run -d -p 6379:6379 redis:latest")
        print("  • Or install locally: https://redis.io/docs/getting-started/")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
