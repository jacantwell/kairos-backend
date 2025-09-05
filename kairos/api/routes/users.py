from fastapi import APIRouter, HTTPException
from kairos.api.deps import CurrentUserDep, DatabaseDep, MailDep
from kairos.core.security import (
    get_password_hash,
    create_verification_token,
    decode_verification_token,
)
from kairos.models.users import User
from fastapi_mail import MessageSchema, MessageType
from kairos.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register_user(db: DatabaseDep, fm: MailDep, user: User) -> None:
    """
    Register a new user.
    """
    existing_users = await db.users.query({"email": user.email})
    if existing_users:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = get_password_hash(user.password)
    await db.users.create(user)

    # Generate verification token
    token = create_verification_token(
        user.email, settings.VERIFICATION_TOKEN_EXPIRE_DELTA
    )

    # Create email message
    verification_link = f"http://127.0.0.1:8000/api/v1/users/verify-email?token={token}"
    html_content = f"""
    <p>Thanks for signing up! Please click the link below to verify your email address:</p>
    <a href="{verification_link}">Verify Email</a>
    """
    message = MessageSchema(
        subject="Verify Your Email Address",
        recipients=[user.email],
        body=html_content,
        subtype=MessageType.html,
    )

    # Send the email
    await fm.send_message(message)


@router.get("/verify-email")
async def verify_email(db: DatabaseDep, token: str):
    try:
        email = decode_verification_token(token)
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


@router.get("/me")
async def get_current_user(user: CurrentUserDep) -> User:
    """
    Get the current authenticated user.
    """
    return user
