"""
Data loading utilities for News and Wiki datasets
"""
import os
import json
import zipfile
from typing import Iterator, Dict, Any
from datasets import load_dataset


class DataLoader:
    """Load data from various sources"""
    
    @staticmethod
    def load_news_data(data_path: str, max_docs: int = None) -> Iterator[Dict[str, Any]]:
        """
        Load news data from webz.io dataset
        
        Args:
            data_path: Path to news data directory
            max_docs: Maximum number of documents to load
            
        Yields:
            Dictionary with doc_id, text, and metadata
        """
        doc_count = 0
        
        for file_name in os.listdir(data_path):
            if file_name.endswith(".zip"):
                zip_path = os.path.join(data_path, file_name)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for inner_file in zip_ref.namelist():
                        if inner_file.endswith(".json"):
                            with zip_ref.open(inner_file) as f:
                                try:
                                    data = json.load(f)
                                    
                                    # Extract text and metadata
                                    if isinstance(data, dict):
                                        # Check if it's English content
                                        if "language" in data and data["language"].lower() == "english":
                                            text = data.get("text", "")
                                            title = data.get("title", "")
                                            
                                            if text:
                                                doc_id = f"news_{file_name}_{inner_file}_{doc_count}"
                                                
                                                yield {
                                                    'doc_id': doc_id,
                                                    'text': f"{title} {text}",
                                                    'metadata': {
                                                        'source': 'news',
                                                        'title': title,
                                                        'language': data.get('language', ''),
                                                        'url': data.get('url', '')
                                                    }
                                                }
                                                
                                                doc_count += 1
                                                if max_docs and doc_count >= max_docs:
                                                    return
                                except Exception as e:
                                    print(f"Error loading {inner_file}: {e}")
                                    continue
    
    @staticmethod
    def load_wiki_data(split: str = "20231101.en", max_docs: int = None) -> Iterator[Dict[str, Any]]:
        """
        Load Wikipedia data from HuggingFace
        
        Args:
            split: Dataset split to load
            max_docs: Maximum number of documents to load
            
        Yields:
            Dictionary with doc_id, text, and metadata
        """
        try:
            # Load dataset from HuggingFace
            dataset = load_dataset("wikimedia/wikipedia", split, streaming=True)
            
            doc_count = 0
            for item in dataset:
                text = item.get('text', '')
                title = item.get('title', '')
                
                if text:
                    doc_id = f"wiki_{item.get('id', doc_count)}"
                    
                    yield {
                        'doc_id': doc_id,
                        'text': f"{title} {text}",
                        'metadata': {
                            'source': 'wiki',
                            'title': title,
                            'url': item.get('url', '')
                        }
                    }
                    
                    doc_count += 1
                    if max_docs and doc_count >= max_docs:
                        return
        except Exception as e:
            print(f"Error loading Wikipedia data: {e}")
            print("You may need to install the datasets library: pip install datasets")
