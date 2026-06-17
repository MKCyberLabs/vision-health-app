#!/bin/bash
# Simulates a POST request to the local API
echo "Testing Vision Health App upload..."
curl -X POST http://localhost:3000/analyze \
  -F "image=@sample-cake.jpg" \
  -F "weight=200g"
