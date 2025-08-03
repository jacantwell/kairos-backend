from contextlib import asynccontextmanager

from fastapi import FastAPI
from mangum import Mangum
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.database import get_database

if settings.ENVIRONMENT != "local":
    # Allow options for only in production
    pass


# In your main app file
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database
    print("Connecting to database...")
    database = get_database()
    app.state.database = database
    print("Database connected.")

    yield

    # Shutdown
    await database.client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.CORS_ORGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mangum handler for lambda deployment
handler = Mangum(app)
