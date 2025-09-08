from typing import List
from fastapi import APIRouter, HTTPException
from kairos.api.deps import CurrentUserDep, DatabaseDep
from kairos.models.journeys import Journey
from kairos.models.markers import Marker
from bson import ObjectId
from kairos.models.id import PyObjectId

router = APIRouter(prefix="/journeys", tags=["journeys"])


@router.post("/")
async def create_journey(
    db: DatabaseDep, user: CurrentUserDep, journey: Journey
) -> Journey:
    """
    Register a new journey.
    """

    journey = await db.journeys.create(journey)

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
    # user: CurrentUserDep,
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

    # Associate marker with journey
    marker.journey_id = PyObjectId(
        ObjectId(journey_id)
    )  # This is messy and may not work
    created_marker = await db.markers.create(marker)

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

    markers = await db.markers.get_journey_markers(journey_id)

    return markers


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
    journeys = await db.markers.get_journey_nearby_journeys(journey_id)

    return journeys


@router.delete("/{journey_id}")
async def delete_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> None:
    await db.journeys.delete(journey_id)


@router.patch("/{journey_id}/active")
async def toggle_active_journey(
    db: DatabaseDep, user: CurrentUserDep, journey_id: str
) -> None:
    # This is a the most basic implementation
    # TODO use a pipeline to just switch the bool
    # TOTHINK should there be validation of only 1 active journey here?
    journey = await db.journeys.read(journey_id)
    journey.active = not journey.active
    await db.journeys.update(journey_id, journey)


@router.patch("/{journey_id}")
async def set_completed_journey(db: DatabaseDep, user: CurrentUserDep, journey_id: str):
    """
    Set a journey as completed.
    If a journey is complete it cannot be active.
    """
    journey = await db.journeys.read(journey_id)
    journey.active = False
    journey.completed = True
    await db.journeys.update(journey_id, journey)
