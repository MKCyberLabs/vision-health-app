#!/bin/bash
set -e

# fetch to be sure
git fetch --all

# list of branches
branches=$(git branch -r | grep -v 'origin/HEAD' | grep -v 'origin/main' | awk -F'origin/' '{print $2}' | tr -d ' ')

for b in $branches; do
    echo "Processing branch: $b"
    
    # checkout the branch
    git checkout "$b"
    
    # pre-merge testing
    node -c index.js
    
    # update with main
    if ! git merge main --no-edit; then
        echo "Merge conflict in $b with main!"
        exit 1
    fi
    
    # test again
    node -c index.js
    
    # switch to main and merge
    git checkout main
    git merge "$b" --no-edit
done

echo "SUCCESS"
