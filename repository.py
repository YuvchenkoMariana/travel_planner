from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from travel_planner import User, Project, Place


class Repository(ABC):
    """
    Abstract base class for data storage.
    Implement this interface for different storage backends (in-memory, SQLite, etc.)
    """

    @abstractmethod
    def add_user(self, user: User) -> User:
        """Add a user to the repository."""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        pass

    @abstractmethod
    def update_user(self, user: User) -> bool:
        """Update an existing user."""
        pass

    @abstractmethod
    def list_users(self) -> List[User]:
        """List all users."""
        pass

    @abstractmethod
    def add_project(self, project: Project) -> Project:
        """Add a project to the repository."""
        pass

    @abstractmethod
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        pass

    @abstractmethod
    def update_project(self, project: Project) -> bool:
        """Update an existing project."""
        pass

    @abstractmethod
    def delete_project(self, project_id: int) -> bool:
        """Delete a project by ID."""
        pass

    @abstractmethod
    def list_projects(self, user_id: Optional[int] = None) -> List[Project]:
        """List all projects, optionally filtered by user_id."""
        pass

    @abstractmethod
    def get_next_user_id(self) -> int:
        """Generate the next available user ID."""
        pass

    @abstractmethod
    def get_next_project_id(self) -> int:
        """Generate the next available project ID."""
        pass


class InMemoryRepository(Repository):
    """
    In-memory implementation of Repository using dictionaries and lists.
    Suitable for testing. Can be swapped with SQLiteRepository for production.
    """

    def __init__(self):
        """Initialize empty storage."""
        self._users: Dict[int, User] = {}
        self._projects: Dict[int, Project] = {}
        self._next_user_id: int = 1
        self._next_project_id: int = 1

    def add_user(self, user: User) -> User:
        """
        Add a user to the repository.

        Args:
            user: User object to add

        Returns:
            The added User object with assigned ID
        """
        if user.id is None:
            user.id = self.get_next_user_id()
        self._users[user.id] = user
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: ID of the user

        Returns:
            User object if found, None otherwise
        """
        return self._users.get(user_id)

    def update_user(self, user: User) -> bool:
        """
        Update an existing user.

        Args:
            user: User object with updated data

        Returns:
            True if updated successfully, False if user not found
        """
        if user.id not in self._users:
            return False
        self._users[user.id] = user
        return True

    def list_users(self) -> List[User]:
        """
        List all users.

        Returns:
            List of all User objects
        """
        return list(self._users.values())

    def add_project(self, project: Project) -> Project:
        """
        Add a project to the repository.

        Args:
            project: Project object to add

        Returns:
            The added Project object with assigned ID
        """
        if project.id is None:
            project.id = self.get_next_project_id()
        self._projects[project.id] = project
        return project

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            project_id: ID of the project

        Returns:
            Project object if found, None otherwise
        """
        return self._projects.get(project_id)

    def update_project(self, project: Project) -> bool:
        """
        Update an existing project.

        Args:
            project: Project object with updated data

        Returns:
            True if updated successfully, False if project not found
        """
        if project.id not in self._projects:
            return False
        self._projects[project.id] = project
        return True

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project by ID.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if deleted successfully, False if project not found
        """
        if project_id not in self._projects:
            return False
        del self._projects[project_id]
        return True

    def list_projects(self, user_id: Optional[int] = None) -> List[Project]:
        """
        List all projects, optionally filtered by user_id.

        Args:
            user_id: Optional user ID to filter projects

        Returns:
            List of Project objects
        """
        projects = list(self._projects.values())
        if user_id is not None:
            projects = [p for p in projects if p.user_id == user_id]
        return projects

    def get_next_user_id(self) -> int:
        """
        Generate the next available user ID.

        Returns:
            Next user ID
        """
        user_id = self._next_user_id
        self._next_user_id += 1
        return user_id

    def get_next_project_id(self) -> int:
        """
        Generate the next available project ID.

        Returns:
            Next project ID
        """
        project_id = self._next_project_id
        self._next_project_id += 1
        return project_id

    def clear(self) -> None:
        """
        Clear all data from the repository.
        Useful for testing.
        """
        self._users.clear()
        self._projects.clear()
        self._next_user_id = 1
        self._next_project_id = 1
