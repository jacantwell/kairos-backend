from fastapi import APIRouter
from kairos.api.routes import auth_router, root_router, users_router, journeys_router
from kairos.core.config import settings

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(root_router)
api_router.include_router(journeys_router)


if settings.ENVIRONMENT == "local":
    # Possilbe to add local only routers
    pass
