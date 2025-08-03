from typing import Annotated

import jwt
from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from app.core.config import settings
from app.core.security import ALGORITHM
from app.database import Database
from app.models.security import TokenPayload
from app.models.users import User


async def get_db(request: Request) -> Database:
    return request.app.state.database


get_auth = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

DatabaseDep = Annotated[Database, Depends(get_db)]
TokenDep = Annotated[str, Depends(get_auth)]


async def get_current_user(db: DatabaseDep, token: TokenDep) -> User:
    """
    By decoding the JWT token and extracting the user ID,
    we can retrieve the user from the database.
    If the token is invalid or the user does not exist, an HTTPException is raised.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await db.users.read(token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
