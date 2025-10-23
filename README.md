# Web Crawler and Search Index System

A comprehensive search indexing system with support for Boolean, ranked (TF), and TF-IDF indexes. Implements query processing with Boolean operators (AND, OR, NOT, PHRASE) and supports both News and Wikipedia datasets.

## Features

### Indexing
- **Boolean Index (SelfIndex-v1.1)**: Basic inverted index with document IDs and position information
- **Ranked Index (SelfIndex-v1.2)**: Term frequency-based ranking
- **TF-IDF Index (SelfIndex-v1.3)**: Advanced ranking with TF-IDF scoring
- **Elasticsearch Index (ESIndex-v1.0)**: Wrapper around Elasticsearch for comparison
- **Redis Index (RedisIndex-v1.0)**: Redis-based distributed inverted index

### Query Processing
- Boolean query parser supporting:
  - AND, OR, NOT operators
  - PHRASE queries for exact matches
  - Parentheses for grouping
  - Operator precedence: PHRASE > NOT > AND > OR
- Term-at-a-time (TAAT) query processing
- Document-at-a-time (DAAT) query processing

### Data Sources
- News data from webz.io (JSON format in ZIP files)
- Wikipedia data from HuggingFace datasets

### Performance Metrics
- Query latency (p50, p95, p99 percentiles)
- Indexing time
- Memory footprint
- Index size
- Throughput (queries/second)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data (will be done automatically on first run)
python -c "import nltk; nltk.download('stopwords')"
```

## Project Structure

```
.
├── src/
│   ├── indexing/           # Index implementations
│   │   ├── base_index.py
│   │   ├── boolean_index.py
│   │   ├── ranked_index.py
│   │   └── tfidf_index.py
│   ├── preprocessing/      # Text processing
│   │   └── text_processor.py
│   ├── query/             # Query processing
│   │   ├── boolean_query_parser.py
│   │   └── query_processor.py
│   └── utils/             # Utilities
│       ├── data_loader.py
│       └── metrics.py
├── data/                  # Data directory
├── indices/              # Saved indexes
├── metrics/              # Performance metrics
├── main.py              # Main entry point
└── requirements.txt
```

## Quick Start

### Example Usage
Run the example script to see all features in action:
```bash
python example_usage.py
```

This will demonstrate:
- Basic indexing and querying
- Boolean query parsing
- Ranked search with TF-IDF
- Query processing modes (TAAT vs DAAT)
- Metrics collection
- Index persistence

### Data Visualization
Analyze and visualize word frequencies:
```bash
# For news data
python visualize_data.py --data-source news --data-path ./data/News_Datasets --max-docs 1000

# For wiki data
python visualize_data.py --data-source wiki --max-docs 1000
```

This generates:
- Word frequency bar charts (raw and preprocessed)
- Frequency distribution plots (Zipf's law)
- Statistical summaries

### Evaluation
Compare different index configurations:
```bash
python evaluate.py --data-source news --data-path ./data/News_Datasets --max-docs 1000
```

This produces:
- Performance comparison tables
- Latency plots (P95, P99)
- Memory usage comparison
- Throughput analysis

## Usage

### Building an Index

#### News Data (Boolean Index)
```bash
python main.py --mode build \
    --index-type boolean \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 1000 \
    --version v1.1
```

#### Wikipedia Data (TF-IDF Index)
```bash
python main.py --mode build \
    --index-type tfidf \
    --data-source wiki \
    --max-docs 1000 \
    --version v1.3
```

#### Elasticsearch Index (Optional)
**Prerequisites**: Elasticsearch must be running
```bash
# Start Elasticsearch (Docker example)
docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.x.x

# Install Elasticsearch Python client
pip install elasticsearch

# Build index
python main.py --mode build \
    --index-type elasticsearch \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 1000 \
    --es-host localhost \
    --es-port 9200
```

#### Redis Index (Optional)
**Prerequisites**: Redis must be running
```bash
# Start Redis (Docker example)
docker run -d -p 6379:6379 redis:latest

# Install Redis Python client
pip install redis

# Build index
python main.py --mode build \
    --index-type redis \
    --data-source news \
    --data-path ./data/News_Datasets \
    --max-docs 1000 \
    --redis-host localhost \
    --redis-port 6379
```

### Querying

#### Simple Query
```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source wiki \
    --query "machine learning algorithms"
```

#### Boolean Query
```bash
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '("Apple" AND "iPhone") OR "Android"' \
    --boolean-query
```

#### Phrase Search
```bash
python main.py --mode query \
    --index-type boolean \
    --data-source news \
    --query '"climate change"' \
    --boolean-query
```

#### Term-at-a-Time Processing
```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source wiki \
    --query "artificial intelligence" \
    --query-mode taat
```

#### Document-at-a-Time Processing
```bash
python main.py --mode query \
    --index-type tfidf \
    --data-source wiki \
    --query "artificial intelligence" \
    --query-mode daat
```

#### Batch Queries from File
```bash
# Create queries.txt with one query per line
echo "machine learning" > queries.txt
echo "deep learning" >> queries.txt
echo "neural networks" >> queries.txt

python main.py --mode query \
    --index-type tfidf \
    --data-source wiki \
    --query-file queries.txt
```

## Boolean Query Syntax

### Operators
- **AND**: Both terms must appear in document
  - Example: `"Apple" AND "iPhone"`
- **OR**: Either term can appear in document
  - Example: `"Apple" OR "Samsung"`
- **NOT**: Exclude documents containing the term
  - Example: `"Apple" AND NOT "iPhone"`
- **PHRASE**: Exact phrase match (use quotes)
  - Example: `"machine learning"`

### Operator Precedence
1. PHRASE (highest)
2. NOT
3. AND
4. OR (lowest)

### Examples
```
# Simple AND query
"Python" AND "programming"

# OR query
"Python" OR "Java" OR "C++"

# NOT query
"Python" AND NOT "snake"

# Phrase query
"artificial intelligence"

# Complex query with parentheses
("machine learning" OR "deep learning") AND "Python"

# Multiple operators
("Apple" AND "iPhone") OR ("Samsung" AND "Galaxy")
```

## Index Versions

The system uses a versioning scheme for different index configurations:

- **v1.1**: Boolean index with document IDs and positions
- **v1.2**: Ranked index with term frequency
- **v1.3**: TF-IDF index with advanced scoring

## Text Preprocessing

The system performs the following preprocessing steps:
1. Tokenization
2. Lowercase conversion
3. URL and email removal
4. Punctuation handling
5. Stopword removal (optional)
6. Stemming using Porter Stemmer (optional)

## Performance Metrics

Metrics are automatically collected during indexing and querying:

- **Indexing Time**: Total time to build the index
- **Query Latency**: Response time for queries
  - Average, P50, P95, P99 percentiles
- **Memory Usage**: RAM footprint
- **Index Size**: Disk space used
- **Throughput**: Queries processed per second

Metrics are saved in JSON format in the `metrics/` directory.

## Data Formats

### News Data
Expected structure:
```
data/News_Datasets/
    ├── file1.zip
    │   └── data.json
    └── file2.zip
        └── data.json
```

JSON format:
```json
{
  "title": "Article Title",
  "text": "Article content...",
  "language": "english",
  "url": "https://..."
}
```

### Wikipedia Data
Automatically downloaded from HuggingFace datasets when building a wiki index.

## Extending the System

### Adding a New Index Type
1. Create a new class in `src/indexing/` that extends `BaseIndex`
2. Implement required methods: `add_document()`, `search()`, `save()`, `load()`
3. Add the new index type to `main.py`

### Adding a New Data Source
1. Add a new method in `src/utils/data_loader.py`
2. Follow the iterator pattern yielding `{'doc_id', 'text', 'metadata'}`
3. Update `main.py` to support the new data source

## Persistence

Indexes are persisted to disk using Python's pickle format. They can be saved and loaded:

```python
# Save
index.save("indices/my_index.pkl")

# Load
index.load("indices/my_index.pkl")
```

## Troubleshooting

### NLTK Data Error
If you get an error about missing NLTK data:
```bash
python -c "import nltk; nltk.download('stopwords')"
```

### Memory Issues
For large datasets, use the `--max-docs` parameter to limit the number of documents:
```bash
python main.py --mode build --max-docs 10000 ...
```

### Wikipedia Dataset Issues
If HuggingFace datasets fail to load:
```bash
pip install --upgrade datasets
```

## License

This project is for educational purposes.

## References

- NLTK: https://www.nltk.org/
- HuggingFace Datasets: https://huggingface.co/docs/datasets/
- webz.io: https://webz.io/
