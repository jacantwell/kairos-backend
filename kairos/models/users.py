from typing import Optional

from kairos.models.id import PyObjectId
from pydantic import BaseModel, Field


class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    password: str
