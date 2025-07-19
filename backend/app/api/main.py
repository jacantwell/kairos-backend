from fastapi import APIRouter

from app.api.routes import users_router, root_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(root_router)


if settings.ENVIRONMENT == "local":
    # Possilbe to add local only routers
    pass