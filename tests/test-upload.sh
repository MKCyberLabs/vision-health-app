#!/bin/bash
# Integration test: Upload a sample image through the Node.js gateway (port 3000)
# and verify the full pipeline: Node.js -> Flask backend -> agy CLI -> response

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_FILE="${SCRIPT_DIR}/sample-cake.jpg"
API_URL="http://localhost:3000"

echo "=========================================="
echo "  Vision Health App - Integration Test"
echo "=========================================="
echo ""

# Check if sample image exists
if [ ! -f "$IMAGE_FILE" ]; then
    echo "ERROR: Sample image not found at $IMAGE_FILE"
    exit 1
fi

echo "[1/3] Checking Flask backend on port 5000..."
if curl -s --connect-timeout 5 http://172.17.0.1:5000/ > /dev/null 2>&1 || curl -s --connect-timeout 5 http://localhost:5000/ > /dev/null 2>&1; then
    echo "  ✅ Flask backend is reachable"
else
    echo "  ⚠️  Flask backend may not be running (this is OK if it returns 404 for /)"
fi

echo ""
echo "[2/3] Checking Node.js gateway on port 3000..."
if curl -s --connect-timeout 5 "${API_URL}/" > /dev/null 2>&1; then
    echo "  ✅ Node.js gateway is reachable"
else
    echo "  ❌ Node.js gateway is NOT reachable at ${API_URL}"
    echo "  Make sure 'docker compose up -d --build' was run"
    exit 1
fi

echo ""
echo "[3/3] Uploading test image to ${API_URL}/analyze..."
echo "  Image: ${IMAGE_FILE}"
echo "  Weight: 200g"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 320 \
    -X POST "${API_URL}/analyze" \
    -F "image=@${IMAGE_FILE}" \
    -F "weight=200g")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status: ${HTTP_CODE}"
echo ""
echo "Response Body:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "=========================================="
    echo "  ✅ Integration test PASSED!"
    echo "=========================================="
else
    echo "=========================================="
    echo "  ❌ Integration test FAILED (HTTP ${HTTP_CODE})"
    echo "=========================================="
    exit 1
fi
