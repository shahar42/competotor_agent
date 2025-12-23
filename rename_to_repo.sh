#!/bin/bash

# Get current directory name
CURRENT_DIR=$(basename "$PWD")

# Get repo name from git remote (strip .git extension)
REPO_NAME=$(git remote get-url origin | sed 's/.*\///' | sed 's/\.git$//')

echo "Current directory: $CURRENT_DIR"
echo "Repository name: $REPO_NAME"

if [ "$CURRENT_DIR" = "$REPO_NAME" ]; then
    echo "Directory already matches repo name. Nothing to do."
    exit 0
fi

# Move to parent and rename
cd ..
mv "$CURRENT_DIR" "$REPO_NAME"

echo "Renamed $CURRENT_DIR -> $REPO_NAME"
echo "New path: $(pwd)/$REPO_NAME"
