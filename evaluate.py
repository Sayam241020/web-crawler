"""
Comprehensive evaluation script for comparing different index configurations
"""
import argparse
import os
import time
import json
from typing import List, Dict, Any
from src.indexing.boolean_index import BooleanIndex
from src.indexing.ranked_index import RankedIndex
from src.indexing.tfidf_index import TFIDFIndex
from src.utils.data_loader import DataLoader
from src.utils.metrics import MetricsCollector


def generate_test_queries() -> List[str]:
    """
    Generate a diverse set of test queries
    
    Returns:
        List of test queries
    """
    return [
        # Single word queries
        "technology",
        "health",
        "education",
        
        # Two word queries
        "machine learning",
        "climate change",
        "artificial intelligence",
        
        # Multi-word queries
        "natural language processing",
        "renewable energy sources",
        "economic growth factors",
        
        # Common terms
        "data science",
        "social media",
        "quantum computing",
        
        # Specific queries
        "deep neural networks",
        "blockchain technology applications",
        "sustainable development goals"
    ]


def load_data_and_build_indexes(data_source: str, data_path: str = None, 
                                max_docs: int = 1000) -> List[Dict[str, Any]]:
    """
    Load data once for all index types
    
    Args:
        data_source: Data source (news, wiki)
        data_path: Path to data (for news)
        max_docs: Maximum documents to load
        
    Returns:
        List of documents
    """
    print(f"Loading {data_source} data...")
    documents = []
    
    data_loader = DataLoader()
    
    if data_source == "news":
        if not data_path:
            raise ValueError("data_path required for news data")
        data_iter = data_loader.load_news_data(data_path, max_docs)
    elif data_source == "wiki":
        data_iter = data_loader.load_wiki_data(max_docs=max_docs)
    else:
        raise ValueError(f"Unknown data source: {data_source}")
    
    for doc in data_iter:
        documents.append(doc)
        if len(documents) % 100 == 0:
            print(f"Loaded {len(documents)} documents...")
    
    print(f"Total documents loaded: {len(documents)}")
    return documents


def build_index(index_type: str, documents: List[Dict[str, Any]], 
               version: str, data_source: str) -> Any:
    """
    Build an index from pre-loaded documents
    
    Args:
        index_type: Type of index
        documents: List of documents
        version: Index version
        data_source: Data source name
        
    Returns:
        Built index
    """
    index_name = f"{data_source}_{index_type}_index"
    
    print(f"\nBuilding {index_name} ({version})...")
    start_time = time.time()
    
    if index_type == "boolean":
        index = BooleanIndex(version=version, index_name=index_name)
    elif index_type == "ranked":
        index = RankedIndex(version=version, index_name=index_name)
    elif index_type == "tfidf":
        index = TFIDFIndex(version=version, index_name=index_name)
    else:
        raise ValueError(f"Unknown index type: {index_type}")
    
    for doc in documents:
        index.add_document(doc['doc_id'], doc['text'], doc['metadata'])
    
    build_time = time.time() - start_time
    print(f"Built {index_name} with {index.doc_count} documents in {build_time:.2f}s")
    
    return index


def run_benchmark(index: Any, queries: List[str], name: str) -> Dict[str, Any]:
    """
    Benchmark an index with queries
    
    Args:
        index: Index to benchmark
        queries: List of queries
        name: Index name
        
    Returns:
        Benchmark results
    """
    print(f"\nBenchmarking {name}...")
    
    query_times = []
    results_count = []
    
    # Warm up
    for _ in range(3):
        index.search(queries[0])
    
    # Run benchmark
    for query in queries:
        start_time = time.time()
        results = index.search(query, top_k=10)
        query_time = time.time() - start_time
        
        query_times.append(query_time)
        results_count.append(len(results))
    
    # Calculate statistics
    avg_time = sum(query_times) / len(query_times)
    sorted_times = sorted(query_times)
    p50 = sorted_times[int(0.50 * len(sorted_times))]
    p95 = sorted_times[int(0.95 * len(sorted_times))]
    p99 = sorted_times[int(0.99 * len(sorted_times))]
    
    avg_results = sum(results_count) / len(results_count)
    
    # Calculate throughput
    total_time = sum(query_times)
    throughput = len(queries) / total_time if total_time > 0 else 0
    
    return {
        'name': name,
        'num_queries': len(queries),
        'avg_query_time_ms': avg_time * 1000,
        'p50_ms': p50 * 1000,
        'p95_ms': p95 * 1000,
        'p99_ms': p99 * 1000,
        'throughput_qps': throughput,
        'avg_results': avg_results,
        'doc_count': index.doc_count,
        'term_count': index.term_count,
        'indexing_time': index.metrics['indexing_time']
    }


def compare_indexes(data_source: str, data_path: str = None, max_docs: int = 1000,
                   output_dir: str = "evaluation"):
    """
    Compare different index configurations
    
    Args:
        data_source: Data source
        data_path: Path to data (for news)
        max_docs: Maximum documents
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data once
    documents = load_data_and_build_indexes(data_source, data_path, max_docs)
    
    # Generate test queries
    queries = generate_test_queries()
    print(f"\nGenerated {len(queries)} test queries")
    
    # Build different index types
    indexes = [
        ('boolean', 'v1.1'),
        ('ranked', 'v1.2'),
        ('tfidf', 'v1.3')
    ]
    
    results = []
    metrics_collector = MetricsCollector()
    
    for index_type, version in indexes:
        # Build index
        index = build_index(index_type, documents, version, data_source)
        
        # Save index
        index_file = os.path.join(output_dir, f"{index.index_name}.pkl")
        index.save(index_file)
        
        # Benchmark
        benchmark_result = run_benchmark(index, queries, index.index_name)
        results.append(benchmark_result)
        
        # Collect metrics
        metrics_collector.collect_index_metrics(index, index.index_name)
    
    # Save results
    results_file = os.path.join(output_dir, f"{data_source}_evaluation_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {results_file}")
    
    # Generate report
    print("\n" + "=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    
    print(f"\nData Source: {data_source}")
    print(f"Documents: {max_docs}")
    print(f"Queries: {len(queries)}")
    
    print("\n" + "-" * 80)
    print(f"{'Index':<30} {'Build Time':<12} {'Avg Query':<12} {'P95':<12} {'P99':<12} {'QPS':<8}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['name']:<30} "
              f"{result['indexing_time']:<12.3f} "
              f"{result['avg_query_time_ms']:<12.4f} "
              f"{result['p95_ms']:<12.4f} "
              f"{result['p99_ms']:<12.4f} "
              f"{result['throughput_qps']:<8.2f}")
    
    print("-" * 80)
    
    # Generate plots
    metrics_collector.generate_report(output_dir)
    
    # Plot throughput comparison
    throughput_data = {r['name']: r['throughput_qps'] for r in results}
    metrics_collector.plot_throughput_comparison(
        throughput_data,
        os.path.join(output_dir, 'throughput_comparison.png')
    )
    
    print(f"\nFull evaluation report generated in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare indexes")
    parser.add_argument("--data-source", choices=["news", "wiki"], required=True,
                       help="Data source")
    parser.add_argument("--data-path", help="Path to data (for news)")
    parser.add_argument("--max-docs", type=int, default=1000,
                       help="Maximum documents to index")
    parser.add_argument("--output-dir", default="evaluation",
                       help="Output directory")
    
    args = parser.parse_args()
    
    compare_indexes(
        args.data_source,
        args.data_path,
        args.max_docs,
        args.output_dir
    )


if __name__ == "__main__":
    main()
