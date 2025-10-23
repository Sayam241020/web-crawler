# Comprehensive Usage Guide

This guide provides detailed instructions for using the Search Index System.

## Table of Contents
1. [Installation](#installation)
2. [Data Preparation](#data-preparation)
3. [Building Indexes](#building-indexes)
4. [Querying](#querying)
5. [Evaluation](#evaluation)
6. [Advanced Features](#advanced-features)
7. [Performance Tuning](#performance-tuning)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd web-crawler

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (happens automatically on first run)
python -c "import nltk; nltk.download('stopwords')"
```

## Data Preparation

### News Data (webz.io)
1. Download news data from webz.io GitHub repository
2. Place ZIP files in `data/News_Datasets/` directory
3. Expected format: JSON files inside ZIP archives

Example data structure:
```
data/News_Datasets/
├── news_batch1.zip
│   └── articles.json
└── news_batch2.zip
    └── articles.json
```

JSON format:
```json
{
  "title": "Article Title",
  "text": "Article content...",
  "language": "english",
  "url": "https://example.com/article"
}
```

### Wikipedia Data
Wikipedia data is automatically downloaded from HuggingFace when building a wiki index.

## Building Indexes

### Index Types

#### 1. Boolean Index (v1.1)
Simple inverted index with document IDs and position information.

```bash
python main.py --mode build \
    --index-type boolean \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 10000 \
    --version v1.1
```

**Use cases:**
- Fast lookup of document presence
- Exact phrase matching
- Boolean query evaluation

#### 2. Ranked Index (v1.2)
Index with term frequency-based ranking.

```bash
python main.py --mode build \
    --index-type ranked \
    --data-source wiki \
    --max-docs 10000 \
    --version v1.2
```

**Use cases:**
- Relevance ranking based on term frequency
- Better than Boolean for result ordering
- Good for general search applications

#### 3. TF-IDF Index (v1.3)
Advanced index with TF-IDF scoring.

```bash
python main.py --mode build \
    --index-type tfidf \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 10000 \
    --version v1.3
```

**Use cases:**
- Most accurate relevance ranking
- Handles common vs. rare terms well
- Best for information retrieval applications

## Querying

### Basic Search

#### Simple Query
```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source news \
    --query "machine learning"
```

Output includes:
- Top 10 matching documents
- Relevance scores
- Document text previews

#### Batch Queries
Create a file `queries.txt`:
```
machine learning
artificial intelligence
deep learning
neural networks
```

Run batch queries:
```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source news \
    --query-file queries.txt
```

### Boolean Queries

Enable Boolean query parsing with `--boolean-query` flag:

#### AND Queries
```bash
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '"Python" AND "programming"' \
    --boolean-query
```

#### OR Queries
```bash
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '"Python" OR "Java"' \
    --boolean-query
```

#### NOT Queries
```bash
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '"Apple" AND NOT "fruit"' \
    --boolean-query
```

#### Phrase Queries
```bash
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '"climate change"' \
    --boolean-query
```

#### Complex Queries
```bash
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '("machine learning" OR "deep learning") AND "Python"' \
    --boolean-query
```

### Query Processing Modes

#### Term-at-a-Time (TAAT)
Processes one query term at a time, accumulating scores.

```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source news \
    --query "machine learning algorithms" \
    --query-mode taat
```

**Advantages:**
- Memory efficient
- Good for long posting lists

#### Document-at-a-Time (DAAT)
Processes all query terms for one document at a time.

```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source news \
    --query "machine learning algorithms" \
    --query-mode daat
```

**Advantages:**
- Better cache locality
- Faster for short posting lists

## Evaluation

### Comprehensive Evaluation
Compare all index types:

```bash
python evaluate.py \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 5000 \
    --output-dir evaluation_results
```

This generates:
- `evaluation_results/news_evaluation_results.json`: Detailed metrics
- `evaluation_results/latency_comparison.png`: Query latency comparison
- `evaluation_results/memory_comparison.png`: Memory usage comparison
- `evaluation_results/throughput_comparison.png`: Throughput comparison

### Metrics Collected

#### A. Latency Metrics
- **Average query time**: Mean response time
- **P50 (median)**: 50th percentile latency
- **P95**: 95th percentile latency
- **P99**: 99th percentile latency

#### B. Throughput Metrics
- **Queries per second (QPS)**: Number of queries processed per second

#### C. Memory Metrics
- **Index size**: Disk space used by index
- **Memory footprint**: RAM usage during operations

#### D. Indexing Metrics
- **Build time**: Time to create index
- **Documents indexed**: Number of documents
- **Vocabulary size**: Number of unique terms

### Custom Evaluation

Create your own evaluation script:

```python
from src.indexing.tfidf_index import TFIDFIndex
from src.utils.metrics import MetricsCollector

# Build index
index = TFIDFIndex(version="v1.3", index_name="custom")
# ... add documents ...

# Run queries
queries = ["query1", "query2", "query3"]
for query in queries:
    results = index.search(query)

# Collect metrics
collector = MetricsCollector()
collector.collect_index_metrics(index, "custom_index")
collector.save_metrics("custom_metrics.json")
```

## Advanced Features

### Data Visualization

#### Word Frequency Analysis
```bash
python visualize_data.py \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 1000 \
    --output-dir visualizations
```

Generates:
- `word_freq_raw.png`: Frequencies before preprocessing
- `word_freq_preprocessed.png`: Frequencies after preprocessing
- `freq_distribution_raw.png`: Zipf's law visualization (raw)
- `freq_distribution_preprocessed.png`: Zipf's law visualization (preprocessed)

#### Without Preprocessing
```bash
python visualize_data.py \
    --data-source news \
    --data-path ./data/News_Datasets \
    --no-preprocessing
```

### Index Persistence

#### Saving Indexes
Indexes are automatically saved when building:
```bash
python main.py --mode build \
    --index-type tfidf \
    --data-source news \
    --data-path ./data/News_Datasets \
    --index-path ./my_indices
```

Index saved to: `./my_indices/news_tfidf_v1.3.pkl`

#### Loading Indexes
Indexes are automatically loaded when querying:
```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source news \
    --index-path ./my_indices \
    --query "test query"
```

### Programmatic Usage

#### Building and Querying
```python
from src.indexing.tfidf_index import TFIDFIndex

# Create index
index = TFIDFIndex(version="v1.3", index_name="my_index")

# Add documents
documents = [
    {"id": "doc1", "text": "Python is great for machine learning"},
    {"id": "doc2", "text": "Java is used in enterprise applications"},
]

for doc in documents:
    index.add_document(doc["id"], doc["text"])

# Query
results = index.search("machine learning", top_k=10)
for result in results:
    print(f"{result['doc_id']}: {result['score']:.4f}")

# Save
index.save("my_index.pkl")

# Load
loaded_index = TFIDFIndex()
loaded_index.load("my_index.pkl")
```

#### Boolean Query Parsing
```python
from src.indexing.boolean_index import BooleanIndex
from src.query.boolean_query_parser import BooleanQueryParser

# Create index
index = BooleanIndex()
# ... add documents ...

# Parse and evaluate query
parser = BooleanQueryParser()
parse_tree = parser.parse('("Python" OR "Java") AND "programming"')
matching_docs = parser.evaluate(parse_tree, index)

for doc_id in matching_docs:
    print(f"Match: {doc_id}")
```

## Performance Tuning

### Memory Optimization

#### Limit Document Count
```bash
python main.py --mode build \
    --max-docs 5000  # Only index first 5000 documents
```

#### Disable Features
```python
from src.preprocessing.text_processor import TextProcessor

# Disable stemming and stopwords for faster processing
processor = TextProcessor(use_stemming=False, use_stopwords=False)
```

### Query Optimization

#### Batch Processing
Process multiple queries in a batch for better throughput:

```python
queries = ["query1", "query2", "query3"]
results = [index.search(q) for q in queries]
```

#### Limit Results
```python
# Only get top 5 results instead of default 10
results = index.search("query", top_k=5)
```

### Index Optimization

#### Choose Right Index Type
- **Boolean**: Fastest for exact matches
- **Ranked**: Good balance of speed and relevance
- **TF-IDF**: Best relevance, slightly slower

#### Preprocessing Trade-offs
- **With stemming**: Smaller index, better recall
- **Without stemming**: Larger index, exact matches
- **With stopwords removed**: Smaller index, faster queries
- **Without stopword removal**: Better for phrase queries

## Common Use Cases

### 1. Document Search Engine
```bash
# Build TF-IDF index for best relevance
python main.py --mode build \
    --index-type tfidf \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 100000

# Query with DAAT for better performance
python main.py --mode query \
    --index-type tfidf \
    --data-source news \
    --query "your search query" \
    --query-mode daat
```

### 2. Boolean Search System
```bash
# Build Boolean index
python main.py --mode build \
    --index-type boolean \
    --data-source news \
    --data-path ./data/News_Datasets

# Complex Boolean queries
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '("keyword1" AND "keyword2") OR "keyword3"' \
    --boolean-query
```

### 3. Research and Analysis
```bash
# Visualize data
python visualize_data.py \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 10000

# Evaluate different approaches
python evaluate.py \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 10000
```

## Troubleshooting

### Out of Memory
Reduce `--max-docs` parameter:
```bash
python main.py --mode build --max-docs 1000
```

### Slow Indexing
Consider:
- Disabling stemming
- Processing in batches
- Using SSD for index storage

### Poor Search Results
Try:
- Using TF-IDF instead of Boolean
- Adjusting preprocessing settings
- Increasing indexed document count

### File Not Found Errors
Check:
- Data path is correct
- Index file exists (for query mode)
- Directory permissions

## Next Steps

1. **Experiment**: Try different index types and configurations
2. **Evaluate**: Run comprehensive evaluations on your data
3. **Optimize**: Tune parameters based on your use case
4. **Extend**: Add custom features or index types

For more examples, see `example_usage.py`.
