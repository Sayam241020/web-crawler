"""
Data visualization for word frequency analysis
"""
import argparse
import os
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
from src.utils.data_loader import DataLoader
from src.preprocessing.text_processor import TextProcessor


def plot_word_frequency(word_freq: Counter, title: str, output_path: str, 
                       top_n: int = 50, log_scale: bool = False):
    """
    Plot word frequency distribution
    
    Args:
        word_freq: Counter object with word frequencies
        title: Plot title
        output_path: Path to save plot
        top_n: Number of top words to plot
        log_scale: Whether to use log scale
    """
    # Get top N words
    top_words = word_freq.most_common(top_n)
    words = [w[0] for w in top_words]
    freqs = [w[1] for w in top_words]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.bar(range(len(words)), freqs)
    
    ax.set_xlabel('Words', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.set_xticks(range(len(words)))
    ax.set_xticklabels(words, rotation=90, ha='right', fontsize=8)
    
    if log_scale:
        ax.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved plot to {output_path}")


def plot_frequency_distribution(word_freq: Counter, output_path: str):
    """
    Plot frequency of frequencies (Zipf's law visualization)
    
    Args:
        word_freq: Counter object with word frequencies
        output_path: Path to save plot
    """
    # Count frequency of frequencies
    freq_of_freq = Counter(word_freq.values())
    
    freqs = sorted(freq_of_freq.keys())
    counts = [freq_of_freq[f] for f in freqs]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.loglog(freqs, counts, 'b.')
    
    ax.set_xlabel('Frequency', fontsize=12)
    ax.set_ylabel('Number of Words', fontsize=12)
    ax.set_title('Word Frequency Distribution (Zipf\'s Law)', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved frequency distribution plot to {output_path}")


def analyze_data(data_source: str, data_path: str = None, max_docs: int = 1000,
                preprocessing: bool = True, output_dir: str = "visualizations"):
    """
    Analyze and visualize data
    
    Args:
        data_source: Data source (news, wiki)
        data_path: Path to data (for news)
        max_docs: Maximum documents to analyze
        preprocessing: Whether to apply preprocessing
        output_dir: Output directory for plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize text processor
    text_processor = TextProcessor(use_stemming=preprocessing, 
                                   use_stopwords=preprocessing)
    
    # Load data and count words
    print(f"Loading {data_source} data...")
    word_freq_raw = Counter()
    word_freq_processed = Counter()
    doc_count = 0
    
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
        # Raw word frequencies (just lowercased and split)
        raw_tokens = doc['text'].lower().split()
        word_freq_raw.update(raw_tokens)
        
        # Preprocessed word frequencies
        processed_tokens = text_processor.preprocess(doc['text'])
        word_freq_processed.update(processed_tokens)
        
        doc_count += 1
        if doc_count % 100 == 0:
            print(f"Processed {doc_count} documents...")
    
    print(f"\nAnalyzed {doc_count} documents")
    print(f"Raw vocabulary size: {len(word_freq_raw)}")
    print(f"Preprocessed vocabulary size: {len(word_freq_processed)}")
    
    # Plot word frequencies without preprocessing
    print("\nGenerating plots...")
    plot_word_frequency(
        word_freq_raw,
        f"{data_source.title()} Data - Word Frequencies (Raw)",
        os.path.join(output_dir, f"{data_source}_word_freq_raw.png"),
        top_n=50
    )
    
    # Plot word frequencies with preprocessing
    plot_word_frequency(
        word_freq_processed,
        f"{data_source.title()} Data - Word Frequencies (Preprocessed)",
        os.path.join(output_dir, f"{data_source}_word_freq_preprocessed.png"),
        top_n=50
    )
    
    # Plot frequency distributions
    plot_frequency_distribution(
        word_freq_raw,
        os.path.join(output_dir, f"{data_source}_freq_distribution_raw.png")
    )
    
    plot_frequency_distribution(
        word_freq_processed,
        os.path.join(output_dir, f"{data_source}_freq_distribution_preprocessed.png")
    )
    
    # Print statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    
    print("\nRaw Data:")
    print(f"  Total words: {sum(word_freq_raw.values())}")
    print(f"  Unique words: {len(word_freq_raw)}")
    print(f"  Top 10 words:")
    for word, freq in word_freq_raw.most_common(10):
        print(f"    {word}: {freq}")
    
    print("\nPreprocessed Data:")
    print(f"  Total words: {sum(word_freq_processed.values())}")
    print(f"  Unique words: {len(word_freq_processed)}")
    print(f"  Top 10 words:")
    for word, freq in word_freq_processed.most_common(10):
        print(f"    {word}: {freq}")


def main():
    parser = argparse.ArgumentParser(description="Visualize word frequencies in data")
    parser.add_argument("--data-source", choices=["news", "wiki"], required=True,
                       help="Data source")
    parser.add_argument("--data-path", help="Path to data (for news)")
    parser.add_argument("--max-docs", type=int, default=1000,
                       help="Maximum documents to analyze")
    parser.add_argument("--no-preprocessing", action="store_true",
                       help="Skip preprocessing (stemming and stopwords)")
    parser.add_argument("--output-dir", default="visualizations",
                       help="Output directory for plots")
    
    args = parser.parse_args()
    
    analyze_data(
        args.data_source,
        args.data_path,
        args.max_docs,
        not args.no_preprocessing,
        args.output_dir
    )


if __name__ == "__main__":
    main()
