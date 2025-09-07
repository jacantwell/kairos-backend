from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from kairos.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_token(subject: str | Any, expires_delta: timedelta, scope: Optional[str] = None) -> str:
    """Creates a JWT token with an expiration time."""
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    if scope:
        to_encode.update({"scope": scope})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str, scope: Optional[str] = None) -> str:
    """Decodes a JWT token and returns the subject if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if scope and payload.get("scope") != scope:
            raise jwt.InvalidTokenError("Invalid token scope")
        subject = payload.get("sub")
        if subject is None:
            raise jwt.InvalidTokenError("Invalid token")
        return subject
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Could not validate credentials: {str(e)}")
    except Exception as e:
        raise jwt.InvalidTokenError(f"An error occurred: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies the password against the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Uses bcrypt to hash the password."""
    return pwd_context.hash(password)
