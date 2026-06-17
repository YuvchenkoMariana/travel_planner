import sqlite3
from typing import Optional, List
from contextlib import contextmanager
from datetime import date
from travel_planner import User, Project, Place
from repository import Repository


class SQLiteRepository(Repository):
    """
    SQLite implementation of Repository.
    Stores users, projects, and places in a SQLite database.
    """

    def __init__(self, db_path: str = "travel_system.db"):
        """
        Initialize SQLite repository with database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints (disabled by default in SQLite)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)

            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    start_date TEXT,
                    completed INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
            """)

            # Places table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    place_name TEXT NOT NULL,
                    external_id TEXT,
                    api_link TEXT,
                    notes TEXT,
                    visited INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_user_id
                ON projects(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_places_project_id
                ON places(project_id)
            """)

    def add_user(self, user: User) -> User:
        """
        Add a user to the repository.

        Args:
            user: User object to add

        Returns:
            The added User object with assigned ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user.id is None:
                user.id = self.get_next_user_id()

            cursor.execute(
                "INSERT INTO users (id, name) VALUES (?, ?)",
                (user.id, user.name)
            )
            return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: ID of the user

        Returns:
            User object if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return User(user_id=row["id"], name=row["name"])

    def update_user(self, user: User) -> bool:
        """
        Update an existing user.

        Args:
            user: User object with updated data

        Returns:
            True if updated successfully, False if user not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET name = ? WHERE id = ?",
                (user.name, user.id)
            )
            return cursor.rowcount > 0

    def list_users(self) -> List[User]:
        """
        List all users.

        Returns:
            List of all User objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id")
            rows = cursor.fetchall()

            return [User(user_id=row["id"], name=row["name"]) for row in rows]

    def add_project(self, project: Project) -> Project:
        """
        Add a project to the repository.

        Args:
            project: Project object to add

        Returns:
            The added Project object with assigned ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if project.id is None:
                project.id = self.get_next_project_id()

            start_date_str = project.start_date.isoformat() if project.start_date else None

            cursor.execute(
                """INSERT INTO projects
                   (id, user_id, name, description, start_date, completed)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project.id, project.user_id, project.name,
                 project.description, start_date_str, int(project.completed))
            )

            # Add all places
            for place in project.places:
                cursor.execute(
                    """INSERT INTO places
                       (project_id, place_name, external_id, api_link, notes, visited)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (project.id, place.place_name, place.external_id,
                     place.api_link, place.notes, int(place.visited))
                )

            return project

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            project_id: ID of the project

        Returns:
            Project object if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            # Parse start_date
            start_date = None
            if row["start_date"]:
                start_date = date.fromisoformat(row["start_date"])

            # Create project
            project = Project(
                user_id=row["user_id"],
                name=row["name"],
                project_id=row["id"],
                description=row["description"],
                start_date=start_date
            )
            project.completed = bool(row["completed"])

            # Load places
            cursor.execute(
                "SELECT * FROM places WHERE project_id = ? ORDER BY id",
                (project_id,)
            )
            place_rows = cursor.fetchall()

            project.places = [
                Place(
                    place_name=place_row["place_name"],
                    external_id=place_row["external_id"],
                    api_link=place_row["api_link"],
                    notes=place_row["notes"],
                    visited=bool(place_row["visited"]),
                    project=project
                )
                for place_row in place_rows
            ]

            return project

    def update_project(self, project: Project) -> bool:
        """
        Update an existing project.

        Args:
            project: Project object with updated data

        Returns:
            True if updated successfully, False if project not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            start_date_str = project.start_date.isoformat() if project.start_date else None

            cursor.execute(
                """UPDATE projects
                   SET user_id = ?, name = ?, description = ?,
                       start_date = ?, completed = ?
                   WHERE id = ?""",
                (project.user_id, project.name, project.description,
                 start_date_str, int(project.completed), project.id)
            )

            if cursor.rowcount == 0:
                return False

            # Delete existing places and re-insert
            cursor.execute("DELETE FROM places WHERE project_id = ?", (project.id,))

            # Re-insert places
            for place in project.places:
                cursor.execute(
                    """INSERT INTO places
                       (project_id, place_name, external_id, api_link, notes, visited)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (project.id, place.place_name, place.external_id,
                     place.api_link, place.notes, int(place.visited))
                )

            return True

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project by ID.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if deleted successfully, False if project not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if project exists
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if cursor.fetchone() is None:
                return False

            # Delete project (places will be cascade deleted)
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return True

    def list_projects(self, user_id: Optional[int] = None) -> List[Project]:
        """
        List all projects, optionally filtered by user_id.

        Args:
            user_id: Optional user ID to filter projects

        Returns:
            List of Project objects
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if user_id is not None:
                cursor.execute(
                    "SELECT * FROM projects WHERE user_id = ? ORDER BY id",
                    (user_id,)
                )
            else:
                cursor.execute("SELECT * FROM projects ORDER BY id")

            rows = cursor.fetchall()
            projects = []

            for row in rows:
                # Parse start_date
                start_date = None
                if row["start_date"]:
                    start_date = date.fromisoformat(row["start_date"])

                # Create project
                project = Project(
                    user_id=row["user_id"],
                    name=row["name"],
                    project_id=row["id"],
                    description=row["description"],
                    start_date=start_date
                )
                project.completed = bool(row["completed"])

                # Load places
                cursor.execute(
                    "SELECT * FROM places WHERE project_id = ? ORDER BY id",
                    (row["id"],)
                )
                place_rows = cursor.fetchall()

                project.places = [
                    Place(
                        place_name=place_row["place_name"],
                        external_id=place_row["external_id"],
                        api_link=place_row["api_link"],
                        notes=place_row["notes"],
                        visited=bool(place_row["visited"]),
                        project=project
                    )
                    for place_row in place_rows
                ]

                projects.append(project)

            return projects

    def get_next_user_id(self) -> int:
        """
        Generate the next available user ID.

        Returns:
            Next user ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) as max_id FROM users")
            row = cursor.fetchone()
            max_id = row["max_id"]
            return 1 if max_id is None else max_id + 1

    def get_next_project_id(self) -> int:
        """
        Generate the next available project ID.

        Returns:
            Next project ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) as max_id FROM projects")
            row = cursor.fetchone()
            max_id = row["max_id"]
            return 1 if max_id is None else max_id + 1

    def clear(self) -> None:
        """
        Clear all data from the repository.
        Useful for testing.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM places")
            cursor.execute("DELETE FROM projects")
            cursor.execute("DELETE FROM users")
