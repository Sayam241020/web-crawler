"""
Example usage of Elasticsearch index (ESIndex-v1.0)

Prerequisites:
1. Install Elasticsearch: 
   - Download from https://www.elastic.co/downloads/elasticsearch
   - Or use Docker: docker run -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.x.x

2. Install Python client:
   pip install elasticsearch

3. Start Elasticsearch service
"""
import sys

try:
    from src.indexing.elasticsearch_index import ElasticsearchIndex
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    print("Error: Elasticsearch library not installed")
    print("Install with: pip install elasticsearch")
    sys.exit(1)


def example_elasticsearch_basic():
    """Basic Elasticsearch example"""
    print("=" * 80)
    print("Example: Elasticsearch Index (ESIndex-v1.0)")
    print("=" * 80)
    
    try:
        # Create Elasticsearch index
        print("\nConnecting to Elasticsearch at localhost:9200...")
        index = ElasticsearchIndex(
            version="v1.0",
            index_name="example_es_index",
            host="localhost",
            port=9200
        )
        
        print("Connected successfully!")
        
        # Add sample documents
        print("\nIndexing documents...")
        documents = [
            {"id": "doc1", "text": "Python is a popular programming language"},
            {"id": "doc2", "text": "Elasticsearch is a powerful search engine"},
            {"id": "doc3", "text": "Machine learning requires large datasets"},
            {"id": "doc4", "text": "Python is great for machine learning"},
            {"id": "doc5", "text": "Search engines use inverted indexes"}
        ]
        
        for doc in documents:
            index.add_document(doc["id"], doc["text"])
        
        # Refresh index to make documents searchable
        index.refresh()
        
        print(f"Indexed {index.doc_count} documents")
        
        # Simple search
        print("\n" + "-" * 80)
        print("Query: 'machine learning'")
        results = index.search("machine learning", top_k=5)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Document: {result['doc_id']} (Score: {result['score']:.4f})")
            print(f"   Text: {result['text']}")
        
        # Boolean search
        print("\n" + "-" * 80)
        print("Boolean Query: 'Python AND learning' (AND operator)")
        results = index.boolean_search("Python learning", operator="AND", top_k=5)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Document: {result['doc_id']} (Score: {result['score']:.4f})")
            print(f"   Text: {result['text']}")
        
        # Phrase search
        print("\n" + "-" * 80)
        print("Phrase Query: 'machine learning'")
        results = index.phrase_search("machine learning", top_k=5)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Document: {result['doc_id']} (Score: {result['score']:.4f})")
            print(f"   Text: {result['text']}")
        
        # Cleanup
        print("\n" + "-" * 80)
        print("Cleaning up...")
        index.delete_index()
        print("Example completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Elasticsearch is running:")
        print("  - Download: https://www.elastic.co/downloads/elasticsearch")
        print("  - Or use Docker: docker run -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.x.x")


def example_elasticsearch_comparison():
    """Compare Elasticsearch with self-implemented index"""
    print("\n" + "=" * 80)
    print("Example: Elasticsearch vs. Self-Implemented Index Comparison")
    print("=" * 80)
    
    from src.indexing.tfidf_index import TFIDFIndex
    import time
    
    try:
        # Sample documents
        documents = [
            {"id": f"doc{i}", "text": f"Document {i} about various topics including technology"}
            for i in range(100)
        ]
        documents.extend([
            {"id": "doc_ml1", "text": "Machine learning is transforming artificial intelligence"},
            {"id": "doc_ml2", "text": "Deep learning and machine learning are related"},
            {"id": "doc_ml3", "text": "Artificial intelligence uses machine learning algorithms"}
        ])
        
        # Build Elasticsearch index
        print("\nBuilding Elasticsearch index...")
        es_start = time.time()
        es_index = ElasticsearchIndex(
            version="v1.0",
            index_name="comparison_es",
            host="localhost",
            port=9200
        )
        
        for doc in documents:
            es_index.add_document(doc["id"], doc["text"])
        
        es_index.refresh()
        es_build_time = time.time() - es_start
        
        # Build TF-IDF index
        print("Building TF-IDF index...")
        tfidf_start = time.time()
        tfidf_index = TFIDFIndex(version="v1.3", index_name="comparison_tfidf")
        
        for doc in documents:
            tfidf_index.add_document(doc["id"], doc["text"])
        
        tfidf_build_time = time.time() - tfidf_start
        
        # Compare build times
        print("\n" + "-" * 80)
        print("Build Time Comparison:")
        print(f"  Elasticsearch: {es_build_time:.4f} seconds")
        print(f"  TF-IDF Index:  {tfidf_build_time:.4f} seconds")
        
        # Query both indexes
        query = "machine learning"
        
        print("\n" + "-" * 80)
        print(f"Query: '{query}'")
        
        # Elasticsearch query
        es_query_start = time.time()
        es_results = es_index.search(query, top_k=3)
        es_query_time = time.time() - es_query_start
        
        # TF-IDF query
        tfidf_query_start = time.time()
        tfidf_results = tfidf_index.search(query, top_k=3)
        tfidf_query_time = time.time() - tfidf_query_start
        
        print(f"\nElasticsearch Results (query time: {es_query_time*1000:.4f} ms):")
        for i, result in enumerate(es_results, 1):
            print(f"  {i}. {result['doc_id']}: {result['text'][:60]}...")
        
        print(f"\nTF-IDF Index Results (query time: {tfidf_query_time*1000:.4f} ms):")
        for i, result in enumerate(tfidf_results, 1):
            print(f"  {i}. {result['doc_id']}: {result['text'][:60]}...")
        
        # Cleanup
        print("\n" + "-" * 80)
        print("Cleaning up...")
        es_index.delete_index()
        print("Comparison completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Elasticsearch is running")


def main():
    """Run Elasticsearch examples"""
    if not ELASTICSEARCH_AVAILABLE:
        return
    
    print("\n" + "=" * 80)
    print("ELASTICSEARCH INDEX EXAMPLES (ESIndex-v1.0)")
    print("=" * 80)
    
    try:
        example_elasticsearch_basic()
        example_elasticsearch_comparison()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
