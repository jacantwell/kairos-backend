from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import DatabaseDep

router = APIRouter()


@router.get("/")
def ping() -> Any:
    """
    Retrieve users.
    """
    return "pong"


@router.get("/mongodb")
async def ping_mongodb(db: DatabaseDep) -> Any:
    """
    Retrieve users.
    """
    try:
        return await db.ping()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
