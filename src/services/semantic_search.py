"""
Semantic search module that implements embedding-based similarity for Task 2.
"""
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re, unicodedata, hashlib

from src.core.config import DEFAULT_EMBEDDING_MODEL

class SemanticSearchEngine:
    """Engine for semantic similarity search using embeddings."""
    
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        """Initialize the semantic search engine with a pre-trained model."""
        self.model = SentenceTransformer(model_name)
        self.cached_embeddings = {}
        self.cached_token_counts = {}
        self.debug_mode = False
        
        # Precompile regex patterns for better performance
        self.whitespace_pattern = re.compile(r'\s{2,}')
        self.party_pattern = re.compile(r'(?:from|to|cc)\s+([^,]+?)(?:\s+for|\s*,|\s+ref)', re.IGNORECASE)
        self.action_pattern = re.compile(r'\b(transfer|payment|refund|deposit|withdrawal|received)\s+(?:from|to|for)', re.IGNORECASE)
        self.acc_pattern = re.compile(r'ACC//[^/]+//CNTR')
        self.ref_pattern = re.compile(r'ref\s+[A-Za-z0-9]{5,}')
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing accents, standardizing case, etc."""
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase and normalize unicode characters
        text = text.lower()
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        
        # Normalize whitespace
        return self.whitespace_pattern.sub(' ', text).strip()
    
    def _preprocess_for_embedding(self, text: str) -> str:
        """Preprocess text for better embedding quality."""
        if not text:
            return ""
        
        # Extract key semantic parts
        semantic_parts = []
        
        # Check for financial terms
        financial_terms = ['debit', 'credit', 'transfer', 'payment', 'received', 
                          'request', 'deposit', 'withdrawal', 'refund', 'charge']
        
        semantic_parts.extend(term for term in financial_terms 
                             if re.search(r'\b' + term + r'\b', text, re.IGNORECASE))
        
        # Extract names/parties
        semantic_parts.extend(match.strip() for match in self.party_pattern.findall(text) 
                             if match.strip())
        
        # Extract action descriptions
        semantic_parts.extend(match.strip() for match in self.action_pattern.findall(text) 
                             if match.strip())
        
        # If no semantic parts found, do basic cleaning
        if not semantic_parts:
            processed_text = self.acc_pattern.sub(' ', text)
            processed_text = self.ref_pattern.sub(' ', processed_text)
            return processed_text.strip()
        
        # Join semantic parts
        return " ".join(semantic_parts)
    
    def get_embedding(self, text: str, preprocess: bool = True) -> Tuple[np.ndarray, int]:
        """Generate an embedding for the given text."""
        if not text:
            return np.zeros((384,)), 0  # Return zero vector for empty text
        
        # Create a unique cache key including preprocessing settings
        cache_key = f"{text}__preprocess" if preprocess else text
        hashed_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Check cache first
        if hashed_key in self.cached_embeddings:
            return self.cached_embeddings[hashed_key], self.cached_token_counts[hashed_key]
        
        # Process text and generate embedding
        processed_text = self._preprocess_for_embedding(text) if preprocess else text
        
        if self.debug_mode:
            print(f"Original: {text}\nPreprocessed: {processed_text}\n{'-' * 50}")
        
        # Get token count and embedding
        tokens = self.model.tokenizer.encode(processed_text, add_special_tokens=True)
        embedding = self.model.encode(processed_text)
        
        # Cache results
        self.cached_embeddings[hashed_key] = embedding
        self.cached_token_counts[hashed_key] = len(tokens)
        
        return embedding, len(tokens)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute the cosine similarity between two embeddings."""
        # Reshape embeddings and compute cosine similarity
        return float(cosine_similarity(
            embedding1.reshape(1, -1), 
            embedding2.reshape(1, -1)
        )[0][0])
    
    def find_similar_transactions(self, 
            query: str, 
            transactions: Dict, 
            threshold: float = 0.4,
            include_description: bool = True,
            preprocess: bool = True,
            limit: int = None) -> Tuple[List[Dict], int]:
        """Find transactions with descriptions semantically similar to the query."""
        if not query:
            return [], 0
        
        # Get query embedding and token count
        processed_query = self._preprocess_for_embedding(query) if preprocess else query
        query_tokens = self.model.tokenizer.encode(processed_query, add_special_tokens=True)
        query_embedding, _ = self.get_embedding(query, preprocess=preprocess)
        query_token_count = len(query_tokens)
        
        # Find matching transactions
        matches = []
        for txn_id, txn_data in transactions.items():
            description = txn_data.get('description', '')
            if not description:
                continue
            
            # Get embedding and compute similarity
            txn_embedding, _ = self.get_embedding(description, preprocess=preprocess)
            similarity = self.compute_similarity(query_embedding, txn_embedding)
            
            # Add to matches if above threshold
            if similarity >= threshold:
                result = {
                    'id': txn_id,
                    'embedding': round(float(similarity), 4)
                }
                
                if include_description:
                    result['description'] = description
                    if 'amount' in txn_data:
                        result['amount'] = txn_data['amount']
                
                matches.append(result)
        
        # Sort and limit results
        matches.sort(key=lambda x: x['embedding'], reverse=True)
        if limit is not None:
            matches = matches[:limit]
        
        # Calculate token count for matched transactions only
        matched_txn_token_count = 0
        if matches:
            for match in matches:
                txn_id = match['id']
                description = transactions[txn_id].get('description', '')
                processed_description = self._preprocess_for_embedding(description) if preprocess else description
                desc_tokens = self.model.tokenizer.encode(processed_description, add_special_tokens=True)
                matched_txn_token_count += len(desc_tokens)
        
        total_token_count = query_token_count + matched_txn_token_count
        
        return matches, total_token_count
