"""
Text preprocessing utilities for tokenization, stemming, and stopword removal
"""
import re
import string
from typing import List, Set
from collections import Counter
import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

# Download required NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


class TextProcessor:
    """Handles text preprocessing including tokenization, stemming, and stopword removal"""
    
    def __init__(self, use_stemming: bool = True, use_stopwords: bool = True):
        """
        Initialize text processor
        
        Args:
            use_stemming: Whether to apply stemming
            use_stopwords: Whether to remove stopwords
        """
        self.use_stemming = use_stemming
        self.use_stopwords = use_stopwords
        self.stemmer = PorterStemmer() if use_stemming else None
        self.stop_words = set(stopwords.words('english')) if use_stopwords else set()
        
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove punctuation but keep internal hyphens and apostrophes
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        
        # Split into tokens
        tokens = text.split()
        
        # Remove tokens that are just punctuation
        tokens = [token.strip(string.punctuation) for token in tokens if token.strip(string.punctuation)]
        
        return tokens
    
    def preprocess(self, text: str) -> List[str]:
        """
        Full preprocessing pipeline: tokenize, remove stopwords, and stem
        
        Args:
            text: Input text
            
        Returns:
            List of preprocessed tokens
        """
        # Tokenize
        tokens = self.tokenize(text)
        
        # Remove stopwords
        if self.use_stopwords:
            tokens = [token for token in tokens if token not in self.stop_words]
        
        # Apply stemming
        if self.use_stemming and self.stemmer:
            tokens = [self.stemmer.stem(token) for token in tokens]
        
        return tokens
    
    def get_word_frequencies(self, text: str) -> Counter:
        """
        Get word frequency counts from text
        
        Args:
            text: Input text
            
        Returns:
            Counter object with word frequencies
        """
        tokens = self.preprocess(text)
        return Counter(tokens)
    
    def get_vocabulary(self, documents: List[str]) -> Set[str]:
        """
        Extract vocabulary from multiple documents
        
        Args:
            documents: List of text documents
            
        Returns:
            Set of unique terms
        """
        vocab = set()
        for doc in documents:
            tokens = self.preprocess(doc)
            vocab.update(tokens)
        return vocab
