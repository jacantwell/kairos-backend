from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DatabaseDep
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.security import Token

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token")
async def login(
    db: DatabaseDep, data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    Authenticate a user and return an access token.
    """
    found_users = await db.users.query({"username": data.username})

    if len(found_users) == 0:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    else:
        user = found_users[0]

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(
        subject=user.id, expires_delta=settings.ACCESS_TOKEN_EXPIRE_DELTA
    )

    return Token(access_token=access_token, token_type="bearer")
