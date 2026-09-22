#!/bin/bash

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Move to the project root
cd "$SCRIPT_DIR"

# Read Python path
PYTHON_PATH=$(cat python_path.txt)

echo "Starting Lake Kivu CTD database interface..."
echo "Python: $PYTHON_PATH"
echo

"$PYTHON_PATH" -m scripts.database_interface

echo
echo "Database interface closed."
read -p "Press Enter to close..."
