import resend
import asyncio
from typing import List, Dict, Any
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from kairos.api.deps import CurrentUserDep, DatabaseDep
from kairos.core.config import settings
from kairos.core.security import (
    create_token,
    decode_token,
    get_password_hash,
)
from kairos.models.users import User
from kairos.models.journeys import Journey


class MessageResponse(BaseModel):
    """Standard message response model."""
    message: str


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", status_code=201, response_model=None)
async def register_user(db: DatabaseDep, user: User) -> None:
    """Register a new user and send verification email.

    Creates a new user account with hashed password, generates a verification token,
    and sends a verification email to the provided email address.

    Args:
        db: Database dependency for accessing data stores.
        user: User model containing registration information.

    Raises:
        HTTPException: 400 if email is already registered.

    Returns:
        None
    """
    existing_users = await db.users.query({"email": user.email})
    if existing_users:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = get_password_hash(user.password)
    try:
        await db.users.create(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

    # Generate verification token
    token = create_token(
        user.email, settings.VERIFICATION_TOKEN_EXPIRE_DELTA, scope="email_verification"
    )

    # Create email message
    verification_link = f"http://www.findkairos.com/verify?token={token}"
    html_content = f"""
    <p>Thanks for signing up! Please click the link below to verify your email address:</p>
    <a href="{verification_link}">Verify Email</a>
    """
    email_content: resend.Emails.SendParams = {
        "from": "Kairos <verify@send.findkairos.com>",
        "to": [user.email],
        "subject": "Verify Your Email Address",
        "html": html_content,
    }

    try:
        resend.Emails.send(email_content)
    except Exception as e:
        # Email sending failed, but user is already created
        # Log error but don't fail the registration
        pass


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(db: DatabaseDep, token: str) -> MessageResponse:
    """Verify user email address using verification token.

    Validates the verification token and marks the user's email as verified.

    Args:
        db: Database dependency for accessing data stores.
        token: Email verification token.

    Raises:
        HTTPException: 400 if token is invalid or expired.
        HTTPException: 404 if user is not found.
        HTTPException: 500 if multiple users found (data integrity error).

    Returns:
        MessageResponse: Confirmation message of verification status.
    """
    try:
        email = decode_token(token, scope="email_verification")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    users = await db.users.query({"email": email})
    if len(users) > 1:
        raise HTTPException(status_code=500, detail="Data integrity error: Multiple users found")
    if len(users) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user = users[0]

    if user.is_verified:
        return MessageResponse(message="Email already verified.")

    user.is_verified = True
    try:
        await db.users.update(str(user.id), user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify email: {str(e)}")
    return MessageResponse(message="Email verified successfully.")


@router.post("/reset-password", status_code=202, response_model=None)
async def reset_password(db: DatabaseDep, email: str) -> None:
    """Request password reset and send reset link via email.

    Generates a password reset token and sends a reset link to the user's email.
    Silently succeeds even if email is not found to prevent user enumeration.

    Args:
        db: Database dependency for accessing data stores.
        email: Email address of the user requesting password reset.

    Raises:
        HTTPException: 500 if multiple users found with the same email (data integrity error).

    Returns:
        None
    """
    users = await db.users.query({"email": email})
    if len(users) > 1:
        raise HTTPException(status_code=500, detail="Data integrity error: Multiple users found")
    elif len(users) == 0:
        return
    else:
        user = users[0]

    token = create_token(
        user.email, settings.PASSWORD_RESET_TOKEN_EXPIRE_DELTA, scope="password_reset"
    )

    # Create email message
    verification_link = f"http://www.findkairos.com/reset-password?token={token}"
    html_content = f"""
    <p>You have requested to change your password, please click the link below:</p>
    <a href="{verification_link}">Reset Password</a>
    """

    email_content: resend.Emails.SendParams = {
        "from": "Kairos <reset@send.findkairos.com>",
        "to": [user.email],
        "subject": "Verify Your Email Address",
        "html": html_content,
    }

    try:
        resend.Emails.send(email_content)
    except Exception as e:
        # Email sending failed, but we don't want to expose this to the user
        # for security reasons (prevents user enumeration)
        pass


@router.post("/update-password", response_model=MessageResponse)
async def update_password(db: DatabaseDep, token: str, new_password: str) -> MessageResponse:
    """Update user password using reset token.

    Validates the password reset token and updates the user's password.

    Args:
        db: Database dependency for accessing data stores.
        token: Password reset token.
        new_password: New password to set for the user.

    Raises:
        HTTPException: 400 if token is invalid or expired.
        HTTPException: 404 if user is not found or multiple users found.

    Returns:
        MessageResponse: Confirmation message of password update.
    """
    try:
        email = decode_token(token, scope="password_reset")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    users = await db.users.query({"email": email})
    if len(users) > 1:
        raise HTTPException(status_code=500, detail="Data integrity error: Multiple users found")
    if len(users) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user = users[0]

    user.password = get_password_hash(new_password)
    try:
        await db.users.update(str(user.id), user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update password: {str(e)}")
    return MessageResponse(message="Password updated successfully.")


@router.get("/me", response_model=User)
async def get_current_user(user: CurrentUserDep) -> User:
    """Get the current authenticated user.

    Retrieves the user profile for the currently authenticated user.

    Args:
        user: Current authenticated user from dependency injection.

    Returns:
        User: The current user's profile information.
    """
    return user


@router.get("/{user_id}", response_model=User)
async def get_user_by_id(db: DatabaseDep, user: CurrentUserDep, user_id: str) -> User:
    """Get a user by their ID.

    Retrieves user profile information by user ID.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        user_id: Unique identifier of the user to retrieve.

    Raises:
        HTTPException: 404 if user is not found.

    Returns:
        User: The requested user's profile information.
    """
    read_user = await db.users.read(user_id)
    if not read_user:
        raise HTTPException(status_code=404, detail="User not found")
    return read_user


@router.get("/{user_id}/journeys", response_model=List[Journey])
async def get_user_journeys(db: DatabaseDep, user: CurrentUserDep, user_id: str) -> List[Journey]:
    """Get all journeys for a specific user.

    Retrieves all journeys associated with the specified user ID.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        user_id: Unique identifier of the user whose journeys to retrieve.

    Raises:
        HTTPException: 400 if user_id is invalid.
        HTTPException: 500 if database query fails.

    Returns:
        List[Journey]: List of all journeys belonging to the user.
    """
    try:
        object_id = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    try:
        journeys = await db.journeys.query({"user_id": object_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve journeys: {str(e)}")
    return journeys


@router.get("/{user_id}/journeys/active", response_model=Journey)
async def get_active_journey(db: DatabaseDep, user: CurrentUserDep, user_id: str) -> Journey:
    """Get the active journey for a specific user.

    Retrieves the currently active journey for the specified user.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        user_id: Unique identifier of the user whose active journey to retrieve.

    Raises:
        HTTPException: 400 if user_id is invalid.
        HTTPException: 404 if no active journey is found.
        HTTPException: 500 if database query fails.

    Returns:
        Journey: The user's currently active journey.
    """
    try:
        object_id = ObjectId(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    try:
        journeys = await db.journeys.query({"user_id": object_id, "active": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active journey: {str(e)}")

    if not journeys:
        raise HTTPException(status_code=404, detail="No active journey found")
    return journeys[0]


@router.put("/{user_id}", response_model=User)
async def update_user(
    db: DatabaseDep, user: CurrentUserDep, user_id: str, updated_user: User
) -> User:
    """Update a user's profile information.

    Updates the user profile with the provided information. Password changes are
    not allowed through this endpoint.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        user_id: Unique identifier of the user to update.
        updated_user: User model containing the updated information.

    Raises:
        HTTPException: 404 if user is not found.
        HTTPException: 400 if password change is attempted.

    Returns:
        User: The updated user profile.
    """
    read_user = await db.users.read(user_id)
    if not read_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user.id = read_user.id  # Ensure the ID remains the same
    if updated_user.password != read_user.password:
        raise HTTPException(status_code=400, detail="Password cannot be changed here.")
    try:
        await db.users.update(user_id, updated_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")
    return updated_user


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(db: DatabaseDep, user: CurrentUserDep, user_id: str) -> MessageResponse:
    """Delete a user and all associated data.

    Permanently deletes a user account along with all their journeys and markers.
    This operation cannot be undone.

    Args:
        db: Database dependency for accessing data stores.
        user: Current authenticated user from dependency injection.
        user_id: Unique identifier of the user to delete.

    Raises:
        HTTPException: 404 if user is not found.

    Returns:
        MessageResponse: Confirmation message of successful deletion.
    """
    read_user = await db.users.read(user_id)
    if not read_user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        await asyncio.gather(
            db.users.delete(user_id),
            db.journeys.delete_user_journeys(user_id),
            db.markers.delete_user_markers(user_id),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    return MessageResponse(message="User deleted successfully.")
