"""Pytest configuration and fixtures for the test suite."""

from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from httpx import AsyncClient
from kairos.core.config import settings
from kairos.core.security import create_token, get_password_hash
from kairos.database import Database
from kairos.main import app
from kairos.models.journeys import Journey
from kairos.models.markers import Coordinates, Marker
from kairos.models.users import User


@pytest.fixture
def mock_collection():
    """Create a mock MongoDB collection."""
    collection = AsyncMock()
    collection.find_one = AsyncMock()
    collection.find = MagicMock()
    collection.insert_one = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()
    collection.delete_many = AsyncMock()
    collection.create_index = AsyncMock()
    collection.aggregate = AsyncMock()
    return collection


@pytest.fixture
def mock_database():
    """Create a mock AsyncDatabase."""
    database = MagicMock()
    return database


@pytest.fixture
def mock_db():
    """Create a mock Database instance with all drivers."""
    db = MagicMock(spec=Database)
    db.users = AsyncMock()
    db.journeys = AsyncMock()
    db.markers = AsyncMock()
    db.ping = AsyncMock(return_value="Pong")
    return db


@pytest.fixture
def sample_user() -> User:
    """Create a sample user for testing."""
    user_id = ObjectId()
    return User(
        id=user_id,
        email="test@example.com",
        name="Test User",
        password=get_password_hash("testpassword123"),
        phonenumber="+1234567890",
        instagram="testuser",
        country="US",
        is_verified=True,
    )


@pytest.fixture
def sample_journey(sample_user: User) -> Journey:
    """Create a sample journey for testing."""
    journey_id = ObjectId()
    return Journey(
        id=journey_id,
        name="Test Journey",
        description="A test journey",
        user_id=sample_user.id,
        created_at=datetime.now(),
        active=True,
        completed=False,
    )


@pytest.fixture
def sample_marker(sample_journey: Journey, sample_user: User) -> Marker:
    """Create a sample marker for testing."""
    marker_id = ObjectId()
    return Marker(
        id=marker_id,
        name="Test Marker",
        journey_id=sample_journey.id,
        owner_id=sample_user.id,
        marker_type="past",
        coordinates=Coordinates(type="Point", coordinates=[-122.4194, 37.7749]),
        timestamp=datetime.now().date(),
        notes="Test marker notes",
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_user_id(sample_user: User) -> ObjectId:
    """Get the sample user's ObjectId."""
    return sample_user.id


@pytest.fixture
def sample_journey_id(sample_journey: Journey) -> ObjectId:
    """Get the sample journey's ObjectId."""
    return sample_journey.id


@pytest.fixture
def sample_marker_id(sample_marker: Marker) -> ObjectId:
    """Get the sample marker's ObjectId."""
    return sample_marker.id


@pytest.fixture
def access_token(sample_user: User) -> str:
    """Generate a valid access token for testing."""
    return create_token(
        subject=str(sample_user.id),
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_DELTA,
        scope="access",
    )


@pytest.fixture
def refresh_token(sample_user: User) -> str:
    """Generate a valid refresh token for testing."""
    return create_token(
        subject=str(sample_user.id),
        expires_delta=settings.REFRESH_TOKEN_EXPIRE_DELTA,
        scope="refresh",
    )


@pytest.fixture
def expired_token(sample_user: User) -> str:
    """Generate an expired token for testing."""
    return create_token(
        subject=str(sample_user.id),
        expires_delta=timedelta(seconds=-1),
        scope="access",
    )


@pytest.fixture
def client() -> Generator:
    """Create a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an async FastAPI test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
