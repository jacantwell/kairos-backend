from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from kairos.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """Creates a JWT token with an expiration time."""
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_verification_token(subject: str | Any, expires_delta: timedelta) -> str:
    """Creates a JWT token with an expiration time."""
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject), "scope": "email_verification"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_verification_token(token: str) -> str:
    """Decodes a JWT token and returns the subject if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != "email_verification":
            raise jwt.InvalidTokenError("Invalid token scope")
        email = payload.get("sub")
        if email is None:
            raise jwt.InvalidTokenError("Invalid token")
        return email
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
