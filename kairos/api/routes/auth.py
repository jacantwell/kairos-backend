from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from kairos.api.deps import DatabaseDep
from kairos.core.config import settings
from kairos.core.security import create_token, decode_token, verify_password
from kairos.models.security import Tokens

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=Tokens)
async def login(
    db: DatabaseDep, data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Tokens:
    """Authenticate a user and return access and refresh tokens.

    Validates user credentials and generates JWT access and refresh tokens
    for authenticated sessions.

    Args:
        db: Database dependency for accessing data stores.
        data: OAuth2 password request form containing username (email) and password.

    Raises:
        HTTPException: 400 if username or password is incorrect.

    Returns:
        Tokens: Object containing access_token and refresh_token.
    """
    found_users = await db.users.query({"email": data.username})

    if len(found_users) == 0:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    else:
        user = found_users[0]

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_token(
        subject=user.id,
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_DELTA,
        scope="access",
    )

    refresh_token = create_token(
        subject=user.id,
        expires_delta=settings.REFRESH_TOKEN_EXPIRE_DELTA,
        scope="refresh",
    )

    return Tokens(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Tokens)
async def refresh(refresh_token: str) -> Tokens:
    """Refresh an access token using a refresh token.

    Validates a refresh token and generates a new access token. The same refresh
    token is returned for continued use.

    Args:
        refresh_token: Valid JWT refresh token.

    Raises:
        HTTPException: 400 if refresh token has expired.
        HTTPException: 403 if refresh token is invalid.

    Returns:
        Tokens: Object containing new access_token and the same refresh_token.

    Note:
        TODO: Add logic for refresh token rotation for improved security.
        This requires maintaining a record of blacklisted refresh tokens.
    """
    try:
        sub = decode_token(refresh_token, scope="refresh")
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Refresh token has expired")
    except Exception as e:
        raise HTTPException(status_code=403, detail="Invalid refresh token")
    new_access = create_token(
        subject=sub,
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_DELTA,
        scope="access",
    )
    # TODO Add logic for refresh token rotation as it is more secure
    # this requires keeping a record of blacklisted refresh tokens.
    return Tokens(access_token=new_access, refresh_token=refresh_token)
