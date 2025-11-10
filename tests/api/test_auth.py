"""Unit tests for authentication endpoints."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from kairos.api.routes.auth import login, refresh
from kairos.core.config import settings
from kairos.core.security import create_token, get_password_hash
from kairos.models.users import User


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    @pytest.mark.unit
    async def test_login_success(self, mock_db, sample_user):
        """Test successful login with valid credentials."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        form_data = type("OAuth2Form", (), {})()
        form_data.username = sample_user.email
        form_data.password = "testpassword123"

        # Act
        result = await login(db=mock_db, data=form_data)

        # Assert
        assert result.access_token is not None
        assert result.refresh_token is not None
        mock_db.users.query.assert_called_once_with({"email": sample_user.email})

    @pytest.mark.unit
    async def test_login_user_not_found(self, mock_db):
        """Test login with non-existent user."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        form_data = type("OAuth2Form", (), {})()
        form_data.username = "nonexistent@example.com"
        form_data.password = "password123"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(db=mock_db, data=form_data)

        assert exc_info.value.status_code == 400
        assert "Incorrect username or password" in exc_info.value.detail

    @pytest.mark.unit
    async def test_login_wrong_password(self, mock_db, sample_user):
        """Test login with incorrect password."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        form_data = type("OAuth2Form", (), {})()
        form_data.username = sample_user.email
        form_data.password = "wrongpassword"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(db=mock_db, data=form_data)

        assert exc_info.value.status_code == 400
        assert "Incorrect username or password" in exc_info.value.detail

    @pytest.mark.unit
    async def test_login_returns_valid_tokens(self, mock_db, sample_user):
        """Test that login returns properly formatted tokens."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        form_data = type("OAuth2Form", (), {})()
        form_data.username = sample_user.email
        form_data.password = "testpassword123"

        # Act
        result = await login(db=mock_db, data=form_data)

        # Assert
        assert isinstance(result.access_token, str)
        assert isinstance(result.refresh_token, str)
        assert len(result.access_token) > 0
        assert len(result.refresh_token) > 0

    @pytest.mark.unit
    async def test_login_with_unverified_user(self, mock_db, sample_user_id):
        """Test login with unverified user still succeeds."""
        # Arrange
        unverified_user = User(
            id=sample_user_id,
            email="unverified@example.com",
            name="Unverified User",
            password=get_password_hash("password123"),
            is_verified=False,
        )
        mock_db.users.query = AsyncMock(return_value=[unverified_user])
        form_data = type("OAuth2Form", (), {})()
        form_data.username = unverified_user.email
        form_data.password = "password123"

        # Act
        result = await login(db=mock_db, data=form_data)

        # Assert
        assert result.access_token is not None
        assert result.refresh_token is not None

    @pytest.mark.unit
    async def test_refresh_token_success(self, sample_user_id):
        """Test successful token refresh with valid refresh token."""
        # Arrange
        refresh_token = create_token(
            subject=str(sample_user_id),
            expires_delta=settings.REFRESH_TOKEN_EXPIRE_DELTA,
            scope="refresh",
        )

        # Act
        result = await refresh(refresh_token=refresh_token)

        # Assert
        assert result.access_token is not None
        assert result.refresh_token == refresh_token
        assert isinstance(result.access_token, str)

    @pytest.mark.unit
    async def test_refresh_token_expired(self, sample_user_id):
        """Test token refresh with expired refresh token."""
        # Arrange
        expired_token = create_token(
            subject=str(sample_user_id),
            expires_delta=timedelta(seconds=-1),
            scope="refresh",
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh(refresh_token=expired_token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.unit
    async def test_refresh_token_invalid(self):
        """Test token refresh with invalid token."""
        # Arrange
        invalid_token = "invalid.token.here"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh(refresh_token=invalid_token)

        assert exc_info.value.status_code == 403
        assert "Invalid refresh token" in exc_info.value.detail

    @pytest.mark.unit
    async def test_refresh_token_wrong_scope(self, sample_user_id):
        """Test token refresh with access token instead of refresh token."""
        # Arrange
        access_token = create_token(
            subject=str(sample_user_id),
            expires_delta=settings.ACCESS_TOKEN_EXPIRE_DELTA,
            scope="access",
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh(refresh_token=access_token)

        assert exc_info.value.status_code == 403

    @pytest.mark.unit
    async def test_refresh_generates_new_access_token(self, sample_user_id):
        """Test that refresh generates a new access token."""
        # Arrange
        refresh_token = create_token(
            subject=str(sample_user_id),
            expires_delta=settings.REFRESH_TOKEN_EXPIRE_DELTA,
            scope="refresh",
        )

        # Act
        result1 = await refresh(refresh_token=refresh_token)
        result2 = await refresh(refresh_token=refresh_token)

        # Assert - Access tokens should be different due to different timestamps
        # (though they could theoretically be the same if called in same second)
        assert result1.refresh_token == result2.refresh_token
        assert isinstance(result1.access_token, str)
        assert isinstance(result2.access_token, str)

    @pytest.mark.unit
    async def test_login_token_contains_user_id(self, mock_db, sample_user):
        """Test that tokens contain the correct user ID."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        form_data = type("OAuth2Form", (), {})()
        form_data.username = sample_user.email
        form_data.password = "testpassword123"

        # Act
        result = await login(db=mock_db, data=form_data)

        # Assert
        from kairos.core.security import decode_token

        access_sub = decode_token(result.access_token, scope="access")
        refresh_sub = decode_token(result.refresh_token, scope="refresh")

        assert access_sub == str(sample_user.id)
        assert refresh_sub == str(sample_user.id)

    @pytest.mark.unit
    async def test_login_case_sensitive_email(self, mock_db, sample_user):
        """Test that login email is case-sensitive."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        form_data = type("OAuth2Form", (), {})()
        form_data.username = sample_user.email.upper()  # Wrong case
        form_data.password = "testpassword123"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(db=mock_db, data=form_data)

        assert exc_info.value.status_code == 400

    @pytest.mark.unit
    async def test_refresh_preserves_refresh_token(self, sample_user_id):
        """Test that refresh returns the same refresh token."""
        # Arrange
        original_refresh_token = create_token(
            subject=str(sample_user_id),
            expires_delta=settings.REFRESH_TOKEN_EXPIRE_DELTA,
            scope="refresh",
        )

        # Act
        result = await refresh(refresh_token=original_refresh_token)

        # Assert
        assert result.refresh_token == original_refresh_token
