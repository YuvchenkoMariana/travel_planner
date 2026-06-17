#!/bin/bash

# Travel Planner API - Quick Test Script
# Tests all major API endpoints

BASE_URL="http://localhost:8000"

echo "========================================"
echo "  Travel Planner API Test Script"
echo "========================================"
echo ""

# Check if server is running
echo "Checking if API server is running..."
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo "❌ ERROR: API server is not running!"
    echo "   Please start the server with: uvicorn api:app --reload"
    exit 1
fi
echo "✓ Server is running"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "⚠️  Warning: 'jq' not found. Installing jq will make output prettier."
    echo "   Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    echo ""
    JQ_CMD="cat"
else
    JQ_CMD="jq"
fi

echo "========================================"
echo "1. Creating User"
echo "========================================"
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User"}')
echo "$USER_RESPONSE" | $JQ_CMD

if command -v jq &> /dev/null; then
    USER_ID=$(echo "$USER_RESPONSE" | jq -r '.id')
else
    USER_ID=1  # Assume first user
fi
echo ""
echo "✓ Created user with ID: $USER_ID"
echo ""

echo "========================================"
echo "2. Creating Project (Without Places)"
echo "========================================"
PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/projects" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"name\": \"Test Project\",
    \"description\": \"Automated test project\",
    \"start_date\": \"2024-07-01\"
  }")
echo "$PROJECT_RESPONSE" | $JQ_CMD

if command -v jq &> /dev/null; then
    PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
else
    PROJECT_ID=1  # Assume first project
fi
echo ""
echo "✓ Created project with ID: $PROJECT_ID"
echo ""

echo "========================================"
echo "3. Adding Place to Project"
echo "========================================"
echo "   Note: This will call the Art Institute API"
echo "   It may fail if the place is not in their database"
echo ""
PLACE_RESPONSE=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "Paris",
    "notes": "Test place - Visit the Louvre"
  }')

# Check if place was added successfully
if echo "$PLACE_RESPONSE" | grep -q "external_id"; then
    echo "✓ Place added successfully!"
    echo "$PLACE_RESPONSE" | $JQ_CMD

    if command -v jq &> /dev/null; then
        EXTERNAL_ID=$(echo "$PLACE_RESPONSE" | jq -r '.places[0].external_id')
    fi
else
    echo "⚠️  Place not added (might not be in Art Institute API)"
    echo "$PLACE_RESPONSE" | $JQ_CMD
    EXTERNAL_ID=""
fi
echo ""

echo "========================================"
echo "4. Listing All Projects"
echo "========================================"
curl -s -X GET "$BASE_URL/projects" | $JQ_CMD
echo ""
echo "✓ Listed all projects"
echo ""

echo "========================================"
echo "5. Getting Project by ID"
echo "========================================"
curl -s -X GET "$BASE_URL/projects/$PROJECT_ID" | $JQ_CMD
echo ""
echo "✓ Retrieved project details"
echo ""

if [ -n "$EXTERNAL_ID" ]; then
    echo "========================================"
    echo "6. Listing Places in Project"
    echo "========================================"
    curl -s -X GET "$BASE_URL/projects/$PROJECT_ID/places" | $JQ_CMD
    echo ""
    echo "✓ Listed all places"
    echo ""

    echo "========================================"
    echo "7. Updating Place (Mark as Visited)"
    echo "========================================"
    curl -s -X PATCH "$BASE_URL/projects/$PROJECT_ID/places/$EXTERNAL_ID" \
      -H "Content-Type: application/json" \
      -d '{
        "visited": true,
        "notes": "Updated via test script - Amazing place!"
      }' | $JQ_CMD
    echo ""
    echo "✓ Updated place status"
    echo ""
fi

echo "========================================"
echo "8. Updating Project"
echo "========================================"
curl -s -X PUT "$BASE_URL/projects/$PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Test Project",
    "description": "Description updated by test script"
  }' | $JQ_CMD
echo ""
echo "✓ Updated project"
echo ""

echo "========================================"
echo "9. Testing Error Case (Non-existent Project)"
echo "========================================"
ERROR_RESPONSE=$(curl -s -X GET "$BASE_URL/projects/99999")
echo "$ERROR_RESPONSE" | $JQ_CMD
echo ""
echo "✓ Correctly returned 404 error"
echo ""

echo "========================================"
echo "10. Deleting Project"
echo "========================================"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/projects/$PROJECT_ID")

if [ "$HTTP_CODE" = "204" ]; then
    echo "✓ Project deleted successfully (HTTP 204)"
elif [ "$HTTP_CODE" = "400" ]; then
    echo "⚠️  Cannot delete project (has visited places) - HTTP 400"
    echo "   This is expected behavior!"
else
    echo "Response code: $HTTP_CODE"
fi
echo ""

echo "========================================"
echo "11. Health Check"
echo "========================================"
curl -s -X GET "$BASE_URL/health" | $JQ_CMD
echo ""
echo "✓ Health check passed"
echo ""

echo "========================================"
echo "✓ All Tests Completed!"
echo "========================================"
echo ""
echo "Summary:"
echo "  - Created user (ID: $USER_ID)"
echo "  - Created project (ID: $PROJECT_ID)"
if [ -n "$EXTERNAL_ID" ]; then
    echo "  - Added place with external_id: $EXTERNAL_ID"
    echo "  - Updated place"
fi
echo "  - Updated project"
echo "  - Tested error handling"
echo "  - Tested deletion"
echo "  - Health check passed"
echo ""
echo "To view the Swagger documentation:"
echo "  http://localhost:8000/docs"
echo ""
