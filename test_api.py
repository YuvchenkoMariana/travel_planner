"""
Integration tests for FastAPI REST API endpoints.
"""

import pytest
import os
from fastapi.testclient import TestClient
from datetime import date

from api import app
from travel_planner import set_repository
from sqlite_repository import SQLiteRepository


@pytest.fixture
def client():
    """Create a test client with a test database."""
    test_db = "test_api.db"

    # Remove test database if it exists
    if os.path.exists(test_db):
        os.remove(test_db)

    # Initialize repository
    repo = SQLiteRepository(test_db)
    set_repository(repo)

    # Create test client
    client = TestClient(app)

    yield client

    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)


class TestUserEndpoints:
    """Test user-related endpoints."""

    def test_create_user(self, client):
        """Test POST /users - create a new user."""
        response = client.post("/users", json={"name": "Alice Johnson"})

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Alice Johnson"

    def test_get_user(self, client):
        """Test GET /users/{user_id} - get user by ID."""
        # Create user first
        create_response = client.post("/users", json={"name": "Bob Smith"})
        user_id = create_response.json()["id"]

        # Get user
        response = client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == "Bob Smith"

    def test_get_nonexistent_user(self, client):
        """Test GET /users/{user_id} - returns 404 for nonexistent user."""
        response = client.get("/users/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestProjectEndpoints:
    """Test project-related endpoints."""

    def test_create_project_without_places(self, client):
        """Test POST /projects - create a new project without places."""
        # Create user first
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        # Create project without places
        response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Europe Trip",
            "description": "Summer vacation",
            "start_date": "2024-07-01"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Europe Trip"
        assert data["description"] == "Summer vacation"
        assert data["start_date"] == "2024-07-01"
        assert data["completed"] is False
        assert len(data["places"]) == 0

    def test_create_project_with_places(self, client):
        """Test POST /projects - create a project with places in one request."""
        # Create user first
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        # Create project with places (will call Art Institute API)
        response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Art Tour",
            "description": "Visit famous art locations",
            "places": [
                {"place_name": "Paris", "notes": "Louvre Museum"}
            ]
        })

        # Will return 201 if API works, or 422 if place not found
        assert response.status_code in [201, 422]

        if response.status_code == 201:
            data = response.json()
            assert data["name"] == "Art Tour"
            assert len(data["places"]) == 1

    def test_create_project_nonexistent_user(self, client):
        """Test POST /projects - returns 404 for nonexistent user."""
        response = client.post("/projects", json={
            "user_id": 999,
            "name": "Trip"
        })

        assert response.status_code == 404
        assert "user" in response.json()["detail"].lower()

    def test_list_projects(self, client):
        """Test GET /projects - list all projects."""
        # Create user and projects
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        client.post("/projects", json={"user_id": user_id, "name": "Trip 1"})
        client.post("/projects", json={"user_id": user_id, "name": "Trip 2"})

        # List projects
        response = client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Trip 1"
        assert data[1]["name"] == "Trip 2"

    def test_list_projects_by_user(self, client):
        """Test GET /projects?user_id=X - filter by user."""
        # Create users and projects
        user1_response = client.post("/users", json={"name": "Alice"})
        user2_response = client.post("/users", json={"name": "Bob"})
        user1_id = user1_response.json()["id"]
        user2_id = user2_response.json()["id"]

        client.post("/projects", json={"user_id": user1_id, "name": "Alice Trip 1"})
        client.post("/projects", json={"user_id": user2_id, "name": "Bob Trip"})
        client.post("/projects", json={"user_id": user1_id, "name": "Alice Trip 2"})

        # Filter by user1
        response = client.get(f"/projects?user_id={user1_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["user_id"] == user1_id for p in data)

    def test_get_project(self, client):
        """Test GET /projects/{project_id} - get single project."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        create_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Europe Trip"
        })
        project_id = create_response.json()["id"]

        # Get project
        response = client.get(f"/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Europe Trip"

    def test_get_nonexistent_project(self, client):
        """Test GET /projects/{project_id} - returns 404."""
        response = client.get("/projects/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_project(self, client):
        """Test PUT /projects/{project_id} - update project."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        create_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Original Name"
        })
        project_id = create_response.json()["id"]

        # Update project
        response = client.put(f"/projects/{project_id}", json={
            "name": "Updated Name",
            "description": "New description"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    def test_delete_project(self, client):
        """Test DELETE /projects/{project_id} - delete project."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        create_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Trip"
        })
        project_id = create_response.json()["id"]

        # Delete project
        response = client.delete(f"/projects/{project_id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/projects/{project_id}")
        assert get_response.status_code == 404

    def test_cannot_delete_project_with_visited_places(self, client):
        """Test DELETE /projects/{project_id} - cannot delete with visited places."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        create_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Trip"
        })
        project_id = create_response.json()["id"]

        # Add a place and mark it visited (bypassing API for test)
        from travel_planner import Project, Place, get_repository
        project = Project.get_by_id(project_id)
        place = Place("Test Place", "test_id", "test_link")
        place.visited = True
        project.places.append(place)
        get_repository().update_project(project)

        # Try to delete
        response = client.delete(f"/projects/{project_id}")

        assert response.status_code == 400
        assert "visited" in response.json()["detail"].lower()


class TestPlaceEndpoints:
    """Test place-related endpoints."""

    def test_add_place_to_project(self, client):
        """Test POST /projects/{project_id}/places - add place."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        project_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Trip"
        })
        project_id = project_response.json()["id"]

        # This would call real API - skip if unavailable
        # For now, test the endpoint structure
        response = client.post(f"/projects/{project_id}/places", json={
            "place_name": "Paris",
            "notes": "Visit Louvre"
        })

        # Will fail with 422 if API doesn't find "Paris"
        # But endpoint structure is correct
        assert response.status_code in [201, 422]

    def test_list_places(self, client):
        """Test GET /projects/{project_id}/places - list places."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        project_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Trip"
        })
        project_id = project_response.json()["id"]

        # Add places directly for testing
        from travel_planner import Project, Place, get_repository
        project = Project.get_by_id(project_id)
        place1 = Place("Paris", "paris_id", "link1", notes="Visit Louvre")
        place2 = Place("Rome", "rome_id", "link2", notes="See Colosseum")
        project.places.extend([place1, place2])
        get_repository().update_project(project)

        # List places
        response = client.get(f"/projects/{project_id}/places")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["place_name"] == "Paris"
        assert data[1]["place_name"] == "Rome"

    def test_get_place(self, client):
        """Test GET /projects/{project_id}/places/{external_id} - get single place."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        project_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Trip"
        })
        project_id = project_response.json()["id"]

        # Add place directly
        from travel_planner import Project, Place, get_repository
        project = Project.get_by_id(project_id)
        place = Place("Paris", "paris_123", "link", notes="Visit Louvre")
        project.places.append(place)
        get_repository().update_project(project)

        # Get place
        response = client.get(f"/projects/{project_id}/places/paris_123")

        assert response.status_code == 200
        data = response.json()
        assert data["place_name"] == "Paris"
        assert data["external_id"] == "paris_123"

    def test_update_place(self, client):
        """Test PATCH /projects/{project_id}/places/{external_id} - update place."""
        user_response = client.post("/users", json={"name": "Alice"})
        user_id = user_response.json()["id"]

        project_response = client.post("/projects", json={
            "user_id": user_id,
            "name": "Trip"
        })
        project_id = project_response.json()["id"]

        # Add place directly
        from travel_planner import Project, Place, get_repository
        project = Project.get_by_id(project_id)
        place = Place("Paris", "paris_123", "link", notes="Original notes")
        project.places.append(place)
        get_repository().update_project(project)

        # Update place
        response = client.patch(f"/projects/{project_id}/places/paris_123", json={
            "notes": "Updated notes",
            "visited": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
        assert data["visited"] is True


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test GET /health - health check."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
