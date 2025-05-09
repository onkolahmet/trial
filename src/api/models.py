"""
Pydantic models for API request and response schemas.
"""
from typing import List, Optional
from pydantic import BaseModel

class MatchUserItem(BaseModel):
    """Schema for a matched user item."""
    id: str
    match_metric: float

class MatchResponse(BaseModel):
    """Schema for the transaction-user matching response."""
    users: List[MatchUserItem]
    total_number_of_matches: int

class TransactionItem(BaseModel):
    """Schema for a transaction item in the semantic search response."""
    id: str
    embedding: float
    description: Optional[str] = None

    # For Pydantic V2
    model_config = {
        "populate_by_name": True
    }

class SemanticResponse(BaseModel):
    """Schema for the semantic search response."""
    transactions: List[TransactionItem]
    total_number_of_tokens_used: int

class MatchUserItem(BaseModel):
    """Schema for a matched user item."""
    id: str
    name: Optional[str] = None
    match_metric: float

class TransactionUserMatchResponse(BaseModel):
    """Schema for a transaction with possible user matches."""
    transaction_id: str
    description: str
    amount: Optional[float] = None
    possible_users: List[MatchUserItem]
    total_matches: int