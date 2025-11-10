"""Unit tests for journeys endpoints."""

from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException
from kairos.api.routes.journeys import (
    add_marker_to_journey,
    create_journey,
    delete_journey,
    delete_journey_marker,
    get_journey,
    get_journey_markers,
    get_nearby_journeys,
    set_completed_journey,
    toggle_active_journey,
    update_journey_marker,
)
from kairos.models.markers import Coordinates, Marker


class TestJourneysEndpoints:
    """Test suite for journeys endpoints."""

    @pytest.mark.unit
    async def test_create_journey_success(self, mock_db, sample_user, sample_journey):
        """Test creating a journey successfully."""
        # Arrange
        sample_journey.id = None
        new_journey_id = ObjectId()
        created_journey = sample_journey.model_copy()
        created_journey.id = new_journey_id
        mock_db.journeys.create = AsyncMock(return_value=created_journey)

        # Act
        result = await create_journey(
            db=mock_db, user=sample_user, journey=sample_journey
        )

        # Assert
        assert result.id == new_journey_id
        mock_db.journeys.create.assert_called_once()

    @pytest.mark.unit
    async def test_create_journey_database_error(self, mock_db, sample_user, sample_journey):
        """Test creating a journey with database error."""
        # Arrange
        mock_db.journeys.create = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_journey(db=mock_db, user=sample_user, journey=sample_journey)

        assert exc_info.value.status_code == 500
        assert "Failed to create journey" in exc_info.value.detail

    @pytest.mark.unit
    async def test_get_journey_success(self, mock_db, sample_user, sample_journey):
        """Test getting a journey by ID successfully."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)

        # Act
        result = await get_journey(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result == sample_journey
        mock_db.journeys.read.assert_called_once_with(str(sample_journey.id))

    @pytest.mark.unit
    async def test_get_journey_not_found(self, mock_db, sample_user):
        """Test getting a journey that doesn't exist."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_journey(db=mock_db, user=sample_user, journey_id=journey_id)

        assert exc_info.value.status_code == 404
        assert "Journey not found" in exc_info.value.detail

    @pytest.mark.unit
    async def test_add_marker_to_journey_success(
        self, mock_db, sample_user, sample_journey, sample_marker
    ):
        """Test adding a marker to a journey successfully."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        sample_marker.id = None
        new_marker_id = ObjectId()
        created_marker = sample_marker.model_copy()
        created_marker.id = new_marker_id
        created_marker.owner_id = sample_user.id
        mock_db.markers.create = AsyncMock(return_value=created_marker)

        # Act
        result = await add_marker_to_journey(
            db=mock_db,
            user=sample_user,
            journey_id=str(sample_journey.id),
            marker=sample_marker,
        )

        # Assert
        assert result.id == new_marker_id
        assert result.owner_id == sample_user.id
        mock_db.markers.create.assert_called_once()

    @pytest.mark.unit
    async def test_add_marker_to_journey_not_found(self, mock_db, sample_user, sample_marker):
        """Test adding a marker to a non-existent journey."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await add_marker_to_journey(
                db=mock_db, user=sample_user, journey_id=journey_id, marker=sample_marker
            )

        assert exc_info.value.status_code == 404
        assert "Journey not found" in exc_info.value.detail

    @pytest.mark.unit
    async def test_add_marker_to_journey_database_error(
        self, mock_db, sample_user, sample_journey, sample_marker
    ):
        """Test adding a marker with database error."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.create = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await add_marker_to_journey(
                db=mock_db,
                user=sample_user,
                journey_id=str(sample_journey.id),
                marker=sample_marker,
            )

        assert exc_info.value.status_code == 500

    @pytest.mark.unit
    async def test_get_journey_markers_success(
        self, mock_db, sample_user, sample_journey, sample_marker
    ):
        """Test getting all markers for a journey."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.get_journey_markers = AsyncMock(return_value=[sample_marker])

        # Act
        result = await get_journey_markers(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert len(result) == 1
        assert result[0] == sample_marker
        mock_db.markers.get_journey_markers.assert_called_once_with(str(sample_journey.id))

    @pytest.mark.unit
    async def test_get_journey_markers_journey_not_found(self, mock_db, sample_user):
        """Test getting markers for non-existent journey."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_journey_markers(db=mock_db, user=sample_user, journey_id=journey_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_get_journey_markers_empty(self, mock_db, sample_user, sample_journey):
        """Test getting markers when journey has no markers."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.get_journey_markers = AsyncMock(return_value=[])

        # Act
        result = await get_journey_markers(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result == []

    @pytest.mark.unit
    async def test_delete_journey_marker_success(
        self, mock_db, sample_user, sample_journey, sample_marker
    ):
        """Test deleting a marker from a journey."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.delete = AsyncMock()

        # Act
        result = await delete_journey_marker(
            db=mock_db,
            user=sample_user,
            journey_id=str(sample_journey.id),
            marker_id=str(sample_marker.id),
        )

        # Assert
        assert result is None
        mock_db.markers.delete.assert_called_once_with(str(sample_marker.id))

    @pytest.mark.unit
    async def test_delete_journey_marker_journey_not_found(
        self, mock_db, sample_user, sample_marker
    ):
        """Test deleting a marker from non-existent journey."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_journey_marker(
                db=mock_db,
                user=sample_user,
                journey_id=journey_id,
                marker_id=str(sample_marker.id),
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_get_nearby_journeys_success(self, mock_db, sample_user, sample_journey):
        """Test getting nearby journeys."""
        # Arrange
        nearby_journey_ids = [str(ObjectId()), str(ObjectId())]
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.get_journey_nearby_journeys = AsyncMock(
            return_value=nearby_journey_ids
        )

        # Act
        result = await get_nearby_journeys(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result == nearby_journey_ids
        mock_db.markers.get_journey_nearby_journeys.assert_called_once_with(
            str(sample_journey.id)
        )

    @pytest.mark.unit
    async def test_get_nearby_journeys_not_found(self, mock_db, sample_user):
        """Test getting nearby journeys for non-existent journey."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_nearby_journeys(db=mock_db, user=sample_user, journey_id=journey_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_get_nearby_journeys_empty(self, mock_db, sample_user, sample_journey):
        """Test getting nearby journeys when none exist."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.get_journey_nearby_journeys = AsyncMock(return_value=[])

        # Act
        result = await get_nearby_journeys(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result == []

    @pytest.mark.unit
    async def test_delete_journey_success(self, mock_db, sample_user, sample_journey):
        """Test deleting a journey successfully."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.journeys.delete = AsyncMock()

        # Act
        result = await delete_journey(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result is None
        mock_db.journeys.delete.assert_called_once_with(str(sample_journey.id))

    @pytest.mark.unit
    async def test_delete_journey_not_found(self, mock_db, sample_user):
        """Test deleting a non-existent journey."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_journey(db=mock_db, user=sample_user, journey_id=journey_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_delete_journey_database_error(self, mock_db, sample_user, sample_journey):
        """Test deleting a journey with database error."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.journeys.delete = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_journey(
                db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
            )

        assert exc_info.value.status_code == 500

    @pytest.mark.unit
    async def test_toggle_active_journey_activate(self, mock_db, sample_user, sample_journey):
        """Test activating a journey."""
        # Arrange
        sample_journey.active = False
        mock_db.journeys.query = AsyncMock(return_value=[])  # No active journeys
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.journeys.update = AsyncMock()

        # Act
        result = await toggle_active_journey(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result is None
        mock_db.journeys.update.assert_called_once()

    @pytest.mark.unit
    async def test_toggle_active_journey_deactivate(self, mock_db, sample_user, sample_journey):
        """Test deactivating an active journey."""
        # Arrange
        sample_journey.active = True
        mock_db.journeys.query = AsyncMock(return_value=[sample_journey])
        mock_db.journeys.update = AsyncMock()

        # Act
        result = await toggle_active_journey(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result is None
        mock_db.journeys.update.assert_called_once()

    @pytest.mark.unit
    async def test_toggle_active_journey_switch(self, mock_db, sample_user, sample_journey):
        """Test switching from one active journey to another."""
        # Arrange
        active_journey_id = ObjectId()
        active_journey = sample_journey.model_copy()
        active_journey.id = active_journey_id
        active_journey.active = True

        new_active_journey = sample_journey.model_copy()
        new_active_journey.active = False

        mock_db.journeys.query = AsyncMock(return_value=[active_journey])
        mock_db.journeys.read = AsyncMock(return_value=new_active_journey)
        mock_db.journeys.update = AsyncMock()

        # Act
        result = await toggle_active_journey(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result is None
        assert mock_db.journeys.update.call_count == 2  # Deactivate old, activate new

    @pytest.mark.unit
    async def test_toggle_active_journey_not_found(self, mock_db, sample_user):
        """Test toggling active status for non-existent journey."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.query = AsyncMock(return_value=[])
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await toggle_active_journey(db=mock_db, user=sample_user, journey_id=journey_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_set_completed_journey_success(self, mock_db, sample_user, sample_journey):
        """Test marking a journey as completed."""
        # Arrange
        sample_journey.completed = False
        sample_journey.active = True
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.journeys.update = AsyncMock()

        # Act
        result = await set_completed_journey(
            db=mock_db, user=sample_user, journey_id=str(sample_journey.id)
        )

        # Assert
        assert result is None
        mock_db.journeys.update.assert_called_once()
        # Verify that both active=False and completed=True

    @pytest.mark.unit
    async def test_set_completed_journey_not_found(self, mock_db, sample_user):
        """Test marking non-existent journey as completed."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await set_completed_journey(db=mock_db, user=sample_user, journey_id=journey_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.unit
    async def test_update_journey_marker_success(
        self, mock_db, sample_user, sample_journey, sample_marker
    ):
        """Test updating a marker in a journey."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.read = AsyncMock(return_value=sample_marker)
        mock_db.markers.update = AsyncMock()

        updated_marker = sample_marker.model_copy()
        updated_marker.name = "Updated Marker"

        # Act
        result = await update_journey_marker(
            db=mock_db,
            user=sample_user,
            journey_id=str(sample_journey.id),
            marker_id=str(sample_marker.id),
            marker=updated_marker,
        )

        # Assert
        assert result.name == "Updated Marker"
        assert result.id == sample_marker.id
        assert result.owner_id == sample_marker.owner_id
        mock_db.markers.update.assert_called_once()

    @pytest.mark.unit
    async def test_update_journey_marker_journey_not_found(
        self, mock_db, sample_user, sample_marker
    ):
        """Test updating marker in non-existent journey."""
        # Arrange
        journey_id = str(ObjectId())
        mock_db.journeys.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_journey_marker(
                db=mock_db,
                user=sample_user,
                journey_id=journey_id,
                marker_id=str(sample_marker.id),
                marker=sample_marker,
            )

        assert exc_info.value.status_code == 404
        assert "Journey not found" in exc_info.value.detail

    @pytest.mark.unit
    async def test_update_journey_marker_marker_not_found(
        self, mock_db, sample_user, sample_journey, sample_marker
    ):
        """Test updating non-existent marker."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.read = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_journey_marker(
                db=mock_db,
                user=sample_user,
                journey_id=str(sample_journey.id),
                marker_id=str(sample_marker.id),
                marker=sample_marker,
            )

        assert exc_info.value.status_code == 404
        assert "Marker not found" in exc_info.value.detail

    @pytest.mark.unit
    async def test_update_journey_marker_preserves_owner(
        self, mock_db, sample_user, sample_journey, sample_marker
    ):
        """Test that updating a marker preserves owner_id."""
        # Arrange
        mock_db.journeys.read = AsyncMock(return_value=sample_journey)
        mock_db.markers.read = AsyncMock(return_value=sample_marker)
        mock_db.markers.update = AsyncMock()

        updated_marker = sample_marker.model_copy()
        different_owner_id = ObjectId()
        updated_marker.owner_id = different_owner_id

        # Act
        result = await update_journey_marker(
            db=mock_db,
            user=sample_user,
            journey_id=str(sample_journey.id),
            marker_id=str(sample_marker.id),
            marker=updated_marker,
        )

        # Assert
        assert result.owner_id == sample_marker.owner_id  # Should preserve original
        assert result.owner_id != different_owner_id
