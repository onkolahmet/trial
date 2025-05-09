"""
API endpoint definitions.
"""
from fastapi import APIRouter, Query, Path
from typing import List

from src.api.models import MatchResponse, SemanticResponse, TransactionUserMatchResponse, TransactionItem
from src.data.loader import DataLoader
from src.services.matching import UserMatcher
from src.services.semantic_search import SemanticSearchEngine
from src.core.config import DEFAULT_MATCH_THRESHOLD, DEFAULT_SIMILARITY_THRESHOLD

# Import our new services
from src.api.services.transaction_service import TransactionService
from src.api.services.search_service import SearchService

# Initialize router
router = APIRouter()

# Initialize components
data_loader = DataLoader()
user_matcher = UserMatcher(data_loader.get_all_users())
semantic_engine = SemanticSearchEngine()

# Initialize services
transaction_service = TransactionService(data_loader, user_matcher)
search_service = SearchService(data_loader, semantic_engine)

@router.post("/transactions/{transaction_id}", tags=["transactions"], response_model=MatchResponse)
async def transactions(
    transaction_id: str = Path(..., description="The ID of the transaction to match"),
    threshold: int = Query(DEFAULT_MATCH_THRESHOLD, ge=0, le=100, description="Minimum match score threshold (0-100)")
):
    """
    Match a transaction to potential users based on the transaction description.

    **Args**:
    - `transaction_id`: The ID of the transaction to match  
    - `threshold`: Minimum match score threshold (0-100)  

    **Returns**:
    - `MatchResponse`: Matching users and match metrics
    """
    result = transaction_service.match_transaction(transaction_id, threshold)
    return MatchResponse(**result)

@router.post(
    "/transactions/semantic_search/{query}", 
    response_model=SemanticResponse,
    tags=["transactions"],
    response_model_exclude_none=True
)
async def semantic_search(
    query: str = Path(..., description="The search query string"),
    threshold: float = Query(DEFAULT_SIMILARITY_THRESHOLD, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    preprocess: bool = Query(True, description="Whether to preprocess text for better semantic matching"),
    include_description: bool = Query(True, description="Include transaction descriptions in results"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return")
):
    """
    Find transactions with descriptions semantically similar to the query.

    **Args**:
    - `query`: The search query string  
    - `threshold`: Minimum similarity threshold (0-1)  
    - `preprocess`: Whether to preprocess text for better semantic matching  
    - `include_description`: Whether to include descriptions in results  
    - `limit`: Maximum number of results to return  

    **Returns**:
    - `SemanticResponse`: Matching transactions and token count
    """
    result = search_service.semantic_search(
        query, threshold, preprocess, include_description, limit
    )
    
    # Convert to Pydantic models
    transaction_items = [TransactionItem(**item) for item in result["transactions"]]
    
    return SemanticResponse(
        transactions=transaction_items,
        total_number_of_tokens_used=result["total_number_of_tokens_used"]
    )

@router.get("/transactions/transactions_with_users", tags=["transactions"], response_model=List[TransactionUserMatchResponse])
async def transactions_with_users(
    threshold: int = Query(DEFAULT_MATCH_THRESHOLD, ge=0, le=100, description="Minimum match score threshold (0-100)")
):
    """
    Get transactions with their possible user matches.

    **Args**:
    - `threshold`: Minimum match score threshold (0-100)  

    **Returns**:
    - `List`: Transactions with their description and possible matching users
    """
    results = transaction_service.get_transactions_with_users(threshold)
    return [TransactionUserMatchResponse(**result) for result in results]
