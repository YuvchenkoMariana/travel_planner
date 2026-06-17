"""
Test automatic project completion status updates.
"""

from travel_planner import User, Project, Place, set_repository
from repository import InMemoryRepository


def test_automatic_completion_update():
    """Test that updating a place's visited status automatically updates project completion."""
    # Setup
    repo = InMemoryRepository()
    set_repository(repo)

    user = User.add_user("Alice")
    project = Project(user_id=user.id, name="Test Trip")
    repo.add_project(project)

    # Add places manually (bypassing API validation)
    place1 = Place("Place 1", "id1", "link1", project=project)
    place2 = Place("Place 2", "id2", "link2", project=project)
    project.places = [place1, place2]

    # Initially not completed
    assert project.is_completed() is False
    assert project.completed is False

    # Mark first place as visited
    place1.update_visited(True)

    # Should still not be completed (only 1 of 2 visited)
    assert project.is_completed() is False
    assert project.completed is False

    # Mark second place as visited
    place2.update_visited(True)

    # NOW it should be automatically completed!
    assert project.is_completed() is True
    assert project.completed is True

    print("✓ Automatic completion update works!")


def test_automatic_completion_with_sqlite():
    """Test that loaded projects from SQLite also have automatic completion."""
    from sqlite_repository import SQLiteRepository
    import os

    # Use temporary database
    db_path = "test_auto_complete.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    try:
        repo = SQLiteRepository(db_path)
        set_repository(repo)

        user = User.add_user("Bob")
        project = Project(user_id=user.id, name="Test Trip")

        # Add places manually
        place1 = Place("Place 1", "id1", "link1", project=project)
        place2 = Place("Place 2", "id2", "link2", project=project)
        project.places = [place1, place2]

        repo.add_project(project)

        # Load project from database
        loaded_project = repo.get_project_by_id(project.id)

        assert loaded_project is not None
        assert loaded_project.completed is False

        # Mark places as visited on the LOADED project
        loaded_project.places[0].update_visited(True)
        assert loaded_project.completed is False  # Still not complete

        loaded_project.places[1].update_visited(True)
        assert loaded_project.completed is True  # NOW complete!

        print("✓ Automatic completion works with SQLite!")

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    test_automatic_completion_update()
    test_automatic_completion_with_sqlite()
    print("\n✅ All automatic completion tests passed!")
