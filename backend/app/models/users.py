from typing import Optional

from pydantic import BaseModel, Field

from app.models.id import PyObjectId

class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: str
    name: str
    phone_number: str
    description: str