#!/bin/bash
set -e

BRANCHES=(
  "palette/accessible-input-hints-5330369807288098924"
  "sentinel-cli-injection-fix-17364729783174775444"
)

git checkout main
git pull origin main

for branch in "${BRANCHES[@]}"; do
  echo "=================================================="
  echo "Processing $branch..."
  
  if ! git checkout "$branch" 2>/dev/null; then
     git checkout -b "$branch" "origin/$branch"
  fi
  git pull origin "$branch"
  
  echo "Merging main into branch to get latest fixes..."
  git merge main --no-edit || {
    echo "FAILED: Merge conflict when merging main into $branch"
    exit 1
  }
  
  if [ -f "package.json" ]; then
    npm install
  fi
  
  git checkout main
  git pull origin main
  
  if ! git merge "$branch" --no-edit; then
    echo "FAILED: Merge conflict when merging $branch into main"
    exit 1
  fi
  
  git push origin main
  echo "SUCCESS: Merged and pushed $branch into main!"
done

echo "=================================================="
echo "Morning sync complete. All branches merged successfully."
