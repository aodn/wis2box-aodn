#!/bin/bash

# This script downloads files from the wis2box-data directory of the aodn/wis2box-aodn GitHub repository.

REPO_OWNER="aodn"
REPO_NAME="wis2box-aodn"
REPO_BRANCH="main"
BASE_PATH="wis2-pipeline/wis2box-data"

REPO_URL="https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/$REPO_BRANCH"
API_URL="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/git/trees/$REPO_BRANCH?recursive=1"

BASE_DIR=$(dirname "$0")/..

# Get the list of files from the GitHub API using python to parse the JSON response.
FILES=$(curl -s "$API_URL" | python -c "import sys, json; data = json.load(sys.stdin); [print(item['path']) for item in data.get('tree', [])]" | grep "^$BASE_PATH/" | sed "s#^$BASE_PATH/##")

# Create directories and download files
for file in $FILES; do
    # Create local directory if it doesn't exist
    mkdir -p "$BASE_DIR/$(dirname "$file")"

    echo "Downloading $file..."
    curl -s -L -o "$BASE_DIR/$file" "$REPO_URL/$BASE_PATH/$file"
done

echo "Download complete."
