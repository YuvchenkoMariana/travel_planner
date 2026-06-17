from typing import Optional, List
from datetime import date


# Global repository instance - will be set by the application
_repository = None


def set_repository(repo):
    """Set the global repository instance."""
    global _repository
    _repository = repo


def get_repository():
    """Get the global repository instance."""
    return _repository


class Place:
    """Represents a place within a travel project."""

    def __init__(self, place_name: str,
                 external_id: Optional[str] = None,
                 api_link: Optional[str] = None,
                 notes: Optional[str] = None,
                 visited: bool = False,
                 project: Optional['Project'] = None):
        """
        Initialize a Place.

        Args:
            place_name: Name of the place
            external_id: External ID from the Art Institute API (populated when added to project)
            api_link: Link to the place in the external API (populated when added to project)
            notes: Optional notes about the place
            visited: Whether the place has been visited (default: False)
            project: Back-reference to parent project (for automatic completion updates)
        """
        self.place_name = place_name
        self.external_id = external_id
        self.api_link = api_link
        self.notes = notes
        self.visited = visited
        self._project = project

    def update_notes(self, notes: str) -> None:
        """
        Update the notes for this place.

        Args:
            notes: New notes text
        """
        self.notes = notes

    def update_visited(self, visited: bool) -> None:
        """
        Update the visited status of this place.
        Automatically updates the parent project's completion status.

        Args:
            visited: New visited status
        """
        self.visited = visited
        # Automatically update parent project completion status
        if self._project is not None:
            self._project.update_completion_status()


class Project:
    """Represents a travel project containing multiple places."""

    MAX_PLACES = 10

    def __init__(self,
                 user_id: int,
                 name: str,
                 project_id: Optional[int] = None,
                 description: Optional[str] = None,
                 start_date: Optional[date] = None):
        """
        Initialize a Project.

        Args:
            user_id: ID of the user who owns this project
            name: Name of the project
            project_id: Optional project ID
            description: Optional description of the project
            start_date: Optional start date for the travel
        """
        self.id = project_id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.start_date = start_date
        self.places: List[Place] = []
        self.completed = False

    @classmethod
    def create_with_places(cls,
                          user_id: int,
                          name: str,
                          places: List[Place],
                          description: Optional[str] = None,
                          start_date: Optional[date] = None) -> 'Project':
        """
        Create a project with multiple places in one operation.
        Used for creating a project with places imported from third-party API.

        Args:
            user_id: ID of the user who owns this project
            name: Name of the project
            places: List of Place objects to add to the project
            description: Optional description
            start_date: Optional start date

        Returns:
            Project: Newly created project with places

        Raises:
            ValueError: If more than MAX_PLACES places provided, duplicate place names found,
                       or if a place cannot be found in the Art Institute API
        """
        from art_institute_client import get_client

        # Validate places count
        if len(places) > cls.MAX_PLACES:
            raise ValueError(f"Cannot add more than {cls.MAX_PLACES} places to a project")

        # Check for duplicate place names
        place_names = [p.place_name.lower() for p in places]
        if len(place_names) != len(set(place_names)):
            raise ValueError("Duplicate place names found in places list")

        # Validate each place against the API and populate external_id/api_link
        client = get_client()
        for place in places:
            api_place = client.find_place_by_name(place.place_name)
            if api_place is None:
                raise ValueError(
                    f"Place '{place.place_name}' not found in Art Institute API"
                )
            # Populate external_id and api_link from API
            place.external_id = api_place["id"]
            place.api_link = api_place["api_link"]

        # Create project and add places
        project = cls(
            user_id=user_id,
            name=name,
            description=description,
            start_date=start_date
        )
        project.places = places.copy()
        # Set back-reference to project for automatic completion updates
        for place in project.places:
            place._project = project
        project.update_completion_status()

        return project

    def add_place(self, place: Place) -> bool:
        """
        Add a place to the project.
        No more than 10 places can be added to a project.
        The place is validated against the Art Institute API and external_id/api_link are populated.

        Args:
            place: Place object to add (only place_name required)

        Returns:
            bool: True if place was added successfully, False if limit reached

        Raises:
            ValueError: If place with same place_name already exists in project,
                       or if place cannot be found in the Art Institute API
        """
        from art_institute_client import get_client

        # Check if limit reached
        if len(self.places) >= self.MAX_PLACES:
            return False

        # Check for duplicate place_name
        if any(p.place_name.lower() == place.place_name.lower() for p in self.places):
            raise ValueError(f"Place with name '{place.place_name}' already exists in project")

        # Search for place in API and populate external_id and api_link
        client = get_client()
        api_place = client.find_place_by_name(place.place_name)

        if api_place is None:
            raise ValueError(
                f"Place '{place.place_name}' not found in Art Institute API"
            )

        # Populate external_id and api_link from API
        place.external_id = api_place["id"]
        place.api_link = api_place["api_link"]

        # Set back-reference to project for automatic completion updates
        place._project = self

        # Add place to list
        self.places.append(place)
        self.update_completion_status()

        return True

    def get_places(self) -> List[Place]:
        """
        Get all places in this project.

        Returns:
            List of Place objects
        """
        return self.places.copy()

    def get_place(self, external_id: str) -> Optional[Place]:
        """
        Get a single place within this project by its external ID.

        Args:
            external_id: External ID of the place from the Art Institute API

        Returns:
            Place object if found, None otherwise
        """
        for place in self.places:
            if place.external_id == external_id:
                return place
        return None

    def update_project(self, name: Optional[str] = None,
                      description: Optional[str] = None,
                      start_date: Optional[date] = None) -> None:
        """
        Update travel project information.

        Args:
            name: New project name (optional)
            description: New project description (optional)
            start_date: New start date (optional)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if start_date is not None:
            self.start_date = start_date

    @staticmethod
    def list_projects(user_id: Optional[int] = None) -> List['Project']:
        """
        List all travel projects, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter projects

        Returns:
            List of Project objects
        """
        repo = get_repository()
        if repo is None:
            return []
        return repo.list_projects(user_id)

    @staticmethod
    def get_by_id(project_id: int) -> Optional['Project']:
        """
        Get a project by its ID.

        Args:
            project_id: ID of the project to retrieve

        Returns:
            Project object if found, None otherwise
        """
        repo = get_repository()
        if repo is None:
            return None
        return repo.get_project_by_id(project_id)

    def delete_project(self) -> bool:
        """
        Delete this project.
        A project cannot be deleted if any of its places are already marked as visited.

        Returns:
            bool: True if deleted successfully, False if deletion not allowed
        """
        if not self.can_delete():
            return False

        repo = get_repository()
        if repo is None or self.id is None:
            return False

        return repo.delete_project(self.id)

    @staticmethod
    def delete_by_id(project_id: int) -> bool:
        """
        Delete a project by its ID.
        A project cannot be deleted if any of its places are already marked as visited.

        Args:
            project_id: ID of the project to delete

        Returns:
            bool: True if deleted successfully, False if project not found or deletion not allowed
        """
        project = Project.get_by_id(project_id)
        if project is None:
            return False
        return project.delete_project()

    def can_delete(self) -> bool:
        """
        Check if this project can be deleted.

        Returns:
            bool: True if no places are visited, False otherwise
        """
        return not any(place.visited for place in self.places)

    def is_completed(self) -> bool:
        """
        Check if all places in the project have been visited.

        Returns:
            bool: True if all places are visited, False otherwise
        """
        if not self.places:
            return False
        return all(place.visited for place in self.places)

    def update_completion_status(self) -> None:
        """
        Update the completed status based on whether all places are visited.

        This is called automatically when a place's visited status is updated via
        place.update_visited(). Can also be called manually if needed.
        """
        self.completed = self.is_completed()


class User:
    """Represents a user of the travel system."""

    def __init__(self, user_id: int, name: str):
        """
        Initialize a User.

        Args:
            user_id: Unique user ID
            name: User's name
        """
        self.id = user_id
        self.name = name

    @staticmethod
    def add_user(name: str) -> 'User':
        """
        Add a new user to the system.

        Args:
            name: Name of the new user

        Returns:
            User: Newly created User object
        """
        repo = get_repository()
        if repo is None:
            raise RuntimeError("Repository not initialized")

        user = User(user_id=repo.get_next_user_id(), name=name)
        return repo.add_user(user)

    def update_user(self, name: Optional[str] = None) -> None:
        """
        Update user information.

        Args:
            name: New name for the user (optional)
        """
        if name is not None:
            self.name = name



