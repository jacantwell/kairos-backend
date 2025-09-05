from typing import Optional

from kairos.models.id import PyObjectId
from pydantic import BaseModel, Field


class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: str
    name: str
    password: str
    phonenumber: Optional[str] = None
    country: Optional[str] = None
