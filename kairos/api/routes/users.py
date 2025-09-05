from fastapi import APIRouter, HTTPException
from kairos.api.deps import CurrentUserDep, DatabaseDep
from kairos.core.security import get_password_hash
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


@router.get("/me")
async def get_current_user(user: CurrentUserDep) -> User:
    """
    Get the current authenticated user.
    """
    return user
