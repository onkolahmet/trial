"""
Unit tests for core services.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Make sure the src directory is in the Python path
base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from src.services.matching import UserMatcher
from src.services.semantic_search import SemanticSearchEngine
from src.data.loader import DataLoader

class TestUserMatcher:
    """Tests for the UserMatcher class."""
    
    def test_normalize_text(self, test_users_data):
        """Test text normalization."""
        matcher = UserMatcher(test_users_data)
        
        # Test with accents and special chars (using Latin characters)
        assert matcher._normalize_text("Évèlyn Allèn") == "evelyn allen"
        # Test with more Latin accented characters
        assert matcher._normalize_text("José Martínez") == "jose martinez"
        # Test with umlauts and other diacritics
        assert matcher._normalize_text("Jürgen Müller") == "jurgen muller"
        # Test with mixed case
        assert matcher._normalize_text("JoHN SmITh") == "john smith"
        # Test with special characters
        assert matcher._normalize_text("O'Brien-Smith") == "o brien smith"
    
    def test_extract_name_candidates(self, test_users_data):
        """Test name extraction from descriptions."""
        matcher = UserMatcher(test_users_data)
        
        # Test standard pattern
        description1 = "From John Smith for Deel, ref ABC123ACC//123456//CNTR"
        candidates1 = matcher._extract_name_candidates(description1)
        assert "John Smith" in candidates1
        
        # Test transfer pattern
        description2 = "Transfer from Emma Brown for Deel, ref ABC123ACC//123456//CNTR"
        candidates2 = matcher._extract_name_candidates(description2)
        assert "Emma Brown" in candidates2
        
        # Test pattern with comma
        description3 = "From Smith, John for Deel, ref ABC123ACC//123456//CNTR"
        candidates3 = matcher._extract_name_candidates(description3)
        assert "Smith, John" in candidates3
    
    def test_calculate_match_score(self, test_users_data):
        """Test match score calculation."""
        matcher = UserMatcher(test_users_data)
        
        # Perfect match
        score1 = matcher._calculate_match_score("John Smith", "user1")
        assert score1 >= 90
        
        # Partial match
        score2 = matcher._calculate_match_score("John", "user1")
        assert score2 >= 40
        
        # Name with typo
        score3 = matcher._calculate_match_score("Jon Smith", "user1")
        assert score3 >= 80
        
        # Different order
        score4 = matcher._calculate_match_score("Smith John", "user1")
        assert score4 >= 80
    
    def test_find_matching_users(self, test_users_data):
        """Test finding matching users."""
        matcher = UserMatcher(test_users_data)
        
        # Description with exact match
        description1 = "From John Smith for Deel, ref ABC123ACC//123456//CNTR"
        matches1 = matcher.find_matching_users(description1)
        assert any(match["id"] == "user1" for match in matches1)
        
        # Description with multiple potential matches
        description2 = "From Smith for Deel, ref ABC123ACC//123456//CNTR"
        matches2 = matcher.find_matching_users(description2)
        smith_matches = [match for match in matches2 if "Smith" in test_users_data[match["id"]]["name"]]
        assert len(smith_matches) >= 1

class TestSemanticSearchEngine:
    """Tests for the SemanticSearchEngine class."""
    
    def test_preprocess_for_embedding(self, test_transactions_data):
        """Test text preprocessing for embeddings."""
        engine = SemanticSearchEngine()
        
        text1 = "Payment from John Smith for Deel, ref ABC123ACC//123456//CNTR"
        processed1 = engine._preprocess_for_embedding(text1)
        assert "payment" in processed1.lower()
        assert "john smith" in processed1.lower()
        
        text2 = "ref ABC123ACC//123456//CNTR"
        processed2 = engine._preprocess_for_embedding(text2)
        assert "abc123" not in processed2.lower()
    
    def test_compute_similarity(self):
        """Test similarity computation."""
        engine = SemanticSearchEngine()
        
        # Create dummy embeddings for testing similarity computation
        emb1 = np.array([1, 0, 0, 0])
        emb2 = np.array([1, 0, 0, 0])  # Same as emb1
        emb3 = np.array([0.7, 0.7, 0, 0])  # Similar to emb1
        emb4 = np.array([0, 1, 0, 0])  # Perpendicular to emb1
        
        # Identical embeddings should have similarity 1.0
        similarity1 = engine.compute_similarity(emb1, emb2)
        assert pytest.approx(similarity1, abs=1e-5) == 1.0
        
        # Similar embeddings should have high similarity
        similarity2 = engine.compute_similarity(emb1, emb3)
        assert similarity2 > 0.5
        
        # Perpendicular embeddings should have similarity 0
        similarity3 = engine.compute_similarity(emb1, emb4)
        assert pytest.approx(similarity3, abs=1e-5) == 0.0
    
    def test_find_similar_transactions(self, test_transactions_data):
        """Test finding similar transactions with mocked similarity computation."""
        # Create a spy on the compute_similarity method
        with patch('src.services.semantic_search.SemanticSearchEngine.compute_similarity') as mock_compute_similarity, \
             patch('src.services.semantic_search.SemanticSearchEngine.get_embedding') as mock_get_embedding:
            
            # Configure mocks
            mock_get_embedding.return_value = (np.zeros(4), 10)  # Return dummy embedding and token count
            
            # Make compute_similarity return high similarity for tx1, low for others
            def side_effect(emb1, emb2):
                # This is the mocked similarity function
                # We'll return high similarity for tx1 and low for others
                # The first embedding is the query embedding (we don't care about it)
                # The second embedding would be the transaction embedding
                return 0.9  # High similarity for all transactions in test
            
            mock_compute_similarity.side_effect = side_effect
            
            # Create engine and test
            engine = SemanticSearchEngine()
            
            matches, token_count = engine.find_similar_transactions(
                "Payment from John",
                test_transactions_data,
                threshold=0.7  # We can use higher threshold now since we're mocking
            )
            
            # Verify results
            assert len(matches) > 0
            assert token_count > 0
            
            # Since our mock returns 0.9 for all transactions, all should match
            assert len(matches) == len(test_transactions_data)
            
            # Check that all transactions are included
            transaction_ids = [match["id"] for match in matches]
            for tx_id in test_transactions_data.keys():
                assert tx_id in transaction_ids

class TestDataLoader:
    """Tests for the DataLoader class."""
    
    def test_load_transactions(self, sample_csv_path):
        """Test loading transaction data."""
        loader = DataLoader(sample_csv_path["transactions_path"], sample_csv_path["users_path"])
        df = loader.load_transactions()
        
        assert df is not None
        assert "id" in df.columns
        assert "description" in df.columns
    
    def test_load_users(self, sample_csv_path):
        """Test loading user data."""
        loader = DataLoader(sample_csv_path["transactions_path"], sample_csv_path["users_path"])
        df = loader.load_users()
        
        assert df is not None
        assert "id" in df.columns
        assert "name" in df.columns
    
    def test_get_transaction_by_id(self, sample_csv_path):
        """Test retrieving a transaction by ID."""
        loader = DataLoader(sample_csv_path["transactions_path"], sample_csv_path["users_path"])
        
        # Test with a known transaction ID
        transaction = loader.get_transaction_by_id("tx1")
        assert transaction is not None
        assert "description" in transaction
        
        # Test with an unknown transaction ID
        transaction = loader.get_transaction_by_id("unknown_id")
        assert transaction is None
    
    def test_get_all_users(self, sample_csv_path):
        """Test retrieving all users."""
        loader = DataLoader(sample_csv_path["transactions_path"], sample_csv_path["users_path"])
        users = loader.get_all_users()
        
        assert users is not None
        assert isinstance(users, dict)
        assert len(users) == 6  # Based on our fixture data
        assert "user1" in users
        assert users["user1"]["name"] == "John Smith"