"""Unit tests for root endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from kairos.api.routes.root import ping, ping_mongodb


class TestRootEndpoints:
    """Test suite for root endpoints."""

    @pytest.mark.unit
    def test_ping_success(self):
        """Test basic ping endpoint."""
        # Act
        result = ping()

        # Assert
        assert result == "pong"

    @pytest.mark.unit
    async def test_ping_mongodb_success(self, mock_db):
        """Test MongoDB ping endpoint successfully."""
        # Arrange
        mock_db.ping = AsyncMock(return_value="Pong")

        # Act
        result = await ping_mongodb(db=mock_db)

        # Assert
        assert result == "Pong"
        mock_db.ping.assert_called_once()

    @pytest.mark.unit
    async def test_ping_mongodb_connection_error(self, mock_db):
        """Test MongoDB ping endpoint with connection error."""
        # Arrange
        mock_db.ping = AsyncMock(side_effect=Exception("Connection failed"))

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await ping_mongodb(db=mock_db)

        assert exc_info.value.status_code == 500
        assert "Connection failed" in str(exc_info.value.detail)

    @pytest.mark.unit
    async def test_ping_mongodb_runtime_error(self, mock_db):
        """Test MongoDB ping endpoint with runtime error."""
        # Arrange
        mock_db.ping = AsyncMock(
            side_effect=RuntimeError("Database connection failed: timeout")
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await ping_mongodb(db=mock_db)

        assert exc_info.value.status_code == 500
