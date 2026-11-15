#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "Running HelpdeskFlow Smoke Test Suite"
echo "========================================="

BASE_URL="${API_BASE_URL:-http://localhost:8100}"

echo "1. Checking API liveness at ${BASE_URL}/health..."
HEALTH=$(curl -s -f "${BASE_URL}/health")
echo "Liveness response: ${HEALTH}"

echo "2. Checking API readiness at ${BASE_URL}/ready..."
READY=$(curl -s -f "${BASE_URL}/ready")
echo "Readiness response: ${READY}"

echo "Smoke test passed successfully!"
