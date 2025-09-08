from datetime import datetime
from typing import Optional

from pydantic import Field
from kairos.models.id import PyObjectId
from kairos.models.base import MongoModel


class Journey(MongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    description: str = ""
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.now)
    active: bool = False
    completed: bool = False
