from typing import Optional

from kairos.models.id import PyObjectId
from pydantic import BaseModel, Field
from kairos.models.base import MongoModel


class User(MongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: str
    name: str
    password: str
    phonenumber: Optional[str] = None
    country: Optional[str] = None
    is_verified: bool = False
