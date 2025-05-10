"""
Integration tests for API endpoints.
"""
import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock

# Make sure the src directory is in the Python path
base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

# We need to patch the dependencies before importing app
import src.api.endpoints
from src.api.app import app

class TestAPI:
    """Integration tests for API endpoints."""
    
    def test_root_redirects_to_docs(self):
        """Test that the root path redirects to docs."""
        client = TestClient(app)
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"
    
    def test_transaction_matching_endpoint(self):
        """Test the transaction-user matching endpoint."""
        # Create a mock transaction service
        with patch('src.api.endpoints.transaction_service') as mock_service:
            # Configure the mock to return a predefined response
            mock_service.match_transaction.return_value = {
                "users": [
                    {"id": "user1", "match_metric": 95.0},
                    {"id": "user3", "match_metric": 85.0}
                ],
                "total_number_of_matches": 2
            }
            
            # Create a test client
            client = TestClient(app)
            
            # Test with a valid transaction ID
            response = client.post("/transactions/tx1")
            assert response.status_code == 200
            
            # Validate response format
            data = response.json()
            assert "users" in data
            assert "total_number_of_matches" in data
            assert isinstance(data["users"], list)
            assert len(data["users"]) == 2
            
            # Ensure matches are sorted by relevance
            assert data["users"][0]["match_metric"] > data["users"][1]["match_metric"]
            
            # Verify the mock was called correctly
            mock_service.match_transaction.assert_called_once_with("tx1", 60)
    
    def test_transaction_matching_with_invalid_id(self):
        """Test transaction matching with an invalid ID."""
        with patch('src.api.endpoints.transaction_service') as mock_service:
            # Set up our mock to raise an HTTPException for an invalid ID
            mock_service.match_transaction.side_effect = HTTPException(status_code=404, detail="Transaction not found")
            
            # Create a test client
            client = TestClient(app)
            
            # Make the request
            response = client.post("/transactions/nonexistent_id")
            assert response.status_code == 404
            
            # Verify the error message
            data = response.json()
            assert "detail" in data
            assert "Transaction not found" in data["detail"]
    
    def test_semantic_search_endpoint(self):
        """Test the semantic search endpoint."""
        with patch('src.api.endpoints.search_service') as mock_service:
            # Configure the mock to return a predefined response
            mock_service.semantic_search.return_value = {
                "transactions": [
                    {"id": "tx1", "embedding": 0.95, "description": "From John Smith for Deel, ref ABC123ACC//123456//CNTR"},
                    {"id": "tx2", "embedding": 0.85, "description": "Transfer from Emma Brown for Deel, ref DEF456ACC//789012//CNTR"}
                ],
                "total_number_of_tokens_used": 42
            }
            
            # Create a test client
            client = TestClient(app)
            
            # Test with a valid search query
            response = client.post("/transactions/semantic_search/payment")
            assert response.status_code == 200
            
            # Validate response format
            data = response.json()
            assert "transactions" in data
            assert "total_number_of_tokens_used" in data
            assert isinstance(data["transactions"], list)
            assert len(data["transactions"]) == 2  # Based on our mock
            
            # Ensure results are sorted by relevance
            assert data["transactions"][0]["embedding"] > data["transactions"][1]["embedding"]
            
            # Verify the mock was called correctly
            mock_service.semantic_search.assert_called_once()
    
    def test_semantic_search_with_empty_query(self):
        """Test semantic search with an empty query."""
        # This should be caught by the router and return a 404 or 422
        client = TestClient(app)
        response = client.post("/transactions/semantic_search/")
        assert response.status_code in [404, 422]  # Either not found or validation error
    
    def test_transactions_with_users_endpoint(self):
        """Test the transactions with users endpoint."""
        with patch('src.api.endpoints.transaction_service') as mock_service:
            # Configure the mock for transaction service
            mock_service.get_transactions_with_users.return_value = [
                {
                    'transaction_id': 'tx1',
                    'description': 'From John Smith for Deel, ref ABC123ACC//123456//CNTR',
                    'amount': 100.0,
                    'possible_users': [
                        {'id': 'user1', 'name': 'John Smith', 'match_metric': 95.0},
                        {'id': 'user3', 'name': 'Olivia Smith', 'match_metric': 85.0}
                    ],
                    'total_matches': 2
                }
            ]
            
            # Create a test client
            client = TestClient(app)
            
            # Make the request
            response = client.get("/transactions/transactions_with_users")
            assert response.status_code == 200
            
            # Validate response format
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            
            # Validate entry format
            first_entry = data[0]
            assert "transaction_id" in first_entry
            assert "description" in first_entry
            assert "possible_users" in first_entry
            assert "total_matches" in first_entry
            assert isinstance(first_entry["possible_users"], list)
            
            # Check if users are sorted by relevance
            assert first_entry["possible_users"][0]["match_metric"] > first_entry["possible_users"][1]["match_metric"]
            
            # Verify the mock was called correctly
            mock_service.get_transactions_with_users.assert_called_once_with(60)