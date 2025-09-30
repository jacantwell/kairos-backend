import resend
import asyncio
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from kairos.api.deps import CurrentUserDep, DatabaseDep
from kairos.core.config import settings
from kairos.core.security import (
    create_token,
    decode_token,
    get_password_hash,
)
from kairos.models.users import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register_user(db: DatabaseDep, user: User) -> None:
    """
    Register a new user.
    """
    existing_users = await db.users.query({"email": user.email})
    if existing_users:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = get_password_hash(user.password)
    await db.users.create(user)

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

    resend.Emails.send(email_content)


@router.get("/verify-email")
async def verify_email(db: DatabaseDep, token: str):
    try:
        email = decode_token(token, scope="email_verification")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    users = await db.users.query({"email": email})
    if len(users) > 1:
        raise HTTPException(status_code=404, detail="Multiple users found")
    if len(users) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user = users[0]

    if user.is_verified:
        return {"message": "Email already verified."}

    user.is_verified = True
    await db.users.update(str(user.id), user)


@router.post("/reset-password")
async def reset_password(db: DatabaseDep, email: str):
    users = await db.users.query({"email": email})
    if len(users) > 1:
        raise HTTPException(status_code=404, detail="Multiple users found")
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

    resend.Emails.send(email_content)


@router.post("/update-password")
async def update_password(db: DatabaseDep, token: str, new_password: str):
    try:
        email = decode_token(token, scope="password_reset")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    users = await db.users.query({"email": email})
    if len(users) > 1:
        raise HTTPException(status_code=404, detail="Multiple users found")
    if len(users) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user = users[0]

    user.password = get_password_hash(new_password)
    await db.users.update(str(user.id), user)


@router.get("/me")
async def get_current_user(user: CurrentUserDep) -> User:
    """
    Get the current authenticated user.
    """
    return user


@router.get("/{user_id}")
async def get_user_by_id(db: DatabaseDep, user: CurrentUserDep, user_id: str) -> User:
    """
    Get a user by ID.
    """
    read_user = await db.users.read(user_id)
    if not read_user:
        raise HTTPException(status_code=404, detail="User not found")
    return read_user


@router.get("/{user_id}/journeys")
async def get_user_journeys(db: DatabaseDep, user: CurrentUserDep, user_id: str):
    """
    Get journeys for a specific user.
    """
    journeys = await db.journeys.query({"user_id": ObjectId(user_id)})
    return journeys


@router.get("/{user_id}/journeys/active")
async def get_active_journey(db: DatabaseDep, user: CurrentUserDep, user_id: str):
    """
    Get the active journey for a specific user.
    """
    journeys = await db.journeys.query({"user_id": ObjectId(user_id), "active": True})
    if not journeys:
        raise HTTPException(status_code=404, detail="No active journey found")
    return journeys[0]


@router.put("/{user_id}")
async def update_user(
    db: DatabaseDep, user: CurrentUserDep, user_id: str, updated_user: User
):
    """
    Update a user by ID.
    """
    read_user = await db.users.read(user_id)
    if not read_user:
        raise HTTPException(status_code=404, detail="User not found")
    updated_user.id = read_user.id  # Ensure the ID remains the same
    if updated_user.password != read_user.password:
        raise HTTPException(status_code=400, detail="Password cannot be changed here.")
    await db.users.update(user_id, updated_user)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(db: DatabaseDep, user: CurrentUserDep, user_id: str):
    """
    Delete a user by ID.
    """
    read_user = await db.users.read(user_id)
    if not read_user:
        raise HTTPException(status_code=404, detail="User not found")
    await asyncio.gather(
        db.users.delete(user_id),
        db.journeys.delete_user_journeys(user_id),
        db.markers.delete_user_markers(user_id),
    )
    return {"message": "User deleted successfully."}
