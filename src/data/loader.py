"""
Data loader module to handle loading and processing the transaction and user CSV files.
"""
import os
import pandas as pd
from typing import Dict, Optional

from src.core.config import TRANSACTIONS_FILE, USERS_FILE
from src.core.utils import ensure_directory_exists

class DataLoader:
    """
    Loads and caches transaction and user data from CSV files.
    """
    def __init__(self, transactions_path: str = TRANSACTIONS_FILE, users_path: str = USERS_FILE):
        """
        Initialize the DataLoader with paths to the CSV files.
        
        Args:
            transactions_path: Path to the transactions CSV file
            users_path: Path to the users CSV file
        """
        self.transactions_path = transactions_path
        self.users_path = users_path
        self._transactions_df = None
        self._users_df = None
        self._transactions_dict = None
        self._users_dict = None
        
        # Ensure data directory exists
        ensure_directory_exists(os.path.dirname(transactions_path))
        ensure_directory_exists(os.path.dirname(users_path))
        
    def load_transactions(self) -> pd.DataFrame:
        """
        Load transactions data from CSV.
        
        Returns:
            DataFrame containing transaction data
        """
        if self._transactions_df is None:
            if not os.path.exists(self.transactions_path):
                raise FileNotFoundError(f"Transactions file not found: {self.transactions_path}")
            
            self._transactions_df = pd.read_csv(self.transactions_path)
            
            # Clean column names (remove spaces, lowercase)
            self._transactions_df.columns = [
                col.strip().lower().replace(' ', '_').replace('(', '').replace(')', '').replace('$', '') 
                for col in self._transactions_df.columns
            ]
            
            # Rename specific columns if needed
            column_mapping = {
                'amount_': 'amount'  # This handles "amount ($)" becoming "amount_$" and then "amount"
            }
            self._transactions_df.rename(columns=column_mapping, inplace=True)
            
            # Ensure required columns exist after cleaning
            required_cols = ['id', 'amount', 'description']
            missing_cols = [col for col in required_cols if col not in self._transactions_df.columns]
            
            if missing_cols:
                # Try to identify and fix column name issues
                original_cols = self._transactions_df.columns.tolist()
                print(f"Warning: Missing columns {missing_cols}. Original columns: {original_cols}")
                
                # Special case for amount column with special characters
                if 'amount' in missing_cols and any('amount' in col.lower() for col in original_cols):
                    for col in original_cols:
                        if 'amount' in col.lower():
                            self._transactions_df.rename(columns={col: 'amount'}, inplace=True)
                            missing_cols.remove('amount')
                            print(f"Fixed: Renamed '{col}' to 'amount'")
                
                if missing_cols:
                    raise ValueError(f"Transactions CSV must contain columns: {required_cols}. Missing: {missing_cols}")
                    
            # Convert columns to appropriate types
            if 'amount' in self._transactions_df.columns:
                self._transactions_df['amount'] = pd.to_numeric(self._transactions_df['amount'], errors='coerce')
                
        return self._transactions_df
                    
    
    def load_users(self) -> pd.DataFrame:
        """
        Load users data from CSV.
        
        Returns:
            DataFrame containing user data
        """
        if self._users_df is None:
            if not os.path.exists(self.users_path):
                raise FileNotFoundError(f"Users file not found: {self.users_path}")
            
            # Add dtype specification to ensure name is loaded as string
            self._users_df = pd.read_csv(self.users_path, dtype={'name': str}, na_values=['', 'NA', 'N/A', 'null'])
            
            # Replace NaN values with empty strings
            self._users_df['name'] = self._users_df['name'].fillna('')
            
            # Clean column names (remove spaces, lowercase)
            self._users_df.columns = [col.strip().lower().replace(' ', '_') for col in self._users_df.columns]
            
            # Ensure required columns exist
            required_cols = ['id', 'name']
            if not all(col in self._users_df.columns for col in required_cols):
                raise ValueError(f"Users CSV must contain columns: {required_cols}")
                
        return self._users_df
    
    def get_transactions_dict(self) -> Dict:
        """
        Convert transactions DataFrame to a dictionary for easier lookup.
        
        Returns:
            Dictionary mapping transaction IDs to transaction details
        """
        if self._transactions_dict is None:
            df = self.load_transactions()
            self._transactions_dict = df.set_index('id').to_dict(orient='index')
        return self._transactions_dict
    
    def get_users_dict(self) -> Dict:
        """
        Convert users DataFrame to a dictionary for easier lookup.
        
        Returns:
            Dictionary mapping user IDs to user details
        """
        if self._users_dict is None:
            df = self.load_users()
            self._users_dict = df.set_index('id').to_dict(orient='index')
        return self._users_dict
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict]:
        """
        Get a transaction by its ID.
        
        Args:
            transaction_id: The ID of the transaction to retrieve
            
        Returns:
            Transaction data dictionary or None if not found
        """
        transactions = self.get_transactions_dict()
        return transactions.get(transaction_id)
    
    def get_all_transactions(self) -> Dict:
        """
        Get all transactions.
        
        Returns:
            Dictionary of all transactions
        """
        return self.get_transactions_dict()
    
    def get_all_users(self) -> Dict:
        """
        Get all users.
        
        Returns:
            Dictionary of all users
        """
        return self.get_users_dict()