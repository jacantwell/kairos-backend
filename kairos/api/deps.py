from typing import Annotated

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from kairos.core.config import settings
from kairos.core.security import decode_token
from kairos.database import Database
from kairos.models.users import User
from pydantic import ValidationError


async def get_db(request: Request) -> Database:
    return request.app.state.database


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

DatabaseDep = Annotated[Database, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(db: DatabaseDep, token: TokenDep) -> User:
    """
    By decoding the JWT token and extracting the user ID,
    we can retrieve the user from the database.
    If the token is invalid or the user does not exist, an HTTPException is raised.
    """
    try:
        sub = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token has expired"
        )
    except (InvalidTokenError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {e}",
        )
    user = await db.users.read(sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
