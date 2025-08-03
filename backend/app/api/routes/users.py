from fastapi import APIRouter

from app.api.deps import CurrentUserDep, DatabaseDep
from app.core.security import get_password_hash
from app.models.users import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register_user(db: DatabaseDep, user: User) -> None:
    """
    Register a new user.
    """
    existing_users = await db.users.query({"username": user.username})
    if existing_users:
        return {"error": "Username already exists"}
    user.password = get_password_hash(user.password)
    await db.users.create(user)


@router.get("/me")
async def get_current_user(user: CurrentUserDep) -> User:
    """
    Get the current authenticated user.
    """
    return user
