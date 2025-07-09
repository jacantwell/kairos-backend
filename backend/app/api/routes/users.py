import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/"
)
def read_users() -> Any:
    """
    Retrieve users.
    """

    return "pong"

