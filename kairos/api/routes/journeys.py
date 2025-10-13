from typing import List

from fastapi import APIRouter, HTTPException
from kairos.api.deps import CurrentUserDep, DatabaseDep
from kairos.models.journeys import Journey
from kairos.models.markers import Marker

router = APIRouter(prefix="/journeys", tags=["journeys"])


@router.post("/")
async def create_journey(
    db: DatabaseDep, user: CurrentUserDep, journey: Journey
) -> Journey:
    """
    Register a new journey.
    """
    try:
        journey = await db.journeys.create(journey)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return journey


@router.get("/{journey_id}")
async def get_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> Journey:
    """
    Get a journey by ID.
    """
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    return journey


@router.post("/{journey_id}/markers")
async def add_marker_to_journey(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
    marker: Marker,
) -> Marker:
    """
    Add a marker to a journey.
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
        raise HTTPException(status_code=400, detail=str(e))

    return created_marker


@router.get("/{journey_id}/markers")
async def get_journey_markers(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
) -> List[Marker]:
    """
    Get all markers for a journey.
    """
    # Ensure the journey exists
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    try:
        markers = await db.markers.get_journey_markers(journey_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return markers


@router.delete("/{journey_id}/markers/{marker_id}")
async def delete_journey_marker(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
    marker_id: str,
) -> None:
    """
    Delete a marker from a journey.
    """
    # Ensure the journey exists
    journey = await db.journeys.read(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    try:
        await db.markers.delete(marker_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{journey_id}/journeys/nearby")
async def get_nearby_journeys(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
):
    """
    Get all journeys with markers near the markers of a given journey.
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
        raise HTTPException(status_code=400, detail=str(e))

    return journeys


@router.delete("/{journey_id}")
async def delete_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> None:
    try:
        await db.journeys.delete(journey_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{journey_id}/active")
async def toggle_active_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> None:
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
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # There is already an active journey, so we need to deactivate it
            active_journey.active = False
            try:
                await db.journeys.update(str(active_journey.id), active_journey)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    # Now activate the chosen journey
    journey = await db.journeys.read(journey_id)
    journey.active = True
    try:
        await db.journeys.update(journey_id, journey)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{journey_id}")
async def set_completed_journey(db: DatabaseDep, user: CurrentUserDep, journey_id: str):
    """
    Set a journey as completed.
    If a journey is complete it cannot be active.
    """
    journey = await db.journeys.read(journey_id)
    journey.active = False
    journey.completed = True
    try:
        await db.journeys.update(journey_id, journey)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{journey_id}/markers/{marker_id}")
async def update_journey_marker(
    db: DatabaseDep,
    user: CurrentUserDep,
    journey_id: str,
    marker_id: str,
    marker: Marker,
) -> None:
    """
    Update a marker in a journey.
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
        raise HTTPException(status_code=400, detail=str(e))
