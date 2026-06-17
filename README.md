# Travel Planner API

A RESTful API for managing travel projects and places, integrated with the Art Institute of Chicago API for place validation.

## Features

- ✅ Create and manage travel projects
- ✅ Add places to projects with automatic Art Institute API validation
- ✅ Track visited places and project completion status
- ✅ Prevent deletion of projects with visited places
- ✅ SQLite database for data persistence
- ✅ Comprehensive API documentation via Swagger/OpenAPI

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite
- **External API**: Art Institute of Chicago API
- **Testing**: pytest
- **Python**: 3.11+

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the API Server

```bash
uvicorn api:app --reload
```

The API will be available at: `http://localhost:8000`

### 3. Access Interactive API Documentation

**🎨 Swagger UI** (Interactive Testing):
- URL: http://localhost:8000/docs
- Try out endpoints directly in your browser
- See request/response examples
- Test the API without curl/Postman

**📖 ReDoc** (Clean Documentation):
- URL: http://localhost:8000/redoc
- Modern, clean documentation layout
- Better for reading and reference

**📄 OpenAPI JSON** (Machine-Readable):
- URL: http://localhost:8000/openapi.json
- Import into Postman or other tools
- OpenAPI 3.0 specification

See [SWAGGER_GUIDE.md](SWAGGER_GUIDE.md) for detailed Swagger documentation.

### 4. Run Tests

```bash
# Run all tests
pytest

# Run specific test files
pytest test_api.py -v
pytest test_integration.py -v
```

## API Endpoints

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Create a new user |
| GET | `/users/{user_id}` | Get user by ID |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create a new project (optionally with places) |
| GET | `/projects` | List all projects (optional: `?user_id=X`) |
| GET | `/projects/{project_id}` | Get a single project |
| PUT | `/projects/{project_id}` | Update project information |
| DELETE | `/projects/{project_id}` | Delete a project |

### Places

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects/{project_id}/places` | Add a place to a project |
| GET | `/projects/{project_id}/places` | List all places in a project |
| GET | `/projects/{project_id}/places/{external_id}` | Get a single place |
| PATCH | `/projects/{project_id}/places/{external_id}` | Update place (notes/visited) |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check endpoint |

## Example Requests

**📖 Complete cURL Examples**: See [CURL_EXAMPLES.md](CURL_EXAMPLES.md) for comprehensive examples of all endpoints.

**🧪 Quick Test Script**: Run `./test_api.sh` to test all endpoints automatically.

### Create a User

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson"}'
```

Response:
```json
{
  "id": 1,
  "name": "Alice Johnson"
}
```

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

Response:
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

### Create a Project with Places (Bulk)

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "name": "Art Tour",
    "description": "Visit famous art locations",
    "start_date": "2024-08-01",
    "places": [
      {"place_name": "Paris", "notes": "Louvre Museum"},
      {"place_name": "Rome", "notes": "Vatican Museums"}
    ]
  }'
```

**Note**: When places are provided, they are automatically validated against the Art Institute API.

### Add a Place to Project

```bash
curl -X POST "http://localhost:8000/projects/1/places" \
  -H "Content-Type: application/json" \
  -d '{
    "place_name": "Paris",
    "notes": "Visit the Louvre Museum"
  }'
```

**Note**: The place name is automatically validated against the Art Institute API, and `external_id` and `api_link` are populated from the API response.

Response:
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
      "notes": "Visit the Louvre Museum",
      "visited": false
    }
  ]
}
```

### List Projects

```bash
# All projects
curl -X GET "http://localhost:8000/projects"

# Filter by user
curl -X GET "http://localhost:8000/projects?user_id=1"
```

### Update a Place (Mark as Visited)

```bash
curl -X PATCH "http://localhost:8000/projects/1/places/-2147476828" \
  -H "Content-Type: application/json" \
  -d '{
    "visited": true,
    "notes": "Amazing place! Loved the Louvre."
  }'
```


### Delete a Project

```bash
curl -X DELETE "http://localhost:8000/projects/1"
```

**Note**: Projects with visited places cannot be deleted (returns 400 Bad Request).

## Validation Rules

### Projects
- Maximum 10 places per project
- Cannot delete a project if any place is marked as visited
- User must exist before creating a project

### Places
- Place name is required
- Place must exist in the Art Institute API
- Duplicate place names within the same project are not allowed
- External ID and API link are automatically populated from the API

### Project Completion
- A project is automatically marked as "completed" when all its places are visited
- Completion status is updated whenever a place's visited status changes

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Delete successful |
| 400 | Bad Request - Validation error or business rule violation |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Place not found in Art Institute API |
| 500 | Internal Server Error - Server error |

## Project Structure

```
travel_planner/
├── api.py                      # FastAPI application and endpoints
├── travel_planner.py          # Domain models (User, Project, Place)
├── repository.py              # Abstract repository + InMemoryRepository
├── sqlite_repository.py       # SQLite implementation
├── art_institute_client.py    # Art Institute API client with caching
├── test_api.py               # API integration tests
├── test_integration.py       # Domain model tests
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── travel_planner.db         # SQLite database (created at runtime)
```

## Architecture

The application follows a clean architecture pattern with clear separation of concerns:

1. **API Layer** (`api.py`): FastAPI routes, request/response models, HTTP handling
2. **Domain Layer** (`travel_planner.py`): Business logic, validation rules, entities
3. **Repository Layer** (`repository.py`, `sqlite_repository.py`): Data persistence
4. **Integration Layer** (`art_institute_client.py`): External API integration

## Development

### Run in Development Mode

```bash
uvicorn api:app --reload --port 8000
```

### Run Tests with Coverage

```bash
pytest --cov=. --cov-report=html
```

### Format Code

```bash
black *.py
```

### Run Linting

```bash
flake8 *.py
```

## Database

The application uses SQLite for data persistence. The database file (`travel_planner.db`) is automatically created on first run.

### Database Schema

**Users Table**:
- id (INTEGER PRIMARY KEY)
- name (TEXT)

**Projects Table**:
- id (INTEGER PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY)
- name (TEXT)
- description (TEXT)
- start_date (TEXT)
- completed (INTEGER/BOOLEAN)

**Places Table**:
- id (INTEGER PRIMARY KEY)
- project_id (INTEGER, FOREIGN KEY)
- place_name (TEXT)
- external_id (TEXT)
- api_link (TEXT)
- notes (TEXT)
- visited (INTEGER/BOOLEAN)

## External API Integration

### Art Institute of Chicago API

The application integrates with the [Art Institute of Chicago API](https://api.artic.edu/docs/) to validate places.

**Features**:
- Automatic place validation by name
- Response caching to minimize API calls
- External ID and API link population
- Graceful error handling

**Example API Call**:
```
GET https://api.artic.edu/api/v1/places/search?q=Paris
```

## Testing

### Test Files

- `test_api.py`: 17 tests for REST API endpoints
- `test_integration.py`: 26 tests for domain logic with in-memory storage

### Run All Tests

```bash
pytest -v
```

### Test Summary

```
test_api.py .......................... 17 passed
test_integration.py .................. 26 passed (4 skipped)
====================================== 43 passed, 4 skipped
```

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn api:app --port 8001
```

### Database Locked Error

```bash
# Remove database and restart
rm travel_planner.db
uvicorn api:app --reload
```

### SSL Certificate Errors (Art Institute API)

Some environments may have SSL certificate issues. This is an environment-specific problem, not a code issue.

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Contact

For questions or issues, please open an issue on GitHub.
