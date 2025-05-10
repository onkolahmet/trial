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

print_header "Running Tests for Deel AI Python Engineer Challenge"

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated virtual environment."
else
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo "Virtual environment created and activated."
    
    # Install dependencies
    print_header "Installing dependencies"
    pip install --upgrade pip
    pip install -r requirements.txt
fi

print_header "Running unit tests"

# Run pytest with coverage report
python -m pytest tests/test_services.py -v

print_header "Running API tests"

# Run API tests
python -m pytest tests/test_apis.py -v

echo ""
echo "Tests completed successfully!"
