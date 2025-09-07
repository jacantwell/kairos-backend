from datetime import datetime
from typing import List, Literal, Optional
from enum import Enum
from kairos.models.id import PyObjectId
from pydantic import BaseModel, Field
from bson import ObjectId


class Coordinates(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [longitude, latitude]


class Marker(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    journey_id: PyObjectId
    marker_type: Literal["past", "plan"]
    coordinates: Coordinates
    timestamp: Optional[datetime] = None  # for journey markers
    estimated_time: Optional[str] = None  # for plan markers
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
