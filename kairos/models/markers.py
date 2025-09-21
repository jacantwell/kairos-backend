from datetime import date, datetime
from enum import Enum
from typing import List, Literal, Optional

from bson import ObjectId
from kairos.models.base import MongoModel
from kairos.models.id import PyObjectId
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [longitude, latitude]


class Marker(MongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    journey_id: PyObjectId
    owner_id: Optional[PyObjectId] = None
    marker_type: Literal["past", "plan"]
    coordinates: Coordinates
    timestamp: Optional[date] = None  # for journey markers
    estimated_time: Optional[date] = None  # for plan markers
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
