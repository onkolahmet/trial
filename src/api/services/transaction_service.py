"""
Service for transaction-related operations.
"""
from typing import List, Dict
from fastapi import HTTPException

from src.data.loader import DataLoader
from src.services.matching import UserMatcher

class TransactionService:
    """Service for transaction operations."""
    
    def __init__(self, data_loader: DataLoader, user_matcher: UserMatcher):
        self.data_loader = data_loader
        self.user_matcher = user_matcher
    
    def match_transaction(self, transaction_id: str, threshold: int) -> Dict:
        """
        Match a transaction to potential users based on the transaction description.
        
        Args:
            transaction_id: The ID of the transaction to match
            threshold: Minimum match score threshold (0-100)
            
        Returns:
            Dictionary with users and match count
        """
        # Get the transaction
        transaction = self.data_loader.get_transaction_by_id(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail=f"Transaction with ID {transaction_id} not found")
            
        # Extract the description
        description = transaction.get('description', '')
        if not description:
            return {"users": [], "total_number_of_matches": 0}
            
        # Find matching users
        matches = self.user_matcher.find_matching_users(description, threshold)
        
        # Return result
        return {
            "users": matches,
            "total_number_of_matches": len(matches)
        }
    
    def get_transactions_with_users(self, threshold: int) -> List[Dict]:
        """
        Get transactions with their possible user matches.
        
        Args:
            threshold: Minimum match score threshold (0-100)
            
        Returns:
            List of transactions with their description and possible matching users
        """
        # Get all transactions and users
        transactions = self.data_loader.get_all_transactions()
        all_users = self.data_loader.get_all_users()
        
        # Limit the number of transactions to process
        transaction_ids = list(transactions.keys())
        
        # Initialize result list
        results = []
        
        # Process each transaction
        for txn_id in transaction_ids:
            transaction = transactions[txn_id]
            description = transaction.get('description', '')
            
            # Skip transactions with no description
            if not description:
                continue
                
            # Find matching users for this transaction
            matching_users = self.user_matcher.find_matching_users(description, threshold)
            
            # Add user names to the matching results
            for user_match in matching_users:
                user_id = user_match['id']
                user_info = all_users.get(user_id, {})
                user_match['name'] = user_info.get('name', '')
            
            # Add to results
            results.append({
                'transaction_id': txn_id,
                'description': description,
                'amount': transaction.get('amount', 0),
                'possible_users': matching_users,
                'total_matches': len(matching_users)
            })
        
        return results