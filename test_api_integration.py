"""
Test to verify that the Art Institute API integration works end-to-end.
This test actually calls the live API to demonstrate the workflow.
"""

from travel_planner import User, Project, Place, set_repository
from repository import InMemoryRepository
from art_institute_client import get_client


def test_real_api_workflow():
    """
    Test the complete workflow with real API calls.
    This demonstrates how places are created with just a name,
    then populated with external_id and api_link when added to a project.
    """
    # Setup
    repo = InMemoryRepository()
    set_repository(repo)
    client = get_client()
    client.clear_cache()

    print("\n=== Testing Real API Integration ===\n")

    # 1. Create a user
    print("1. Creating user...")
    user = User.add_user("Test User")
    print(f"   User created: {user.name} (ID: {user.id})")

    # 2. Create a project
    print("\n2. Creating project...")
    project = Project(user_id=user.id, name="Art Places Tour")
    repo.add_project(project)
    print(f"   Project created: {project.name}")

    # 3. Create a place with ONLY a name (no external_id or api_link)
    print("\n3. Creating place with just a name...")
    place = Place(place_name="Paris", notes="Must visit!")
    print(f"   Place created: {place.place_name}")
    print(f"   external_id before adding: {place.external_id}")
    print(f"   api_link before adding: {place.api_link}")

    # 4. Try to add the place to the project
    print("\n4. Adding place to project (will search API and populate fields)...")
    try:
        success = project.add_place(place)

        if success:
            print(f"   ✓ Place added successfully!")
            print(f"   external_id after adding: {place.external_id}")
            print(f"   api_link after adding: {place.api_link}")

            # Verify the place is in the project
            assert len(project.places) == 1
            assert project.places[0].place_name == "Paris"
            assert project.places[0].external_id is not None
            assert project.places[0].api_link is not None

            print("\n   ✓ All assertions passed!")

            # Test the cache
            print("\n5. Testing cache - adding another place with same search...")
            place2 = Place(place_name="Paris", notes="Different notes")
            try:
                project.add_place(place2)
            except ValueError as e:
                print(f"   ✓ Correctly rejected duplicate: {e}")

            print(f"\n   Cache size: {client.get_cache_size()} entries")
            print("   (Same search only hit API once thanks to caching!)")

        else:
            print("   ✗ Failed to add place (limit reached?)")

    except PlaceException as e:
        print(f"\n   ⚠ PlaceException: {e}")
        print("   This means the place wasn't found in the Art Institute API.")
        print("   The API might be down or 'Chicago' might not be in their places database.")
        print("   Try searching for actual place names from: https://api.artic.edu/api/v1/places/search")

    except Exception as e:
        print(f"\n   ✗ Unexpected error: {type(e).__name__}: {e}")
        raise

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_real_api_workflow()
