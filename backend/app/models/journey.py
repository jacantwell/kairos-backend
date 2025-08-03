from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.id import PyObjectId


class GeoJsonPoint(BaseModel):
    """
    A model to represent a point in GeoJSON format, as required by MongoDB.
    The format is a dictionary with 'type' and 'coordinates' fields.
    Coordinates are stored as [longitude, latitude].
    """

    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]  # [longitude, latitude]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v):
        longitude, latitude = v
        if not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v


class TimeEstimate(BaseModel):
    """
    A model to represent a time estimate for future locations.
    This allows for specific dates, date ranges, or general text descriptions.
    """

    start_date: Optional[datetime] = Field(
        None, description="The earliest estimated date/time of arrival."
    )
    end_date: Optional[datetime] = Field(
        None, description="The latest estimated date/time of arrival."
    )
    description: Optional[str] = Field(
        ...,
        description="A textual description of the estimated time (e.g., 'Late July 2025', 'Morning of August 10th').",
        examples=["Sometime next week"],
    )


class HistoricLocation(BaseModel):
    """
    A model for a location that has been visited or is the user's current location.
    It uses a precise, non-negotiable timestamp.
    """

    location_name: str = Field(
        ...,
        description="A user-defined name for the location.",
        examples=["Col du Galibier Summit", "Campsite near Briançon"],
    )
    coordinates: GeoJsonPoint = Field(
        ..., description="The precise GPS coordinates of the location."
    )
    timestamp: datetime = Field(
        ..., description="The exact date and time the user was at this location."
    )
    notes: Optional[str] = Field(
        None,
        description="Optional user notes about this location (e.g., 'Great view', 'Refilled water bottles here').",
    )


class PlannedLocation(BaseModel):
    """
    A model for a future, planned location on the journey.
    It uses a flexible time estimate instead of a precise timestamp.
    """

    coordinates: GeoJsonPoint = Field(
        ..., description="The GPS coordinates of the planned location."
    )
    time_estimate: TimeEstimate = Field(
        ..., description="The estimated time of arrival at this location."
    )
    location_name: Optional[str] = Field(
        ...,
        description="A user-defined name for the planned location.",
        examples=["Turin", "Meeting point at the cafe"],
    )
    notes: Optional[str] = Field(
        None,
        description="Optional user notes about this planned stop (e.g., 'Need to buy supplies', 'Meet up with Sarah').",
    )


class Journey(BaseModel):
    """
    The main Journey model.
    It aggregates the historic and planned routes for a user's trip.
    """

    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(
        ...,
        description="The name of the journey.",
        examples=["Alps Crossing Summer 2025"],
    )
    description: str = Field(
        ..., description="A detailed description of the journey's purpose and goals."
    )
    user_id: str = Field(
        ..., description="The unique identifier for the user who owns this journey."
    )
    is_public: bool = Field(
        True, description="Whether this journey is visible to other users on the map."
    )
    route_history: List[HistoricLocation] = Field(
        default_factory=list,
        description="An ordered list of locations the user has already visited.",
    )
    planned_route: List[PlannedLocation] = Field(
        default_factory=list,
        description="An ordered list of planned future locations for the journey.",
    )
