"""
Service for semantic search operations.
"""
from typing import Dict
from fastapi import HTTPException

from src.data.loader import DataLoader
from src.services.semantic_search import SemanticSearchEngine

class SearchService:
    """Service for semantic search operations."""
    
    def __init__(self, data_loader: DataLoader, semantic_engine: SemanticSearchEngine):
        self.data_loader = data_loader
        self.semantic_engine = semantic_engine
    
    def semantic_search(
        self,
        query: str,
        threshold: float,
        preprocess: bool,
        include_description: bool,
        limit: int
    ) -> Dict:
        """
        Find transactions with descriptions semantically similar to the query.
        
        Args:
            query: The search query string
            threshold: Minimum similarity threshold (0-1)
            preprocess: Whether to preprocess text for better semantic matching
            include_description: Whether to include descriptions in results
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with transactions and token count
        """
        if not query:
            raise HTTPException(status_code=400, detail="Query string cannot be empty")
        
        # Get all transactions
        transactions = self.data_loader.get_all_transactions()
        
        # Find similar transactions
        matches, token_count = self.semantic_engine.find_similar_transactions(
            query=query,
            transactions=transactions,
            threshold=threshold,
            include_description=include_description,
            preprocess=preprocess,
            limit=limit
        )
        
        # Process matches to ensure description is only included when requested
        processed_matches = []
        for match in matches:
            # Start with required fields
            item = {"id": match["id"], "embedding": match["embedding"]}
            
            # Add description only if requested and available
            if include_description and "description" in match:
                item["description"] = match["description"]
                
            processed_matches.append(item)
        
        return {
            "transactions": processed_matches,
            "total_number_of_tokens_used": token_count
        }