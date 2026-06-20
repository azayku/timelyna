#!/bin/bash
# Quick Docker testing script
# Usage: bash docker_test.sh

set -e

echo "=========================================="
echo "Timelyna - Docker Testing"
echo "=========================================="
echo ""

# Check if docker is running
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker not found"
    exit 1
fi

# Step 1: Check Docker services
echo "[1] Checking Docker services..."
docker-compose ps
echo ""

# Step 2: Check if backend is healthy
echo "[2] Testing backend health..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"admin@timelyna.com","password":"Admin1234!"}')

if [ "$BACKEND_STATUS" == "401" ]; then
    echo "[FAIL] Got 401 - credentials wrong or user doesn't exist"
elif [ "$BACKEND_STATUS" == "200" ]; then
    echo "[OK] Backend responding (200)"
else
    echo "[ERROR] Backend returned $BACKEND_STATUS (expected 200 or 401)"
    exit 1
fi
echo ""

# Step 3: Seed database
echo "[3] Seeding database..."
docker-compose exec -T backend python seed_dev.py 2>&1 | head -20
echo ""

# Step 4: Test login
echo "[4] Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@timelyna.com","password":"Admin1234!"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4 || true)

if [ -z "$TOKEN" ]; then
    echo "[ERROR] Failed to get token"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "[OK] Got token: ${TOKEN:0:30}..."
echo ""

# Step 5: Test /admin/users
echo "[5] Testing GET /admin/users..."
USERS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8000/api/v1/admin/users \
    -H "Authorization: Bearer $TOKEN")

echo "[API Status: $USERS_STATUS]"

USERS_DATA=$(curl -s -X GET http://localhost:8000/api/v1/admin/users \
    -H "Authorization: Bearer $TOKEN")

USER_COUNT=$(echo "$USERS_DATA" | grep -o '"employee_id"' | wc -l || echo "0")

if [ "$USER_COUNT" -gt 0 ]; then
    echo "[OK] Found $USER_COUNT users"
    echo "$USERS_DATA" | head -c 200
else
    echo "[WARN] No users found (empty response)"
    echo "Response: $USERS_DATA"
fi
echo ""

# Step 6: Test /finance/invoices
echo "[6] Testing GET /finance/invoices..."
INVOICES_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://localhost:8000/api/v1/finance/invoices \
    -H "Authorization: Bearer $TOKEN")

echo "[API Status: $INVOICES_STATUS]"

INVOICES_DATA=$(curl -s -X GET http://localhost:8000/api/v1/finance/invoices \
    -H "Authorization: Bearer $TOKEN")

INVOICE_COUNT=$(echo "$INVOICES_DATA" | grep -o '"invoice_id"' | wc -l || echo "0")

if [ "$INVOICE_COUNT" -gt 0 ]; then
    echo "[OK] Found $INVOICE_COUNT invoices"
    echo "$INVOICES_DATA" | head -c 200
else
    echo "[OK] No invoices (empty response - expected for new system)"
    echo "Response: $INVOICES_DATA"
fi
echo ""

# Step 7: Check frontend
echo "[7] Testing frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)

if [ "$FRONTEND_STATUS" == "200" ]; then
    echo "[OK] Frontend responding (HTTP 200)"
else
    echo "[WARN] Frontend returned $FRONTEND_STATUS"
fi
echo ""

# Step 8: Check database
echo "[8] Checking database content..."
EMPLOYEE_COUNT=$(docker-compose exec -T postgres psql -U timelyna -d timelyna -c "SELECT COUNT(*) FROM employees;" 2>/dev/null | tail -1 | tr -d ' ')

if [ ! -z "$EMPLOYEE_COUNT" ]; then
    echo "[OK] Database has $EMPLOYEE_COUNT employees"
else
    echo "[WARN] Could not check database"
fi
echo ""

echo "=========================================="
echo "Testing Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open http://localhost in your browser"
echo "2. Login with: admin@timelyna.com / Admin1234!"
echo "3. Try navigating to /admin/users"
echo "4. Try navigating to /finance/invoices"
echo ""
echo "If pages don't load, check:"
echo "  - Browser console (F12) for errors"
echo "  - Docker logs: docker-compose logs backend"
echo "  - Network tab in DevTools"
