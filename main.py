"""
Main entry point for the search index system
"""
import argparse
import os
import time
from src.indexing.boolean_index import BooleanIndex
from src.indexing.ranked_index import RankedIndex
from src.indexing.tfidf_index import TFIDFIndex

try:
    from src.indexing.elasticsearch_index import ElasticsearchIndex
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

try:
    from src.indexing.redis_index import RedisIndex
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.query.boolean_query_parser import BooleanQueryParser
from src.query.query_processor import QueryProcessor
from src.utils.data_loader import DataLoader
from src.utils.metrics import MetricsCollector


def build_index(index_type: str, data_source: str, data_path: str = None, 
                max_docs: int = None, version: str = "v1.0", es_host: str = "localhost",
                es_port: int = 9200, redis_host: str = "localhost", redis_port: int = 6379):
    """
    Build an index from data
    
    Args:
        index_type: Type of index (boolean, ranked, tfidf, elasticsearch, redis)
        data_source: Data source (news, wiki)
        data_path: Path to data (for news)
        max_docs: Maximum number of documents to index
        version: Index version
        es_host: Elasticsearch host (if using elasticsearch)
        es_port: Elasticsearch port (if using elasticsearch)
        redis_host: Redis host (if using redis)
        redis_port: Redis port (if using redis)
        
    Returns:
        Built index
    """
    # Create index
    index_name = f"{data_source}_{index_type}_index"
    
    if index_type == "boolean":
        index = BooleanIndex(version=version, index_name=index_name)
    elif index_type == "ranked":
        index = RankedIndex(version=version, index_name=index_name)
    elif index_type == "tfidf":
        index = TFIDFIndex(version=version, index_name=index_name)
    elif index_type == "elasticsearch":
        if not ELASTICSEARCH_AVAILABLE:
            raise ImportError("Elasticsearch is not available. Install with: pip install elasticsearch")
        index = ElasticsearchIndex(version=version, index_name=index_name, 
                                   host=es_host, port=es_port)
    elif index_type == "redis":
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not available. Install with: pip install redis")
        index = RedisIndex(version=version, index_name=index_name,
                          redis_host=redis_host, redis_port=redis_port)
    else:
        raise ValueError(f"Unknown index type: {index_type}")
    
    # Load and index data
    print(f"Building {index_name}...")
    start_time = time.time()
    
    if data_source == "news":
        if not data_path:
            raise ValueError("data_path required for news data")
        
        data_loader = DataLoader()
        for doc in data_loader.load_news_data(data_path, max_docs):
            index.add_document(doc['doc_id'], doc['text'], doc['metadata'])
            
            if index.doc_count % 100 == 0:
                print(f"Indexed {index.doc_count} documents...")
    
    elif data_source == "wiki":
        data_loader = DataLoader()
        for doc in data_loader.load_wiki_data(max_docs=max_docs):
            index.add_document(doc['doc_id'], doc['text'], doc['metadata'])
            
            if index.doc_count % 100 == 0:
                print(f"Indexed {index.doc_count} documents...")
    
    else:
        raise ValueError(f"Unknown data source: {data_source}")
    
    build_time = time.time() - start_time
    print(f"Built index with {index.doc_count} documents in {build_time:.2f} seconds")
    
    return index


def run_queries(index, queries: list, use_boolean_parser: bool = False, 
                query_mode: str = "default"):
    """
    Run queries on an index
    
    Args:
        index: Index to query
        queries: List of query strings
        use_boolean_parser: Whether to use boolean query parser
        query_mode: Query processing mode (default, taat, daat)
        
    Returns:
        List of results for each query
    """
    results = []
    
    if use_boolean_parser:
        parser = BooleanQueryParser()
        for query in queries:
            print(f"\nQuery: {query}")
            parse_tree = parser.parse(query)
            matching_docs = parser.evaluate(parse_tree, index)
            
            query_results = []
            for doc_id in matching_docs:
                query_results.append({
                    'doc_id': doc_id,
                    'text': index.documents[doc_id]['text'][:200] + "...",
                    'metadata': index.documents[doc_id]['metadata']
                })
            
            results.append(query_results)
            print(f"Found {len(query_results)} results")
    
    elif query_mode in ["taat", "daat"]:
        processor = QueryProcessor(index)
        for query in queries:
            print(f"\nQuery: {query}")
            query_terms = index.text_processor.preprocess(query)
            
            if query_mode == "taat":
                query_results = processor.term_at_a_time(query_terms)
            else:  # daat
                query_results = processor.document_at_a_time(query_terms)
            
            results.append(query_results)
            print(f"Found {len(query_results)} results")
            
            # Print top 3 results
            for i, result in enumerate(query_results[:3], 1):
                print(f"  {i}. Score: {result['score']:.4f}")
                print(f"     {result['text'][:150]}...")
    
    else:  # default search
        for query in queries:
            print(f"\nQuery: {query}")
            query_results = index.search(query)
            results.append(query_results)
            print(f"Found {len(query_results)} results")
            
            # Print top 3 results
            for i, result in enumerate(query_results[:3], 1):
                print(f"  {i}. Score: {result['score']:.4f}")
                print(f"     {result['text'][:150]}...")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Search Index System")
    parser.add_argument("--mode", choices=["build", "query", "evaluate"], 
                       default="build", help="Operation mode")
    parser.add_argument("--index-type", choices=["boolean", "ranked", "tfidf", "elasticsearch", "redis"],
                       default="boolean", help="Type of index")
    parser.add_argument("--data-source", choices=["news", "wiki"],
                       default="news", help="Data source")
    parser.add_argument("--data-path", help="Path to data (for news)")
    parser.add_argument("--max-docs", type=int, help="Maximum documents to index")
    parser.add_argument("--index-path", default="indices", help="Path to save/load index")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--query-file", help="File with queries (one per line)")
    parser.add_argument("--boolean-query", action="store_true", 
                       help="Use boolean query parser")
    parser.add_argument("--query-mode", choices=["default", "taat", "daat"],
                       default="default", help="Query processing mode")
    parser.add_argument("--metrics-dir", default="metrics", help="Metrics output directory")
    parser.add_argument("--version", default="v1.0", help="Index version")
    parser.add_argument("--es-host", default="localhost", help="Elasticsearch host")
    parser.add_argument("--es-port", type=int, default=9200, help="Elasticsearch port")
    parser.add_argument("--redis-host", default="localhost", help="Redis host")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis port")
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs(args.index_path, exist_ok=True)
    os.makedirs(args.metrics_dir, exist_ok=True)
    
    index_file = os.path.join(args.index_path, 
                             f"{args.data_source}_{args.index_type}_{args.version}.pkl")
    
    if args.mode == "build":
        # Build index
        index = build_index(args.index_type, args.data_source, args.data_path,
                          args.max_docs, args.version, args.es_host, args.es_port,
                          args.redis_host, args.redis_port)
        
        # Save index (not needed for Elasticsearch or Redis as they persist externally)
        if args.index_type not in ["elasticsearch", "redis"]:
            print(f"\nSaving index to {index_file}...")
            index.save(index_file)
            print("Index saved successfully")
        elif args.index_type == "elasticsearch":
            print("\nElasticsearch index is stored on ES server")
        elif args.index_type == "redis":
            print("\nRedis index is stored on Redis server")
        
        # Collect metrics
        metrics = MetricsCollector()
        metrics.collect_index_metrics(index, index.index_name)
        metrics.save_metrics(os.path.join(args.metrics_dir, 
                                         f"{index.index_name}_metrics.json"))
        print(f"Metrics saved to {args.metrics_dir}")
    
    elif args.mode == "query":
        # Load index
        if args.index_type not in ["elasticsearch", "redis"]:
            print(f"Loading index from {index_file}...")
            
            if args.index_type == "boolean":
                index = BooleanIndex()
            elif args.index_type == "ranked":
                index = RankedIndex()
            elif args.index_type == "tfidf":
                index = TFIDFIndex()
            
            index.load(index_file)
            print(f"Loaded index with {index.doc_count} documents")
        elif args.index_type == "elasticsearch":
            # Connect to Elasticsearch
            if not ELASTICSEARCH_AVAILABLE:
                print("Error: Elasticsearch library not installed")
                print("Install with: pip install elasticsearch")
                return
            
            print(f"Connecting to Elasticsearch at {args.es_host}:{args.es_port}...")
            index = ElasticsearchIndex(version=args.version, 
                                      index_name=f"{args.data_source}_{args.index_type}_index",
                                      host=args.es_host, port=args.es_port)
            index.load("")  # Check connection
        elif args.index_type == "redis":
            # Connect to Redis
            if not REDIS_AVAILABLE:
                print("Error: Redis library not installed")
                print("Install with: pip install redis")
                return
            
            print(f"Connecting to Redis at {args.redis_host}:{args.redis_port}...")
            index = RedisIndex(version=args.version,
                              index_name=f"{args.data_source}_{args.index_type}_index",
                              redis_host=args.redis_host, redis_port=args.redis_port)
            print(f"Connected to Redis with {index.doc_count} documents")
        
        # Get queries
        queries = []
        if args.query:
            queries = [args.query]
        elif args.query_file:
            with open(args.query_file, 'r') as f:
                queries = [line.strip() for line in f if line.strip()]
        else:
            print("No query provided. Use --query or --query-file")
            return
        
        # Run queries
        run_queries(index, queries, args.boolean_query, args.query_mode)
    
    elif args.mode == "evaluate":
        # Evaluate multiple indexes
        print("Evaluation mode - comparing different index configurations")
        
        # This would involve building multiple indexes and comparing their performance
        # For now, just provide a message
        print("To evaluate, build multiple indexes with different configurations")
        print("and compare their metrics files in the metrics directory")


if __name__ == "__main__":
    main()
