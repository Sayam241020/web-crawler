"""
Example usage of the search index system
"""
import os
from src.indexing.boolean_index import BooleanIndex
from src.indexing.ranked_index import RankedIndex
from src.indexing.tfidf_index import TFIDFIndex
from src.query.boolean_query_parser import BooleanQueryParser
from src.query.query_processor import QueryProcessor
from src.utils.metrics import MetricsCollector


def example_basic_indexing():
    """Example of basic indexing and querying"""
    print("=" * 80)
    print("Example 1: Basic Boolean Indexing")
    print("=" * 80)
    
    # Create a boolean index
    index = BooleanIndex(version="v1.1", index_name="example_boolean")
    
    # Add sample documents
    documents = [
        {"id": "doc1", "text": "Python is a popular programming language for machine learning"},
        {"id": "doc2", "text": "Java is widely used in enterprise applications"},
        {"id": "doc3", "text": "Machine learning and deep learning are transforming AI"},
        {"id": "doc4", "text": "Python programming is easy to learn for beginners"},
        {"id": "doc5", "text": "Deep learning models require large amounts of data"}
    ]
    
    for doc in documents:
        index.add_document(doc["id"], doc["text"])
    
    print(f"\nIndexed {index.doc_count} documents")
    print(f"Vocabulary size: {index.term_count} terms")
    
    # Simple search
    print("\n" + "-" * 80)
    print("Query: 'machine learning'")
    results = index.search("machine learning")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Document: {result['doc_id']}")
        print(f"   Text: {result['text']}")
    
    # Phrase search
    print("\n" + "-" * 80)
    print("Phrase Query: 'machine learning'")
    results = index.phrase_search("machine learning")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Document: {result['doc_id']}")
        print(f"   Text: {result['text']}")
        print(f"   Phrase at position: {result.get('phrase_position', 'N/A')}")


def example_boolean_queries():
    """Example of boolean query parsing"""
    print("\n" + "=" * 80)
    print("Example 2: Boolean Query Parsing")
    print("=" * 80)
    
    # Create index
    index = BooleanIndex(version="v1.1", index_name="example_boolean2")
    
    # Add documents
    documents = [
        {"id": "doc1", "text": "Apple released the new iPhone with advanced features"},
        {"id": "doc2", "text": "Samsung Galaxy phone has excellent camera quality"},
        {"id": "doc3", "text": "Apple and Samsung are competing in the smartphone market"},
        {"id": "doc4", "text": "The new iPad tablet from Apple is powerful"},
        {"id": "doc5", "text": "Android phones offer great customization options"}
    ]
    
    for doc in documents:
        index.add_document(doc["id"], doc["text"])
    
    # Boolean queries
    parser = BooleanQueryParser()
    
    queries = [
        '"Apple" AND "iPhone"',
        '"Apple" OR "Samsung"',
        '"Apple" AND NOT "iPhone"',
        '("Apple" OR "Samsung") AND "phone"'
    ]
    
    for query in queries:
        print(f"\n{'-' * 80}")
        print(f"Query: {query}")
        
        parse_tree = parser.parse(query)
        print(f"Parse tree: {parse_tree}")
        
        matching_docs = parser.evaluate(parse_tree, index)
        print(f"Matching documents: {matching_docs}")
        
        for doc_id in matching_docs:
            print(f"  - {doc_id}: {index.documents[doc_id]['text']}")


def example_ranked_search():
    """Example of ranked search with TF-IDF"""
    print("\n" + "=" * 80)
    print("Example 3: Ranked Search (TF-IDF)")
    print("=" * 80)
    
    # Create TF-IDF index
    index = TFIDFIndex(version="v1.3", index_name="example_tfidf")
    
    # Add documents
    documents = [
        {"id": "doc1", "text": "Machine learning is a subset of artificial intelligence"},
        {"id": "doc2", "text": "Deep learning is a subset of machine learning"},
        {"id": "doc3", "text": "Neural networks are used in deep learning"},
        {"id": "doc4", "text": "Machine learning algorithms learn from data"},
        {"id": "doc5", "text": "Artificial intelligence and machine learning are transforming industries"}
    ]
    
    for doc in documents:
        index.add_document(doc["id"], doc["text"])
    
    # Search with ranking
    print("\n" + "-" * 80)
    print("Query: 'machine learning'")
    results = index.search("machine learning", top_k=5)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Document: {result['doc_id']} (Score: {result['score']:.4f})")
        print(f"   Text: {result['text']}")


def example_query_processing_modes():
    """Example of different query processing modes"""
    print("\n" + "=" * 80)
    print("Example 4: Query Processing Modes (TAAT vs DAAT)")
    print("=" * 80)
    
    # Create index
    index = TFIDFIndex(version="v1.3", index_name="example_processing")
    
    # Add documents
    documents = [
        {"id": "doc1", "text": "Python programming language is versatile and powerful"},
        {"id": "doc2", "text": "Python is great for data science and machine learning"},
        {"id": "doc3", "text": "Java programming is used in enterprise applications"},
        {"id": "doc4", "text": "Programming languages like Python and Java are popular"},
        {"id": "doc5", "text": "Learn Python programming for artificial intelligence"}
    ]
    
    for doc in documents:
        index.add_document(doc["id"], doc["text"])
    
    # Create query processor
    processor = QueryProcessor(index)
    query_terms = index.text_processor.preprocess("Python programming")
    
    # Term-at-a-Time
    print("\n" + "-" * 80)
    print("Term-at-a-Time (TAAT) Processing")
    print(f"Query: 'Python programming'")
    results = processor.term_at_a_time(query_terms, top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Document: {result['doc_id']} (Score: {result['score']:.4f})")
        print(f"   Text: {result['text']}")
    
    # Document-at-a-Time
    print("\n" + "-" * 80)
    print("Document-at-a-Time (DAAT) Processing")
    print(f"Query: 'Python programming'")
    results = processor.document_at_a_time(query_terms, top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Document: {result['doc_id']} (Score: {result['score']:.4f})")
        print(f"   Text: {result['text']}")


def example_metrics_collection():
    """Example of metrics collection"""
    print("\n" + "=" * 80)
    print("Example 5: Metrics Collection")
    print("=" * 80)
    
    # Create and populate index
    index = TFIDFIndex(version="v1.3", index_name="example_metrics")
    
    for i in range(100):
        index.add_document(f"doc{i}", f"This is document number {i} with some sample text")
    
    # Run some queries
    for _ in range(10):
        index.search("sample text")
    
    # Collect metrics
    metrics_collector = MetricsCollector()
    metrics_collector.collect_index_metrics(index, "example_tfidf")
    
    # Print metrics
    metrics = index.get_metrics()
    print(f"\nIndex Metrics:")
    print(f"  - Documents: {metrics['doc_count']}")
    print(f"  - Terms: {metrics['term_count']}")
    print(f"  - Indexing time: {metrics['indexing_time']:.4f} seconds")
    print(f"  - Average query time: {metrics['avg_query_time']:.6f} seconds")
    print(f"  - P95 query time: {metrics['p95_query_time']:.6f} seconds")
    print(f"  - P99 query time: {metrics['p99_query_time']:.6f} seconds")
    print(f"  - Memory usage: {metrics['memory_usage_mb']:.2f} MB")
    
    # Save metrics
    os.makedirs("metrics", exist_ok=True)
    metrics_collector.save_metrics("metrics/example_metrics.json")
    print(f"\nMetrics saved to metrics/example_metrics.json")


def example_persistence():
    """Example of saving and loading indexes"""
    print("\n" + "=" * 80)
    print("Example 6: Index Persistence")
    print("=" * 80)
    
    # Create and save index
    print("\nCreating index...")
    index = BooleanIndex(version="v1.1", index_name="example_persistence")
    
    for i in range(10):
        index.add_document(f"doc{i}", f"Document {i} contains important information")
    
    os.makedirs("indices", exist_ok=True)
    index_path = "indices/example_index.pkl"
    
    print(f"Saving index to {index_path}...")
    index.save(index_path)
    print(f"Index saved (size: {os.path.getsize(index_path)} bytes)")
    
    # Load index
    print(f"\nLoading index from {index_path}...")
    loaded_index = BooleanIndex()
    loaded_index.load(index_path)
    
    print(f"Index loaded successfully!")
    print(f"  - Documents: {loaded_index.doc_count}")
    print(f"  - Terms: {loaded_index.term_count}")
    
    # Query loaded index
    results = loaded_index.search("important information")
    print(f"\nQuery 'important information': {len(results)} results")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("SEARCH INDEX SYSTEM - EXAMPLES")
    print("=" * 80)
    
    try:
        example_basic_indexing()
        example_boolean_queries()
        example_ranked_search()
        example_query_processing_modes()
        example_metrics_collection()
        example_persistence()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
