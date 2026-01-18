#!/bin/bash
#
# Mini-ERP UAT Testing Script
# Tests login flow and all migrated services
#

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
LEGACY_URL="${LEGACY_URL:-http://localhost:8001}"

echo "============================================"
echo "  Mini-ERP UAT Testing Script"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; }
info() { echo -e "${YELLOW}→ $1${NC}"; }

# Step 1: Get login token from legacy backend (has DB connection)
echo "========== STEP 1: LOGIN =========="
info "Attempting login via legacy backend..."

LOGIN_RESPONSE=$(curl -s -X POST "$LEGACY_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password123")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ]; then
  # Try JSON format
  LOGIN_RESPONSE=$(curl -s -X POST "$LEGACY_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}')
  TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')
fi

if [ -z "$TOKEN" ]; then
  fail "Login failed. Response: $LOGIN_RESPONSE"
  echo ""
  echo "Trying with different credentials..."
  
  # Try token endpoint
  TOKEN_RESPONSE=$(curl -s -X POST "$LEGACY_URL/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=password123")
  TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty')
  
  if [ -z "$TOKEN" ]; then
    fail "All login attempts failed"
    echo "Last response: $TOKEN_RESPONSE"
    exit 1
  fi
fi

success "Login successful! Token obtained."
echo "Token: ${TOKEN:0:50}..."
echo ""

# Step 2: Test Gateway endpoints with token
echo "========== STEP 2: TEST GATEWAY SERVICES =========="

test_endpoint() {
  local name="$1"
  local url="$2"
  local expected="$3"
  
  RESPONSE=$(curl -s -w "\n%{http_code}" "$url" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
  BODY=$(echo "$RESPONSE" | head -n -1)
  
  if [ "$HTTP_CODE" = "$expected" ]; then
    success "$name (HTTP $HTTP_CODE)"
    echo "  Response: $(echo "$BODY" | head -c 100)..."
  else
    fail "$name (Expected $expected, got $HTTP_CODE)"
    echo "  Response: $(echo "$BODY" | head -c 200)"
  fi
  echo ""
}

# Auth Service
echo "--- Auth Service ---"
test_endpoint "GET /auth/me" "$BASE_URL/api/v1/auth/me" "200"

# Finance Service
echo "--- Finance Service ---"
test_endpoint "GET /finance/coa" "$BASE_URL/api/v1/finance/coa" "200"
test_endpoint "GET /finance/reports/trial-balance" "$BASE_URL/api/v1/finance/reports/trial-balance" "200"

# HR Service
echo "--- HR Service ---"
test_endpoint "GET /hr/stats" "$BASE_URL/api/v1/hr/stats" "200"
test_endpoint "GET /hr/departments" "$BASE_URL/api/v1/hr/departments" "200"
test_endpoint "GET /hr/employees" "$BASE_URL/api/v1/hr/employees" "200"

# Legacy Backend (direct)
echo "--- Legacy Backend (Direct) ---"
test_endpoint "GET /inventory/products" "$LEGACY_URL/inventory/products" "200"
test_endpoint "GET /hr/employees" "$LEGACY_URL/hr/employees" "200"

echo ""
echo "========== UAT COMPLETE =========="
echo ""
