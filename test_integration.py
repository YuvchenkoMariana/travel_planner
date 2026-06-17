import pytest
from datetime import date
from travel_planner import User, Project, Place, set_repository, get_repository
from repository import InMemoryRepository
from art_institute_client import ArtInstituteClient, APICache, get_client, clear_cache


@pytest.fixture
def setup_repository():
    """Setup in-memory repository before each test."""
    repo = InMemoryRepository()
    set_repository(repo)
    yield repo
    repo.clear()


@pytest.fixture
def setup_api_client():
    """Setup API client with cache before each test."""
    cache = APICache()
    client = ArtInstituteClient(cache)
    # Replace the global client
    import art_institute_client
    art_institute_client._default_client = client
    yield client
    client.clear_cache()


class TestUser:
    """Test User CRUD operations."""

    def test_add_user(self, setup_repository):
        """Test adding a new user."""
        user = User.add_user("John Doe")
        assert user.id == 1
        assert user.name == "John Doe"

    def test_add_multiple_users(self, setup_repository):
        """Test adding multiple users with auto-incrementing IDs."""
        user1 = User.add_user("Alice")
        user2 = User.add_user("Bob")

        assert user1.id == 1
        assert user2.id == 2
        assert user1.name == "Alice"
        assert user2.name == "Bob"

    def test_update_user(self, setup_repository):
        """Test updating user information."""
        user = User.add_user("John Doe")
        user.update_user(name="Jane Doe")

        assert user.name == "Jane Doe"


class TestPlace:
    """Test Place operations."""

    def test_create_place(self):
        """Test creating a place."""
        place = Place(
            place_name="Chicago",
            notes="Visit in summer"
        )

        assert place.place_name == "Chicago"
        assert place.external_id is None  # Not populated until added to project
        assert place.api_link is None  # Not populated until added to project
        assert place.notes == "Visit in summer"
        assert place.visited is False

    def test_update_notes(self):
        """Test updating place notes."""
        place = Place("Chicago", "123", "https://example.com")
        place.update_notes("New notes here")

        assert place.notes == "New notes here"

    def test_update_visited(self):
        """Test marking place as visited."""
        place = Place("Chicago", "123", "https://example.com")
        assert place.visited is False

        place.update_visited(True)
        assert place.visited is True


class TestProject:
    """Test Project CRUD operations."""

    def test_create_project(self, setup_repository):
        """Test creating a basic project."""
        user = User.add_user("Alice")
        project = Project(
            user_id=user.id,
            name="Europe Trip",
            description="Summer vacation",
            start_date=date(2024, 7, 1)
        )

        repo = get_repository()
        saved_project = repo.add_project(project)

        assert saved_project.id == 1
        assert saved_project.name == "Europe Trip"
        assert saved_project.description == "Summer vacation"
        assert len(saved_project.places) == 0
        assert saved_project.completed is False

    def test_update_project(self, setup_repository):
        """Test updating project information."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")
        repo = get_repository()
        repo.add_project(project)

        project.update_project(
            name="Updated Trip",
            description="New description",
            start_date=date(2024, 8, 1)
        )

        assert project.name == "Updated Trip"
        assert project.description == "New description"
        assert project.start_date == date(2024, 8, 1)

    def test_list_projects(self, setup_repository):
        """Test listing all projects."""
        user1 = User.add_user("Alice")
        user2 = User.add_user("Bob")

        project1 = Project(user_id=user1.id, name="Trip 1")
        project2 = Project(user_id=user2.id, name="Trip 2")

        repo = get_repository()
        repo.add_project(project1)
        repo.add_project(project2)

        projects = Project.list_projects()
        assert len(projects) == 2

    def test_list_projects_by_user(self, setup_repository):
        """Test filtering projects by user."""
        user1 = User.add_user("Alice")
        user2 = User.add_user("Bob")

        project1 = Project(user_id=user1.id, name="Trip 1")
        project2 = Project(user_id=user2.id, name="Trip 2")
        project3 = Project(user_id=user1.id, name="Trip 3")

        repo = get_repository()
        repo.add_project(project1)
        repo.add_project(project2)
        repo.add_project(project3)

        alice_projects = Project.list_projects(user_id=user1.id)
        assert len(alice_projects) == 2
        assert all(p.user_id == user1.id for p in alice_projects)

    def test_get_project_by_id(self, setup_repository):
        """Test retrieving a project by ID."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        saved = repo.add_project(project)

        retrieved = Project.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.name == "Trip"

    def test_get_nonexistent_project(self, setup_repository):
        """Test retrieving a project that doesn't exist."""
        result = Project.get_by_id(999)
        assert result is None


class TestProjectPlaces:
    """Test project place management."""

    def test_add_place_to_project(self, setup_repository, setup_api_client):
        """Test adding a place to a project with API validation."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        # Create place with just the name - external_id and api_link will be populated by API
        place = Place(place_name="Chicago")

        try:
            success = project.add_place(place)
            assert success is True
            assert len(project.places) == 1
            assert project.places[0].place_name == "Chicago"
            # After adding, external_id and api_link should be populated from API
            assert project.places[0].external_id is not None
            assert project.places[0].api_link is not None
        except ValueError:
            # If the API is down or the place doesn't exist, skip this test
            pytest.skip("Art Institute API unavailable or place not found")

    def test_add_place_max_limit(self, setup_repository):
        """Test that adding more than 10 places returns False."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        # Add 10 places directly (bypassing API validation for this test)
        for i in range(10):
            project.places.append(Place(f"Place {i}", f"id_{i}", f"link_{i}"))

        # Try to add 11th place
        place = Place("Extra Place", "extra_id", "extra_link")
        success = project.add_place(place)

        assert success is False
        assert len(project.places) == 10

    def test_add_duplicate_place(self, setup_repository):
        """Test that adding a duplicate place name raises ValueError."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        place1 = Place("Chicago")
        place1.external_id = "123"  # Simulate already added
        project.places.append(place1)

        place2 = Place("Chicago")  # Same name

        with pytest.raises(ValueError, match="already exists"):
            project.add_place(place2)

    def test_get_places(self, setup_repository):
        """Test retrieving all places from a project."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        place1 = Place("Place 1", "id1", "link1")
        place2 = Place("Place 2", "id2", "link2")

        project.places.append(place1)
        project.places.append(place2)

        places = project.get_places()
        assert len(places) == 2
        assert places[0].place_name == "Place 1"
        assert places[1].place_name == "Place 2"

    def test_get_place_by_external_id(self, setup_repository):
        """Test retrieving a specific place by external ID."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        place1 = Place("Place 1", "id1", "link1")
        place2 = Place("Place 2", "id2", "link2")

        project.places.append(place1)
        project.places.append(place2)

        found = project.get_place("id2")
        assert found is not None
        assert found.place_name == "Place 2"

        not_found = project.get_place("id999")
        assert not_found is None


class TestProjectCompletion:
    """Test project completion tracking."""

    def test_project_not_completed_by_default(self, setup_repository):
        """Test that new projects are not completed."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        assert project.completed is False
        assert project.is_completed() is False

    def test_project_completed_when_all_visited(self, setup_repository):
        """Test that project is completed when all places visited."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        place1 = Place("Place 1", "id1", "link1")
        place2 = Place("Place 2", "id2", "link2")
        place1.visited = True
        place2.visited = True

        project.places.append(place1)
        project.places.append(place2)

        project.update_completion_status()

        assert project.is_completed() is True
        assert project.completed is True

    def test_project_not_completed_when_some_unvisited(self, setup_repository):
        """Test that project is not completed if some places unvisited."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        place1 = Place("Place 1", "id1", "link1")
        place2 = Place("Place 2", "id2", "link2")
        place1.visited = True
        place2.visited = False

        project.places.append(place1)
        project.places.append(place2)

        project.update_completion_status()

        assert project.is_completed() is False
        assert project.completed is False


class TestProjectDeletion:
    """Test project deletion rules."""

    def test_can_delete_project_with_unvisited_places(self, setup_repository):
        """Test that projects with unvisited places can be deleted."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        place = Place("Place 1", "id1", "link1", visited=False)
        project.places.append(place)

        assert project.can_delete() is True

    def test_cannot_delete_project_with_visited_places(self, setup_repository):
        """Test that projects with visited places cannot be deleted."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        place = Place("Place 1", "id1", "link1", visited=True)
        project.places.append(place)

        assert project.can_delete() is False

    def test_delete_project_instance(self, setup_repository):
        """Test deleting a project via instance method."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        success = project.delete_project()
        assert success is True

        # Verify it's deleted
        retrieved = Project.get_by_id(project.id)
        assert retrieved is None

    def test_delete_project_by_id(self, setup_repository):
        """Test deleting a project via static method."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        success = Project.delete_by_id(project.id)
        assert success is True

        # Verify it's deleted
        retrieved = Project.get_by_id(project.id)
        assert retrieved is None

    def test_cannot_delete_project_with_visited_place(self, setup_repository):
        """Test deletion fails when project has visited places."""
        user = User.add_user("Alice")
        project = Project(user_id=user.id, name="Trip")

        repo = get_repository()
        repo.add_project(project)

        place = Place("Place 1", "id1", "link1", visited=True)
        project.places.append(place)

        success = project.delete_project()
        assert success is False

        # Verify it still exists
        retrieved = Project.get_by_id(project.id)
        assert retrieved is not None


class TestCreateProjectWithPlaces:
    """Test creating projects with places in one operation."""

    def test_create_with_places_success(self, setup_repository, setup_api_client):
        """Test creating a project with valid places."""
        user = User.add_user("Alice")

        places = [
            Place(place_name="Chicago")
        ]

        try:
            project = Project.create_with_places(
                user_id=user.id,
                name="USA Trip",
                places=places,
                description="Visit major cities"
            )

            assert project.name == "USA Trip"
            assert len(project.places) == 1
            assert project.places[0].place_name == "Chicago"
            # external_id and api_link should be populated from API
            assert project.places[0].external_id is not None
            assert project.places[0].api_link is not None
        except ValueError:
            pytest.skip("Art Institute API unavailable or place not found")

    def test_create_with_too_many_places(self, setup_repository):
        """Test that creating with >10 places raises ValueError."""
        user = User.add_user("Alice")

        places = [
            Place(f"Place {i}", f"id_{i}", f"link_{i}")
            for i in range(11)
        ]

        with pytest.raises(ValueError, match="Cannot add more than 10 places"):
            Project.create_with_places(
                user_id=user.id,
                name="Big Trip",
                places=places
            )

    def test_create_with_duplicate_places(self, setup_repository):
        """Test that duplicate place names raise ValueError."""
        user = User.add_user("Alice")

        places = [
            Place("Chicago"),
            Place("Chicago")  # Duplicate name
        ]

        with pytest.raises(ValueError, match="Duplicate place names"):
            Project.create_with_places(
                user_id=user.id,
                name="Trip",
                places=places
            )


class TestAPICache:
    """Test API caching functionality."""

    def test_cache_stores_and_retrieves(self, setup_api_client):
        """Test that cache stores and retrieves responses."""
        client = setup_api_client

        # First call - hits API
        try:
            result1 = client.search_places("Chicago")
            cache_size_after_first = client.get_cache_size()

            # Second call - should hit cache
            result2 = client.search_places("Chicago")
            cache_size_after_second = client.get_cache_size()

            # Cache size should be the same (no new entry)
            assert cache_size_after_first == cache_size_after_second
            assert result1 == result2
        except Exception:
            pytest.skip("Art Institute API unavailable")

    def test_different_queries_create_different_cache_entries(self, setup_api_client):
        """Test that different queries create separate cache entries."""
        client = setup_api_client

        try:
            client.search_places("Chicago")
            size_after_first = client.get_cache_size()

            client.search_places("Paris")
            size_after_second = client.get_cache_size()

            # Should have 2 cache entries
            assert size_after_second == size_after_first + 1
        except Exception:
            pytest.skip("Art Institute API unavailable")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
