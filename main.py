"""
Main entry point for the Deel AI Python Engineer Challenge application.
"""
import os
import sys
from pathlib import Path

# Make sure the src directory is in the Python path
base_dir = Path(__file__).resolve().parent
sys.path.append(str(base_dir))

def setup_application():
    """
    Set up the application environment.
    
    Creates necessary directories and performs initial setup.
    """
    # Get the base directory
    base_dir = Path(__file__).resolve().parent
    
    # Ensure data directory exists
    data_dir = os.path.join(base_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created data directory: {data_dir}")
    
    # Check if CSV files exist
    transactions_file = os.path.join(data_dir, "transactions.csv")
    users_file = os.path.join(data_dir, "users.csv")
    
    if not os.path.exists(transactions_file):
        print(f"Warning: Transactions file not found at {transactions_file}")
        print("Please copy transactions.csv to the data directory.")
    else:
        # Check format of transactions file
        try:
            import pandas as pd
            df = pd.read_csv(transactions_file)
            # Print column names for debugging
            print(f"Info: Transactions file has columns: {list(df.columns)}")
            
            # Check for required columns with flexible matching
            has_id = any(col == 'id' or col.lower() == 'id' for col in df.columns)
            has_amount = any('amount' in col.lower() for col in df.columns)
            has_description = any(col == 'description' or col.lower() == 'description' for col in df.columns)
            
            if not has_id:
                print("Warning: Transactions file is missing 'id' column")
            if not has_amount:
                print("Warning: Transactions file is missing 'amount' or similar column")
            if not has_description:
                print("Warning: Transactions file is missing 'description' column")
        except Exception as e:
            print(f"Warning: Error checking transactions file: {e}")
    
    if not os.path.exists(users_file):
        print(f"Warning: Users file not found at {users_file}")
        print("Please copy users.csv to the data directory.")
    else:
        # Check format of users file
        try:
            import pandas as pd
            df = pd.read_csv(users_file)
            # Print column names for debugging
            print(f"Info: Users file has columns: {list(df.columns)}")
            
            has_id = any(col == 'id' or col.lower() == 'id' for col in df.columns)
            has_name = any(col == 'name' or col.lower() == 'name' for col in df.columns)
            
            if not has_id:
                print("Warning: Users file is missing 'id' column")
            if not has_name:
                print("Warning: Users file is missing 'name' column")
            elif 'name' in df.columns:
                # Check for missing names
                missing_names = df['name'].isna().sum()
                if missing_names > 0:
                    print(f"Warning: Users file contains {missing_names} rows with missing names")
        except Exception as e:
            print(f"Warning: Error checking users file: {e}")
    
    print(f"Application setup complete.")
    print(f"Data directory: {data_dir}")

if __name__ == "__main__":
    setup_application()
    
    # Import here to ensure paths are set up correctly
    from src.api.app import app
    import uvicorn
    from src.core.config import HOST, PORT
    
    print(f"Starting application on {HOST}:{PORT}")
    print(f"API will be available at http://localhost:{PORT}")
    uvicorn.run("src.api.app:app", host=HOST, port=PORT, reload=True)