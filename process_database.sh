#!/bin/bash

# Read Python path from file
PYTHON_PATH=$(cat python_path.txt)

echo "Starting data processing"
echo "Please wait until the Processing Options window opens..."

"$PYTHON_PATH" scripts/main_ctd_database.py

echo "Processing finished."
read -p "Press Enter to close..."
