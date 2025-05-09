"""
Application configuration settings.
"""
import os
from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Data paths
DATA_DIR = os.path.join(BASE_DIR, "data")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.csv")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")

# API settings
API_TITLE = "Deel AI Python Engineer Challenge"
API_DESCRIPTION = "API for transaction-user matching and semantic search"
API_VERSION = "1.0.0"
HOST = "0.0.0.0"
PORT = 8000

# Model settings
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_MATCH_THRESHOLD = 60  # For user matching
DEFAULT_SIMILARITY_THRESHOLD = 0.4  # For semantic search