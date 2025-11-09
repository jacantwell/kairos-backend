"""Unit tests for users endpoints."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException
from kairos.api.routes.users import (
    delete_user,
    get_active_journey,
    get_current_user,
    get_user_by_id,
    get_user_journeys,
    register_user,
    reset_password,
    update_password,
    update_user,
    verify_email,
)
from kairos.core.security import create_token, get_password_hash
from kairos.models.journeys import Journey
from kairos.models.users import User


class TestUsersEndpoints:
    """Test suite for users endpoints."""

    @pytest.mark.unit
    @patch("kairos.api.routes.users.resend.Emails.send")
    async def test_register_user_success(self, mock_send, mock_db):
        """Test successful user registration."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        mock_db.users.create = AsyncMock()
        new_user = User(
            email="newuser@example.com",
            name="New User",
            password="password123",
            is_verified=False,
        )

        # Act
        result = await register_user(db=mock_db, user=new_user)

        # Assert
        assert result is None
        mock_db.users.query.assert_called_once_with({"email": new_user.email})
        mock_db.users.create.assert_called_once()
        mock_send.assert_called_once()

    @pytest.mark.unit
    async def test_register_user_email_already_exists(self, mock_db, sample_user):
        """Test registration with existing email."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        new_user = User(
            email=sample_user.email,
            name="Another User",
            password="password123",
            is_verified=False,
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register_user(db=mock_db, user=new_user)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail

    @pytest.mark.unit
    @patch("kairos.api.routes.users.resend.Emails.send")
    async def test_register_user_hashes_password(self, mock_send, mock_db):
        """Test that password is hashed during registration."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        created_user = None

        async def capture_user(user):
            nonlocal created_user
            created_user = user

        mock_db.users.create = AsyncMock(side_effect=capture_user)
        new_user = User(
            email="test@example.com",
            name="Test User",
            password="plainpassword",
            is_verified=False,
        )

        # Act
        await register_user(db=mock_db, user=new_user)

        # Assert
        assert created_user.password != "plainpassword"
        assert created_user.password.startswith("$2b$")  # bcrypt hash prefix

    @pytest.mark.unit
    @patch("kairos.api.routes.users.resend.Emails.send", side_effect=Exception("Email failed"))
    async def test_register_user_email_failure_does_not_fail(self, mock_send, mock_db):
        """Test that email sending failure doesn't prevent registration."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        mock_db.users.create = AsyncMock()
        new_user = User(
            email="test@example.com",
            name="Test User",
            password="password123",
            is_verified=False,
        )

        # Act - Should not raise exception
        result = await register_user(db=mock_db, user=new_user)

        # Assert
        assert result is None
        mock_db.users.create.assert_called_once()

    @pytest.mark.unit
    async def test_register_user_database_failure(self, mock_db):
        """Test registration with database failure."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        mock_db.users.create = AsyncMock(side_effect=Exception("Database error"))
        new_user = User(
            email="test@example.com",
            name="Test User",
            password="password123",
            is_verified=False,
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register_user(db=mock_db, user=new_user)

        assert exc_info.value.status_code == 500
        assert "Failed to create user" in exc_info.value.detail

    @pytest.mark.unit
    async def test_verify_email_success(self, mock_db, sample_user):
        """Test successful email verification."""
        # Arrange
        sample_user.is_verified = False
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        mock_db.users.update = AsyncMock()
        token = create_token(
            sample_user.email, timedelta(hours=24), scope="email_verification"
        )

        # Act
        result = await verify_email(db=mock_db, token=token)

        # Assert
        assert "verified successfully" in result.message.lower()
        mock_db.users.update.assert_called_once()

    @pytest.mark.unit
    async def test_verify_email_already_verified(self, mock_db, sample_user):
        """Test email verification when already verified."""
        # Arrange
        sample_user.is_verified = True
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        token = create_token(
            sample_user.email, timedelta(hours=24), scope="email_verification"
        )

        # Act
        result = await verify_email(db=mock_db, token=token)

        # Assert
        assert "already verified" in result.message.lower()
        mock_db.users.update.assert_not_called()

    @pytest.mark.unit
    async def test_verify_email_invalid_token(self, mock_db):
        """Test email verification with invalid token."""
        # Arrange
        invalid_token = "invalid.token.here"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_email(db=mock_db, token=invalid_token)

        assert exc_info.value.status_code == 400

    @pytest.mark.unit
    async def test_verify_email_user_not_found(self, mock_db):
        """Test email verification when user doesn't exist."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        token = create_token(
            "nonexistent@example.com", timedelta(hours=24), scope="email_verification"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_email(db=mock_db, token=token)

        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    @pytest.mark.unit
    async def test_verify_email_multiple_users(self, mock_db, sample_user):
        """Test email verification with data integrity error."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user, sample_user])
        token = create_token(
            sample_user.email, timedelta(hours=24), scope="email_verification"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await verify_email(db=mock_db, token=token)

        assert exc_info.value.status_code == 500
        assert "integrity error" in exc_info.value.detail.lower()

    @pytest.mark.unit
    @patch("kairos.api.routes.users.resend.Emails.send")
    async def test_reset_password_success(self, mock_send, mock_db, sample_user):
        """Test successful password reset request."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])

        # Act
        result = await reset_password(db=mock_db, email=sample_user.email)

        # Assert
        assert result is None
        mock_send.assert_called_once()

    @pytest.mark.unit
    async def test_reset_password_user_not_found(self, mock_db):
        """Test password reset for non-existent user."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])

        # Act - Should succeed silently to prevent user enumeration
        result = await reset_password(db=mock_db, email="nonexistent@example.com")

        # Assert
        assert result is None

    @pytest.mark.unit
    @patch("kairos.api.routes.users.resend.Emails.send", side_effect=Exception("Email failed"))
    async def test_reset_password_email_failure(self, mock_send, mock_db, sample_user):
        """Test password reset with email sending failure."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])

        # Act - Should succeed silently
        result = await reset_password(db=mock_db, email=sample_user.email)

        # Assert
        assert result is None

    @pytest.mark.unit
    async def test_update_password_success(self, mock_db, sample_user):
        """Test successful password update."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[sample_user])
        mock_db.users.update = AsyncMock()
        token = create_token(
            sample_user.email, timedelta(hours=1), scope="password_reset"
        )
        new_password = "newpassword123"

        # Act
        result = await update_password(db=mock_db, token=token, new_password=new_password)

        # Assert
        assert "updated successfully" in result.message.lower()
        mock_db.users.update.assert_called_once()

    @pytest.mark.unit
    async def test_update_password_invalid_token(self, mock_db):
        """Test password update with invalid token."""
        # Arrange
        invalid_token = "invalid.token.here"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_password(db=mock_db, token=invalid_token, new_password="newpass")

        assert exc_info.value.status_code == 400

    @pytest.mark.unit
    async def test_update_password_user_not_found(self, mock_db):
        """Test password update when user doesn't exist."""
        # Arrange
        mock_db.users.query = AsyncMock(return_value=[])
        token = create_token(
            "nonexistent@example.com", timedelta(hours=1), scope="password_reset"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_password(db=mock_db, token=token, new_password="newpass")

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_get_current_user(self, sample_user):
        """Test getting current authenticated user."""
        # Act
        result = await get_current_user(user=sample_user)

        # Assert
        assert result == sample_user

    @pytest.mark.unit
    async def test_get_user_by_id_success(self, mock_db, sample_user):
        """Test getting user by ID successfully."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=sample_user)

        # Act
        result = await get_user_by_id(
            db=mock_db, user=sample_user, user_id=str(sample_user.id)
        )

        # Assert
        assert result == sample_user
        mock_db.users.read.assert_called_once_with(str(sample_user.id))

    @pytest.mark.unit
    async def test_get_user_by_id_not_found(self, mock_db, sample_user):
        """Test getting user by ID when user doesn't exist."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=None)
        user_id = str(ObjectId())

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_id(db=mock_db, user=sample_user, user_id=user_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_get_user_journeys_success(self, mock_db, sample_user, sample_journey):
        """Test getting user journeys successfully."""
        # Arrange
        mock_db.journeys.query = AsyncMock(return_value=[sample_journey])

        # Act
        result = await get_user_journeys(
            db=mock_db, user=sample_user, user_id=str(sample_user.id)
        )

        # Assert
        assert len(result) == 1
        assert result[0] == sample_journey

    @pytest.mark.unit
    async def test_get_user_journeys_invalid_id(self, mock_db, sample_user):
        """Test getting user journeys with invalid user ID."""
        # Arrange
        invalid_id = "invalid_id"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_journeys(db=mock_db, user=sample_user, user_id=invalid_id)

        assert exc_info.value.status_code == 400
        assert "Invalid user ID" in exc_info.value.detail

    @pytest.mark.unit
    async def test_get_user_journeys_database_error(self, mock_db, sample_user):
        """Test getting user journeys with database error."""
        # Arrange
        mock_db.journeys.query = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_user_journeys(db=mock_db, user=sample_user, user_id=str(sample_user.id))

        assert exc_info.value.status_code == 500

    @pytest.mark.unit
    async def test_get_active_journey_success(self, mock_db, sample_user, sample_journey):
        """Test getting active journey successfully."""
        # Arrange
        sample_journey.active = True
        mock_db.journeys.query = AsyncMock(return_value=[sample_journey])

        # Act
        result = await get_active_journey(
            db=mock_db, user=sample_user, user_id=str(sample_user.id)
        )

        # Assert
        assert result == sample_journey
        mock_db.journeys.query.assert_called_once()

    @pytest.mark.unit
    async def test_get_active_journey_not_found(self, mock_db, sample_user):
        """Test getting active journey when none exists."""
        # Arrange
        mock_db.journeys.query = AsyncMock(return_value=[])

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_active_journey(db=mock_db, user=sample_user, user_id=str(sample_user.id))

        assert exc_info.value.status_code == 404
        assert "No active journey" in exc_info.value.detail

    @pytest.mark.unit
    async def test_update_user_success(self, mock_db, sample_user):
        """Test updating user successfully."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=sample_user)
        mock_db.users.update = AsyncMock()
        updated_user = sample_user.model_copy()
        updated_user.name = "Updated Name"

        # Act
        result = await update_user(
            db=mock_db,
            user=sample_user,
            user_id=str(sample_user.id),
            updated_user=updated_user,
        )

        # Assert
        assert result.name == "Updated Name"
        mock_db.users.update.assert_called_once()

    @pytest.mark.unit
    async def test_update_user_not_found(self, mock_db, sample_user):
        """Test updating user that doesn't exist."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_user(
                db=mock_db,
                user=sample_user,
                user_id=str(sample_user.id),
                updated_user=sample_user,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_update_user_password_change_rejected(self, mock_db, sample_user):
        """Test that password changes are rejected in update."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=sample_user)
        updated_user = sample_user.model_copy()
        updated_user.password = get_password_hash("newpassword")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_user(
                db=mock_db,
                user=sample_user,
                user_id=str(sample_user.id),
                updated_user=updated_user,
            )

        assert exc_info.value.status_code == 400
        assert "Password cannot be changed" in exc_info.value.detail

    @pytest.mark.unit
    async def test_delete_user_success(self, mock_db, sample_user):
        """Test deleting user successfully."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=sample_user)
        mock_db.users.delete = AsyncMock()
        mock_db.journeys.delete_user_journeys = AsyncMock()
        mock_db.markers.delete_user_markers = AsyncMock()

        # Act
        result = await delete_user(db=mock_db, user=sample_user, user_id=str(sample_user.id))

        # Assert
        assert "deleted successfully" in result.message.lower()
        mock_db.users.delete.assert_called_once()
        mock_db.journeys.delete_user_journeys.assert_called_once()
        mock_db.markers.delete_user_markers.assert_called_once()

    @pytest.mark.unit
    async def test_delete_user_not_found(self, mock_db, sample_user):
        """Test deleting user that doesn't exist."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_user(db=mock_db, user=sample_user, user_id=str(sample_user.id))

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_delete_user_database_error(self, mock_db, sample_user):
        """Test delete user with database error."""
        # Arrange
        mock_db.users.read = AsyncMock(return_value=sample_user)
        mock_db.users.delete = AsyncMock(side_effect=Exception("Delete failed"))

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_user(db=mock_db, user=sample_user, user_id=str(sample_user.id))

        assert exc_info.value.status_code == 500
