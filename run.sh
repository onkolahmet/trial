#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print section header
print_header() {
    echo -e "\n${GREEN}$1${NC}"
    echo "========================================"
}

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

print_header "Setting up Deel AI Python Engineer Challenge"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    echo -e "${YELLOW}Python 3.8 or higher is required. Found Python $PYTHON_VERSION.${NC}"
    exit 1
fi

print_header "Creating virtual environment"

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
source venv/bin/activate

print_header "Installing dependencies"

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

print_header "Setting up data directory"

# Create data directory if it doesn't exist
mkdir -p data

# # Check if CSV files exist in the current directory
# if [ -f "transactions.csv" ] && [ ! -f "data/transactions.csv" ]; then
#     echo "Copying transactions.csv to data directory..."
#     cp transactions.csv data/
# fi

# if [ -f "users.csv" ] && [ ! -f "data/users.csv" ]; then
#     echo "Copying users.csv to data directory..."
#     cp users.csv data/
# fi

# # Check if CSV files exist in the data directory
# if [ ! -f "data/transactions.csv" ]; then
#     echo -e "${YELLOW}Warning: transactions.csv not found in the data directory.${NC}"
#     echo "Please place transactions.csv in the data directory before running the application."
# fi

# if [ ! -f "data/users.csv" ]; then
#     echo -e "${YELLOW}Warning: users.csv not found in the data directory.${NC}"
#     echo "Please place users.csv in the data directory before running the application."
# fi

print_header "Starting the application"
echo "The API will be available at http://localhost:8000"
echo "Press Ctrl+C to stop the server."
echo ""

# Run the application
python main.py