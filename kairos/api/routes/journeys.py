from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from kairos.api.deps import CurrentUserDep, DatabaseDep
from kairos.models.journeys import Journey
from kairos.models.markers import Marker


class MessageResponse(BaseModel):
    """Standard message response model."""
    message: str


router = APIRouter(prefix="/journeys", tags=["journeys"])


@router.post("/", status_code=201, response_model=Journey)
async def create_journey(
    db: DatabaseDep, user: CurrentUserDep, journey: Journey
) -> Journey:
    """Create a new journey.

    Creates a new journey for the authenticated user.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey: Journey model containing the journey information.

    Raises:
        HTTPException: 400 if journey creation fails.

    Returns:
        Journey: The newly created journey.
    """
    try:
        journey = await db.journeys.create(journey)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create journey: {str(e)}")

    return journey


@router.get("/{journey_id}", response_model=Journey)
async def get_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> Journey:
    """Get a journey by ID.

    Retrieves a specific journey by its unique identifier.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey to retrieve.

    Raises:
        HTTPException: 404 if journey is not found.

    Returns:
        Journey: The requested journey.
    """
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    return journey


@router.post("/{journey_id}/markers", status_code=201, response_model=Marker)
async def add_marker_to_journey(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
    marker: Marker,
) -> Marker:
    """Add a marker to a journey.

    Creates a new marker associated with the specified journey and the
    authenticated user.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey to add the marker to.
        marker: Marker model containing the marker information.

    Raises:
        HTTPException: 404 if journey is not found.
        HTTPException: 400 if marker creation fails.

    Returns:
        Marker: The newly created marker.
    """
    # Ensure the journey exists
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    # Associate marker with the user
    marker.owner_id = user.id
    try:
        created_marker = await db.markers.create(marker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create marker: {str(e)}")

    return created_marker


@router.get("/{journey_id}/markers", response_model=List[Marker])
async def get_journey_markers(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
) -> List[Marker]:
    """Get all markers for a journey.

    Retrieves all markers associated with the specified journey.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey whose markers to retrieve.

    Raises:
        HTTPException: 404 if journey is not found.
        HTTPException: 400 if retrieval fails.

    Returns:
        List[Marker]: List of all markers belonging to the journey.
    """
    # Ensure the journey exists
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    try:
        markers = await db.markers.get_journey_markers(journey_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve markers: {str(e)}")

    return markers


@router.delete("/{journey_id}/markers/{marker_id}", status_code=204, response_model=None)
async def delete_journey_marker(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
    marker_id: str,
) -> None:
    """Delete a marker from a journey.

    Permanently removes a marker from the specified journey.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey containing the marker.
        marker_id: Unique identifier of the marker to delete.

    Raises:
        HTTPException: 404 if journey is not found.
        HTTPException: 400 if deletion fails.

    Returns:
        None
    """
    # Ensure the journey exists
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    try:
        await db.markers.delete(marker_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete marker: {str(e)}")


@router.get("/{journey_id}/journeys/nearby", response_model=List[str])
async def get_nearby_journeys(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
) -> List[str]:
    """Get all journeys with markers near the markers of a given journey.

    Retrieves journeys that have markers geographically close to the markers
    of the specified journey.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey to find nearby journeys for.

    Raises:
        HTTPException: 404 if journey is not found.
        HTTPException: 400 if retrieval fails.

    Returns:
        List[Journey]: List of journeys with nearby markers.
    """
    # Ensure the journey exists and belongs to the user
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    # if journey.user_id != str(user.id):
    #     raise HTTPException(status_code=403, detail="Access denied")

    # Get journeys
    try:
        journeys = await db.markers.get_journey_nearby_journeys(journey_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nearby journeys: {str(e)}")

    return journeys


@router.delete("/{journey_id}", status_code=204, response_model=None)
async def delete_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> None:
    """Delete a journey.

    Permanently removes a journey from the database.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey to delete.

    Raises:
        HTTPException: 404 if journey is not found.
        HTTPException: 500 if deletion fails.

    Returns:
        None
    """
    # Check if journey exists before deletion
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    try:
        await db.journeys.delete(journey_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete journey: {str(e)}")


@router.patch("/{journey_id}/active", status_code=204, response_model=None)
async def toggle_active_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> None:
    """Toggle a journey's active status.

    Sets the specified journey as active and deactivates any other active journey
    for the user. If the specified journey is already active, it will be deactivated.
    Only one journey can be active per user at a time.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey to toggle.

    Raises:
        HTTPException: 400 if update fails.

    Returns:
        None
    """
    # This is a the most basic implementation
    # TODO use a pipeline to just switch the bool
    # TOTHINK should there be validation of only 1 active journey here?

    user_active_journeys = await db.journeys.query({"user_id": user.id, "active": True})

    if len(user_active_journeys) == 1:
        active_journey = user_active_journeys[0]
        # If the chosen journey is the active one, just toggle it and exit
        if str(active_journey.id) == journey_id:
            active_journey.active = not active_journey.active
            try:
                await db.journeys.update(journey_id, active_journey)
                return
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update journey: {str(e)}")
        else:
            # There is already an active journey, so we need to deactivate it
            active_journey.active = False
            try:
                await db.journeys.update(str(active_journey.id), active_journey)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to deactivate journey: {str(e)}")

    # Now activate the chosen journey
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    journey.active = True
    try:
        await db.journeys.update(journey_id, journey)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate journey: {str(e)}")


@router.patch("/{journey_id}", status_code=204, response_model=None)
async def set_completed_journey(db: DatabaseDep, user: CurrentUserDep, journey_id: str) -> None:
    """Set a journey as completed.

    Marks a journey as completed and automatically deactivates it.
    A completed journey cannot be active.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey to mark as completed.

    Raises:
        HTTPException: 404 if journey is not found.
        HTTPException: 500 if update fails.

    Returns:
        None
    """
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    journey.active = False
    journey.completed = True
    try:
        await db.journeys.update(journey_id, journey)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete journey: {str(e)}")


@router.put("/{journey_id}/markers/{marker_id}", response_model=Marker)
async def update_journey_marker(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
    marker_id: str,
    marker: Marker,
) -> Marker:
    """Update a marker in a journey.

    Updates an existing marker with new information while preserving its ID
    and ownership.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        journey_id: Unique identifier of the journey containing the marker.
        marker_id: Unique identifier of the marker to update.
        marker: Marker model containing the updated information.

    Raises:
        HTTPException: 404 if journey or marker is not found.
        HTTPException: 400 if update fails.

    Returns:
        Marker: The updated marker.
    """
    # Ensure the journey exists
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    existing_marker = await db.markers.read(marker_id)
    if not existing_marker:
        raise HTTPException(status_code=404, detail="Marker not found")

    marker.id = existing_marker.id
    marker.owner_id = existing_marker.owner_id
    try:
        await db.markers.update(marker_id, marker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update marker: {str(e)}")

    return marker
