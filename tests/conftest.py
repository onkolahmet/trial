"""
Shared test fixtures for the test suite.
"""
import pytest
import os
import pandas as pd
from pathlib import Path

@pytest.fixture
def test_users_data():
    """Return a dictionary of test user data."""
    return {
        "user1": {"name": "John Smith"},
        "user2": {"name": "Emma Brown"},
        "user3": {"name": "Olivia Smith"},
        "user4": {"name": "Benjamin Lee"},
        "user5": {"name": "David Wood"},
        "user6": {"name": "Sarah Connor"}
    }

@pytest.fixture
def test_transactions_data():
    """Return a dictionary of test transaction data."""
    return {
        "tx1": {
            "description": "From John Smith for Deel, ref ABC123ACC//123456//CNTR",
            "amount": 100.00
        },
        "tx2": {
            "description": "Transfer from Emma Brown for Deel, ref DEF456ACC//789012//CNTR",
            "amount": 200.00
        },
        "tx3": {
            "description": "From David Wood for monthly service fee, ref GHI789ACC//345678//CNTR",
            "amount": 300.00
        },
        "tx4": {
            "description": "Received from Benjamin Lee for Deel invoice, ref JKL012ACC//901234//CNTR",
            "amount": 400.00
        }
    }

@pytest.fixture
def sample_csv_path(tmp_path):
    """Create temporary CSV files for testing."""
    # Create data directory in the temporary path
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create users CSV
    users_df = pd.DataFrame([
        {"id": "user1", "name": "John Smith"},
        {"id": "user2", "name": "Emma Brown"},
        {"id": "user3", "name": "Olivia Smith"},
        {"id": "user4", "name": "Benjamin Lee"},
        {"id": "user5", "name": "David Wood"},
        {"id": "user6", "name": "Sarah Connor"}
    ])
    users_path = data_dir / "users.csv"
    users_df.to_csv(users_path, index=False)
    
    # Create transactions CSV
    transactions_df = pd.DataFrame([
        {"id": "tx1", "amount ($)": 100.00, "description": "From John Smith for Deel, ref ABC123ACC//123456//CNTR"},
        {"id": "tx2", "amount ($)": 200.00, "description": "Transfer from Emma Brown for Deel, ref DEF456ACC//789012//CNTR"},
        {"id": "tx3", "amount ($)": 300.00, "description": "From David Wood for monthly service fee, ref GHI789ACC//345678//CNTR"},
        {"id": "tx4", "amount ($)": 400.00, "description": "Received from Benjamin Lee for Deel invoice, ref JKL012ACC//901234//CNTR"}
    ])
    transactions_path = data_dir / "transactions.csv"
    transactions_df.to_csv(transactions_path, index=False)
    
    return {
        "data_dir": str(data_dir),
        "users_path": str(users_path),
        "transactions_path": str(transactions_path)
    }