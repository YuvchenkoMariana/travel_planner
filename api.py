"""
FastAPI REST API for Travel Planner System.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

from travel_planner import User, Project, Place, set_repository
from sqlite_repository import SQLiteRepository

# Initialize FastAPI app
app = FastAPI(
    title="Travel Planner API",
    description="""
    API for managing travel projects and places, integrated with the Art Institute of Chicago API.

    ## Features

    * **Users**: Create and manage users
    * **Projects**: Create, update, and delete travel projects
    * **Places**: Add places to projects with automatic validation
    * **Completion Tracking**: Automatically track project completion status
    * **API Validation**: Places are validated against the Art Institute of Chicago API

    ## Quick Start

    1. Create a user: `POST /users`
    2. Create a project: `POST /projects`
    3. Add places: `POST /projects/{project_id}/places`
    4. Mark places as visited: `PATCH /projects/{project_id}/places/{external_id}`

    ## Business Rules

    * Maximum 10 places per project
    * Cannot delete projects with visited places
    * Places must exist in the Art Institute API
    * Projects are auto-completed when all places are visited
    """,
    version="1.0.0",
    contact={
        "name": "Travel Planner API",
        "url": "https://github.com/yourusername/travel-planner",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Users",
            "description": "Operations for managing users",
        },
        {
            "name": "Projects",
            "description": "Operations for managing travel projects",
        },
        {
            "name": "Places",
            "description": "Operations for managing places within projects",
        },
        {
            "name": "Health",
            "description": "Health check endpoint",
        },
    ]
)

# Initialize repository on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the database repository on startup."""
    repo = SQLiteRepository("travel_planner.db")
    set_repository(repo)


# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class PlaceCreate(BaseModel):
    """Request model for creating a place."""
    place_name: str = Field(..., description="Name of the place", min_length=1)
    notes: Optional[str] = Field(None, description="Optional notes about the place")


class PlaceResponse(BaseModel):
    """Response model for a place."""
    place_name: str
    external_id: Optional[str]
    api_link: Optional[str]
    notes: Optional[str]
    visited: bool

    class Config:
        from_attributes = True


class PlaceUpdate(BaseModel):
    """Request model for updating a place."""
    notes: Optional[str] = Field(None, description="Updated notes")
    visited: Optional[bool] = Field(None, description="Mark as visited/unvisited")


class ProjectCreate(BaseModel):
    """Request model for creating a project, optionally with places."""
    user_id: int = Field(..., description="ID of the user who owns this project", gt=0)
    name: str = Field(..., description="Project name", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Project description")
    start_date: Optional[date] = Field(None, description="Start date for the trip")
    places: Optional[List[PlaceCreate]] = Field(
        None,
        description="Optional list of places to add (1-10 places)",
        min_length=1,
        max_length=10
    )


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, description="Updated project name", min_length=1)
    description: Optional[str] = Field(None, description="Updated description")
    start_date: Optional[date] = Field(None, description="Updated start date")


class ProjectResponse(BaseModel):
    """Response model for a project."""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    start_date: Optional[date]
    completed: bool
    places: List[PlaceResponse]

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Request model for creating a user."""
    name: str = Field(..., description="User's name", min_length=1, max_length=100)


class UserResponse(BaseModel):
    """Response model for a user."""
    id: int
    name: str

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str


# ============================================================================
# Helper Functions
# ============================================================================

def project_to_response(project: Project) -> ProjectResponse:
    """Convert Project domain model to ProjectResponse."""
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        start_date=project.start_date,
        completed=project.completed,
        places=[place_to_response(p) for p in project.places]
    )


def place_to_response(place: Place) -> PlaceResponse:
    """Convert Place domain model to PlaceResponse."""
    return PlaceResponse(
        place_name=place.place_name,
        external_id=place.external_id,
        api_link=place.api_link,
        notes=place.notes,
        visited=place.visited
    )


def user_to_response(user: User) -> UserResponse:
    """Convert User domain model to UserResponse."""
    return UserResponse(id=user.id, name=user.name)


# ============================================================================
# User Endpoints
# ============================================================================

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user_data: UserCreate):
    """
    Create a new user.

    Returns the created user with auto-generated ID.
    """
    try:
        user = User.add_user(user_data.name)
        return user_to_response(user)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: int):
    """
    Get a user by ID.

    Returns 404 if user not found.
    """
    from travel_planner import get_repository
    repo = get_repository()
    user = repo.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

    return user_to_response(user)


# ============================================================================
# Project Endpoints
# ============================================================================

@app.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, tags=["Projects"])
async def create_project(project_data: ProjectCreate):
    """
    Create a new travel project, optionally with places.

    If places are provided, they will be validated against the Art Institute API.
    If no places are provided, an empty project is created.
    """
    from travel_planner import get_repository

    # Verify user exists
    repo = get_repository()
    user = repo.get_user_by_id(project_data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {project_data.user_id} not found")

    # If places are provided, use create_with_places
    if project_data.places:
        # Create Place objects
        places = [
            Place(place_name=p.place_name, notes=p.notes)
            for p in project_data.places
        ]

        try:
            # This will validate places against the API
            project = Project.create_with_places(
                user_id=project_data.user_id,
                name=project_data.name,
                places=places,
                description=project_data.description,
                start_date=project_data.start_date
            )

            # Save to database
            saved_project = repo.add_project(project)
            return project_to_response(saved_project)

        except ValueError as e:
            # Distinguish between validation errors (400) and API validation errors (422)
            # If error message mentions "not found in Art Institute API", use 422
            if "not found in Art Institute API" in str(e):
                raise HTTPException(status_code=422, detail=str(e))
            else:
                raise HTTPException(status_code=400, detail=str(e))

    # No places provided - create empty project
    else:
        project = Project(
            user_id=project_data.user_id,
            name=project_data.name,
            description=project_data.description,
            start_date=project_data.start_date
        )

        saved_project = repo.add_project(project)
        return project_to_response(saved_project)


@app.get("/projects", response_model=List[ProjectResponse], tags=["Projects"])
async def list_projects(user_id: Optional[int] = None):
    """
    List all travel projects.
    Optionally filter by user_id.
    """
    projects = Project.list_projects(user_id=user_id)
    return [project_to_response(p) for p in projects]


@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def get_project(project_id: int):
    """Get a single travel project by ID."""
    project = Project.get_by_id(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    return project_to_response(project)


@app.put("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def update_project(project_id: int, project_data: ProjectUpdate):
    """Update travel project information (Name, Description, Start Date)."""
    from travel_planner import get_repository

    project = Project.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    # Update project fields
    project.update_project(
        name=project_data.name,
        description=project_data.description,
        start_date=project_data.start_date
    )

    # Save to database
    repo = get_repository()
    repo.update_project(project)

    return project_to_response(project)


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Projects"])
async def delete_project(project_id: int):
    """
    Delete a travel project.
    A project cannot be deleted if any of its places are already marked as visited.
    """
    project = Project.get_by_id(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    if not project.can_delete():
        raise HTTPException(
            status_code=400,
            detail="Cannot delete project: it has places marked as visited"
        )

    success = project.delete_project()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete project")


# ============================================================================
# Place Endpoints
# ============================================================================

@app.post("/projects/{project_id}/places", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, tags=["Places"])
async def add_place_to_project(project_id: int, place_data: PlaceCreate):
    """
    Add a place to an existing project.
    The place is validated against the Art Institute API before being added.
    """
    from travel_planner import get_repository

    project = Project.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    # Create place
    place = Place(place_name=place_data.place_name, notes=place_data.notes)

    try:
        success = project.add_place(place)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot add place: project has reached maximum of {Project.MAX_PLACES} places"
            )

        # Save to database
        repo = get_repository()
        repo.update_project(project)

        return project_to_response(project)

    except ValueError as e:
        # Distinguish between validation errors (400) and API validation errors (422)
        if "not found in Art Institute API" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


@app.get("/projects/{project_id}/places", response_model=List[PlaceResponse], tags=["Places"])
async def list_places(project_id: int):
    """List all places for a project."""
    project = Project.get_by_id(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    return [place_to_response(p) for p in project.get_places()]


@app.get("/projects/{project_id}/places/{external_id}", response_model=PlaceResponse, tags=["Places"])
async def get_place(project_id: int, external_id: str):
    """Get a single place within a project by its external ID."""
    project = Project.get_by_id(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    place = project.get_place(external_id)
    if place is None:
        raise HTTPException(
            status_code=404,
            detail=f"Place with external_id '{external_id}' not found in project {project_id}"
        )

    return place_to_response(place)


@app.patch("/projects/{project_id}/places/{external_id}", response_model=PlaceResponse, tags=["Places"])
async def update_place(project_id: int, external_id: str, place_data: PlaceUpdate):
    """
    Update a place within a project.
    Can update notes and/or visited status.
    """
    from travel_planner import get_repository

    project = Project.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    place = project.get_place(external_id)
    if place is None:
        raise HTTPException(
            status_code=404,
            detail=f"Place with external_id '{external_id}' not found in project {project_id}"
        )

    # Update place fields
    if place_data.notes is not None:
        place.update_notes(place_data.notes)

    if place_data.visited is not None:
        place.update_visited(place_data.visited)
        project.update_completion_status()

    # Save to database
    repo = get_repository()
    repo.update_project(project)

    return place_to_response(place)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the service status and name.
    """
    return {"status": "healthy", "service": "travel-planner-api"}


# ============================================================================
# Run with: uvicorn api:app --reload
# ============================================================================
