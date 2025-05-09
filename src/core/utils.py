"""
Shared utility functions.
"""
import os, re

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure the specified directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory to check/create
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def preprocess_text(text: str) -> str:
    """
    Preprocess text by converting to lowercase, removing punctuation, and normalizing whitespace.
    
    Args:
        text: The text to preprocess
        
    Returns:
        Preprocessed text
    """
    # Handle None, NaN, or non-string values
    if text is None or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text