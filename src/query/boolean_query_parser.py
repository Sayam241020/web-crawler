"""
Boolean query parser for AND, OR, NOT, and PHRASE operations
"""
import re
from typing import List, Set, Any
from enum import Enum


class QueryOperator(Enum):
    """Query operators"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    PHRASE = "PHRASE"


class QueryNode:
    """Node in query parse tree"""
    
    def __init__(self, operator: QueryOperator = None, value: Any = None):
        self.operator = operator
        self.value = value
        self.left = None
        self.right = None
    
    def __repr__(self):
        if self.operator == QueryOperator.PHRASE:
            return f'PHRASE("{self.value}")'
        elif self.operator == QueryOperator.NOT:
            return f'NOT({self.left})'
        elif self.operator in [QueryOperator.AND, QueryOperator.OR]:
            return f'({self.left} {self.operator.value} {self.right})'
        else:
            return f'"{self.value}"'


class BooleanQueryParser:
    """Parser for boolean queries with AND, OR, NOT, and PHRASE operators"""
    
    def __init__(self):
        self.tokens = []
        self.pos = 0
    
    def parse(self, query: str) -> QueryNode:
        """
        Parse a boolean query string
        
        Args:
            query: Query string
            
        Returns:
            Root node of parse tree
        """
        # Tokenize query
        self.tokens = self._tokenize(query)
        self.pos = 0
        
        if not self.tokens:
            return None
        
        return self._parse_or()
    
    def _tokenize(self, query: str) -> List[str]:
        """
        Tokenize query string
        
        Args:
            query: Query string
            
        Returns:
            List of tokens
        """
        # Pattern to match:
        # - Quoted phrases
        # - Operators (AND, OR, NOT)
        # - Parentheses
        # - Words
        pattern = r'"[^"]*"|AND|OR|NOT|\(|\)|[^\s\(\)]+'
        tokens = re.findall(pattern, query)
        return tokens
    
    def _current_token(self) -> str:
        """Get current token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def _consume(self) -> str:
        """Consume and return current token"""
        token = self._current_token()
        self.pos += 1
        return token
    
    def _parse_or(self) -> QueryNode:
        """Parse OR expression (lowest precedence)"""
        left = self._parse_and()
        
        while self._current_token() == "OR":
            self._consume()  # consume OR
            right = self._parse_and()
            node = QueryNode(QueryOperator.OR)
            node.left = left
            node.right = right
            left = node
        
        return left
    
    def _parse_and(self) -> QueryNode:
        """Parse AND expression"""
        left = self._parse_not()
        
        while self._current_token() == "AND":
            self._consume()  # consume AND
            right = self._parse_not()
            node = QueryNode(QueryOperator.AND)
            node.left = left
            node.right = right
            left = node
        
        return left
    
    def _parse_not(self) -> QueryNode:
        """Parse NOT expression"""
        if self._current_token() == "NOT":
            self._consume()  # consume NOT
            operand = self._parse_not()
            node = QueryNode(QueryOperator.NOT)
            node.left = operand
            return node
        
        return self._parse_primary()
    
    def _parse_primary(self) -> QueryNode:
        """Parse primary expression (term, phrase, or parenthesized expression)"""
        token = self._current_token()
        
        if not token:
            return None
        
        # Parenthesized expression
        if token == "(":
            self._consume()  # consume (
            node = self._parse_or()
            if self._current_token() == ")":
                self._consume()  # consume )
            return node
        
        # Quoted phrase
        if token.startswith('"') and token.endswith('"'):
            phrase = token[1:-1]  # remove quotes
            self._consume()
            node = QueryNode(QueryOperator.PHRASE, phrase)
            return node
        
        # Regular term
        self._consume()
        node = QueryNode(value=token)
        return node
    
    def evaluate(self, node: QueryNode, index) -> Set[str]:
        """
        Evaluate query tree against an index
        
        Args:
            node: Query tree node
            index: Index to search
            
        Returns:
            Set of matching document IDs
        """
        if node is None:
            return set()
        
        # Leaf node (term)
        if node.operator is None:
            # Simple term search
            results = index.search(node.value, top_k=10000)
            return {r['doc_id'] for r in results}
        
        # PHRASE operator
        if node.operator == QueryOperator.PHRASE:
            results = index.phrase_search(node.value)
            return {r['doc_id'] for r in results}
        
        # NOT operator
        if node.operator == QueryOperator.NOT:
            all_docs = set(index.documents.keys())
            excluded = self.evaluate(node.left, index)
            return all_docs - excluded
        
        # AND operator
        if node.operator == QueryOperator.AND:
            left_results = self.evaluate(node.left, index)
            right_results = self.evaluate(node.right, index)
            return left_results & right_results
        
        # OR operator
        if node.operator == QueryOperator.OR:
            left_results = self.evaluate(node.left, index)
            right_results = self.evaluate(node.right, index)
            return left_results | right_results
        
        return set()
