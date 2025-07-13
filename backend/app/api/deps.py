from typing import Annotated
from fastapi import Request, Depends

from app.database import Database

async def get_db(request: Request) -> Database:
    return request.app.state.database

DatabaseDep = Annotated[Database, Depends(get_db)]