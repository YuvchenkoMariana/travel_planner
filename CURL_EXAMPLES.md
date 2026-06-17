# Travel Planner API - cURL Examples

Complete collection of cURL commands for all API endpoints. Copy and paste these examples to test the API.

## Prerequisites

Server must be running:
```bash
uvicorn api:app --reload
```

Base URL: `http://localhost:8000`

---

## Table of Contents

1. [Users](#users)
2. [Projects](#projects)
3. [Places](#places)
4. [Health Check](#health-check)
5. [Complete Workflow Example](#complete-workflow-example)

---

## Users

### Create a User

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson"
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Alice Johnson"
}
```

### Get User by ID

```bash
curl -X GET "http://localhost:8000/users/1"
```

**Response:**
```json
{
  "id": 1,
  "name": "Alice Johnson"
}
```

### Get Non-existent User (404 Example)

```bash
curl -X GET "http://localhost:8000/users/999"
```

**Response:**
```json
{
  "detail": "User with id 999 not found"
}
```

---

## Projects

### Create a Project (Without Places)

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "name": "European Adventure",
    "description": "Summer trip across Europe",
    "start_date": "2024-07-01"
  }'
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "European Adventure",
  "description": "Summer trip across Europe",
  "start_date": "2024-07-01",
  "completed": false,
  "places": []
}
```

### Create a Project with Places (Bulk Create)

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "name": "Art Tour",
    "description": "Visit famous art locations",
    "start_date": "2024-08-01",
    "places": [
      {
        "place_name": "Paris",
        "notes": "Visit the Louvre Museum"
      },
      {
        "place_name": "Rome",
        "notes": "See the Vatican Museums"
      }
    ]
  }'
```

**Note:** Places will be validated against the Art Institute API and `external_id` and `api_link` will be populated automatically.

**Response:**
```json
{
  "id": 2,
  "user_id": 1,
  "name": "Art Tour",
  "description": "Visit famous art locations",
  "start_date": "2024-08-01",
  "completed": false,
  "places": [
    {
      "place_name": "Paris",
      "external_id": "-2147476828",
      "api_link": "https://api.artic.edu/api/v1/places/-2147476828",
      "notes": "Visit the Louvre Museum",
      "visited": false
    }
  ]
}
```

### List All Projects

```bash
curl -X GET "http://localhost:8000/projects"
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "European Adventure",
    "description": "Summer trip across Europe",
    "start_date": "2024-07-01",
    "completed": false,
    "places": []
  },
  {
    "id": 2,
    "user_id": 1,
    "name": "Art Tour",
    "description": "Visit famous art locations",
    "start_date": "2024-08-01",
    "completed": false,
    "places": [...]
  }
]
```

### List Projects for Specific User

```bash
curl -X GET "http://localhost:8000/projects?user_id=1"
```

### Get Project by ID

```bash
curl -X GET "http://localhost:8000/projects/1"
```

### Update Project

```bash
curl -X PUT "http://localhost:8000/projects/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "European Grand Tour",
    "description": "Extended summer trip across Europe - 3 weeks",
    "start_date": "2024-07-15"
  }'
```

**Note:** All fields are optional. Only include fields you want to update.

**Partial Update Example:**
```bash
curl -X PUT "http://localhost:8000/projects/1" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description only"
  }'
```

### Delete Project (Success)

```bash
curl -X DELETE "http://localhost:8000/projects/1" -v
```

**Response:** 204 No Content (empty body)

### Delete Project with Visited Places (Error Example)

```bash
curl -X DELETE "http://localhost:8000/projects/2" -v
```

**Response:** 400 Bad Request
```json
{
  "detail": "Cannot delete project: it has places marked as visited"
}
```

---

## Places

### Add Place to Project

```bash
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "Paris",
    "notes": "Visit the Eiffel Tower and Louvre"
  }'
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "European Adventure",
  "description": "Summer trip across Europe",
  "start_date": "2024-07-01",
  "completed": false,
  "places": [
    {
      "place_name": "Paris",
      "external_id": "-2147476828",
      "api_link": "https://api.artic.edu/api/v1/places/-2147476828",
      "notes": "Visit the Eiffel Tower and Louvre",
      "visited": false
    }
  ]
}
```

### Add Place Without Notes

```bash
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "Rome"
  }'
```

### List All Places in Project

```bash
curl -X GET "http://localhost:8000/projects/1/places"
```

**Response:**
```json
[
  {
    "place_name": "Paris",
    "external_id": "-2147476828",
    "api_link": "https://api.artic.edu/api/v1/places/-2147476828",
    "notes": "Visit the Eiffel Tower and Louvre",
    "visited": false
  },
  {
    "place_name": "Rome",
    "external_id": "-2783",
    "api_link": "https://api.artic.edu/api/v1/places/-2783",
    "notes": null,
    "visited": false
  }
]
```

### Get Single Place

```bash
curl -X GET "http://localhost:8000/projects/1/places/-2147476828"
```

**Response:**
```json
{
  "place_name": "Paris",
  "external_id": "-2147476828",
  "api_link": "https://api.artic.edu/api/v1/places/-2147476828",
  "notes": "Visit the Eiffel Tower and Louvre",
  "visited": false
}
```

### Update Place - Mark as Visited

```bash
curl -X PATCH "http://localhost:8000/projects/1/places/-2147476828" \
  -H "Content-Type: application/json" \
  -d '{
    "visited": true
  }'
```

**Response:**
```json
{
  "place_name": "Paris",
  "external_id": "-2147476828",
  "api_link": "https://api.artic.edu/api/v1/places/-2147476828",
  "notes": "Visit the Eiffel Tower and Louvre",
  "visited": true
}
```

### Update Place - Update Notes

```bash
curl -X PATCH "http://localhost:8000/projects/1/places/-2147476828" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Amazing experience! The Louvre was incredible."
  }'
```

### Update Place - Both Notes and Visited

```bash
curl -X PATCH "http://localhost:8000/projects/1/places/-2147476828" \
  -H "Content-Type: application/json" \
  -d '{
    "visited": true,
    "notes": "Completed! The Eiffel Tower at sunset was breathtaking."
  }'
```

---

## Health Check

### Check API Health

```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "travel-planner-api"
}
```

---

## Complete Workflow Example

Here's a complete end-to-end example of using the API:

### Step 1: Create a User

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Smith"}'
```

Save the `id` from response (e.g., `1`)

### Step 2: Create a Project

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "name": "Summer Vacation",
    "description": "Beach and city tour",
    "start_date": "2024-06-15"
  }'
```

Save the project `id` from response (e.g., `1`)

### Step 3: Add Places to Project

```bash
# Add first place
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "Paris",
    "notes": "Day 1-3: Explore the city"
  }'

# Add second place
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "Rome",
    "notes": "Day 4-6: Ancient history tour"
  }'

# Add third place
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "Barcelona",
    "notes": "Day 7-9: Beach and Gaudi architecture"
  }'
```

### Step 4: View All Places

```bash
curl -X GET "http://localhost:8000/projects/1/places"
```

### Step 5: Mark Places as Visited

```bash
# Mark Paris as visited
curl -X PATCH "http://localhost:8000/projects/1/places/PARIS_EXTERNAL_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "visited": true,
    "notes": "Day 1-3: Explored the city. Loved the Louvre!"
  }'

# Mark Rome as visited
curl -X PATCH "http://localhost:8000/projects/1/places/ROME_EXTERNAL_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "visited": true,
    "notes": "Day 4-6: Colosseum was amazing!"
  }'
```

**Note:** Replace `PARIS_EXTERNAL_ID` and `ROME_EXTERNAL_ID` with actual external IDs from the responses.

### Step 6: Check Project Status

```bash
curl -X GET "http://localhost:8000/projects/1"
```

The project's `completed` field will be `false` because not all places are visited.

### Step 7: Mark Last Place as Visited

```bash
curl -X PATCH "http://localhost:8000/projects/1/places/BARCELONA_EXTERNAL_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "visited": true,
    "notes": "Day 7-9: Perfect ending to the trip!"
  }'
```

### Step 8: Verify Project Completion

```bash
curl -X GET "http://localhost:8000/projects/1"
```

Now `completed` will be `true` because all places are visited!

### Step 9: Try to Delete (Should Fail)

```bash
curl -X DELETE "http://localhost:8000/projects/1" -v
```

Should return 400 Bad Request because project has visited places.

---

## Error Examples

### 400 Bad Request - Too Many Places

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "name": "Too Many Places",
    "places": [
      {"place_name": "Place1"},
      {"place_name": "Place2"},
      {"place_name": "Place3"},
      {"place_name": "Place4"},
      {"place_name": "Place5"},
      {"place_name": "Place6"},
      {"place_name": "Place7"},
      {"place_name": "Place8"},
      {"place_name": "Place9"},
      {"place_name": "Place10"},
      {"place_name": "Place11"}
    ]
  }'
```

**Response:** 400 Bad Request
```json
{
  "detail": "Cannot add more than 10 places to a project"
}
```

### 400 Bad Request - Duplicate Place Names

```bash
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{"place_name": "Paris"}'

# Try to add Paris again
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{"place_name": "Paris"}'
```

**Response:** 400 Bad Request
```json
{
  "detail": "Place with name 'Paris' already exists in project"
}
```

### 404 Not Found - Project Doesn't Exist

```bash
curl -X GET "http://localhost:8000/projects/999"
```

**Response:** 404 Not Found
```json
{
  "detail": "Project with id 999 not found"
}
```

### 422 Unprocessable Entity - Place Not in API

```bash
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "NonexistentCity12345"
  }'
```

**Response:** 422 Unprocessable Entity
```json
{
  "detail": "Place 'NonexistentCity12345' not found in Art Institute API"
}
```

---

## Pretty Print JSON Responses

Add `| jq` to any command for formatted JSON output:

```bash
curl -X GET "http://localhost:8000/projects/1" | jq
```

Or use Python:

```bash
curl -X GET "http://localhost:8000/projects/1" | python -m json.tool
```

---

## Save Response to File

```bash
curl -X GET "http://localhost:8000/projects/1" > project.json
```

---

## Show HTTP Headers

Add `-v` (verbose) or `-i` (include headers):

```bash
curl -X GET "http://localhost:8000/projects/1" -v
```

---

## Test Script

Save this as `test_api.sh` for quick testing:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "1. Creating user..."
USER_ID=$(curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User"}' | jq -r '.id')
echo "   Created user ID: $USER_ID"

echo "2. Creating project..."
PROJECT_ID=$(curl -s -X POST "$BASE_URL/projects" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": $USER_ID, \"name\": \"Test Project\"}" | jq -r '.id')
echo "   Created project ID: $PROJECT_ID"

echo "3. Adding place..."
curl -s -X POST "$BASE_URL/projects/$PROJECT_ID/places" \
  -H "Content-Type: application/json" \
  -d '{"place_name": "Paris", "notes": "Test place"}' | jq

echo "4. Listing places..."
curl -s -X GET "$BASE_URL/projects/$PROJECT_ID/places" | jq

echo "Done!"
```

Make executable and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Summary of All Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Create a user |
| GET | `/users/{user_id}` | Get user by ID |
| POST | `/projects` | Create project (with or without places) |
| GET | `/projects` | List all projects |
| GET | `/projects?user_id={id}` | List projects for user |
| GET | `/projects/{project_id}` | Get project by ID |
| PUT | `/projects/{project_id}` | Update project |
| DELETE | `/projects/{project_id}` | Delete project |
| POST | `/projects/{project_id}/places` | Add place to project |
| GET | `/projects/{project_id}/places` | List places in project |
| GET | `/projects/{project_id}/places/{external_id}` | Get single place |
| PATCH | `/projects/{project_id}/places/{external_id}` | Update place |
| GET | `/health` | Health check |

---

## Tips

1. **Use `jq` for JSON formatting**: `| jq`
2. **Save common requests**: Create shell aliases
3. **Use variables**: Store IDs in variables for easier testing
4. **Check status codes**: Use `-w "\nHTTP: %{http_code}\n"` to see status
5. **Debug**: Use `-v` flag to see full request/response

---

## Related Documentation

- [README.md](README.md) - Setup and overview
- [SWAGGER_GUIDE.md](SWAGGER_GUIDE.md) - Interactive Swagger UI
- [API_WORKFLOW.md](API_WORKFLOW.md) - API usage patterns

**Happy testing!** 🚀
