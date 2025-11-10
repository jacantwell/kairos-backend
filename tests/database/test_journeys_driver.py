"""Unit tests for JourneysDriver."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from kairos.database.drivers.journeys import JourneysDriver
from kairos.models.journeys import Journey


class TestJourneysDriver:
    """Test suite for JourneysDriver class."""

    @pytest.fixture
    def journeys_driver(self, mock_database):
        """Create a JourneysDriver instance with mock database."""
        mock_database.__getitem__ = MagicMock(return_value=AsyncMock())
        driver = JourneysDriver(mock_database)
        driver.collection = AsyncMock()
        return driver

    @pytest.mark.unit
    async def test_create_indexes(self, journeys_driver):
        """Test creating indexes for journeys collection."""
        # Arrange
        journeys_driver.collection.create_index = AsyncMock()

        # Act
        await journeys_driver.create_indexes()

        # Assert
        journeys_driver.collection.create_index.assert_called_once_with(
            [("user_id", 1)]
        )

    @pytest.mark.unit
    async def test_create_journey_success(self, journeys_driver, sample_journey):
        """Test creating a new journey successfully."""
        # Arrange
        new_journey_id = ObjectId()
        sample_journey.id = None
        journeys_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=new_journey_id)
        )

        # Act
        result = await journeys_driver.create(sample_journey)

        # Assert
        assert result.id == new_journey_id
        journeys_driver.collection.insert_one.assert_called_once()
        call_args = journeys_driver.collection.insert_one.call_args[0][0]
        assert "id" not in call_args
        assert call_args["name"] == sample_journey.name
        assert call_args["description"] == sample_journey.description

    @pytest.mark.unit
    async def test_create_journey_removes_id(self, journeys_driver, sample_journey):
        """Test that create removes the id field before insertion."""
        # Arrange
        new_journey_id = ObjectId()
        sample_journey.id = ObjectId()  # Set an ID that should be removed
        journeys_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=new_journey_id)
        )

        # Act
        result = await journeys_driver.create(sample_journey)

        # Assert
        call_args = journeys_driver.collection.insert_one.call_args[0][0]
        assert "id" not in call_args
        assert result.id == new_journey_id

    @pytest.mark.unit
    async def test_query_journeys_empty_result(self, journeys_driver):
        """Test querying journeys with no results."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        journeys_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await journeys_driver.query({"name": "Nonexistent Journey"})

        # Assert
        assert result == []
        journeys_driver.collection.find.assert_called_once_with(
            {"name": "Nonexistent Journey"}
        )

    @pytest.mark.unit
    async def test_query_journeys_with_results(self, journeys_driver, sample_journey):
        """Test querying journeys with results."""
        # Arrange
        journey_data = sample_journey.model_dump(by_alias=True)
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[journey_data])
        journeys_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await journeys_driver.query({"user_id": sample_journey.user_id})

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], Journey)
        assert result[0].name == sample_journey.name
        assert result[0].user_id == sample_journey.user_id

    @pytest.mark.unit
    async def test_query_journeys_multiple_results(self, journeys_driver, sample_user_id):
        """Test querying journeys returning multiple results."""
        # Arrange
        journey_id_1 = ObjectId()
        journey_id_2 = ObjectId()
        journeys_data = [
            {
                "_id": journey_id_1,
                "name": "Journey 1",
                "description": "First journey",
                "user_id": sample_user_id,
                "active": True,
                "completed": False,
            },
            {
                "_id": journey_id_2,
                "name": "Journey 2",
                "description": "Second journey",
                "user_id": sample_user_id,
                "active": False,
                "completed": False,
            },
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=journeys_data)
        journeys_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await journeys_driver.query({"user_id": sample_user_id})

        # Assert
        assert len(result) == 2
        assert all(isinstance(j, Journey) for j in result)

    @pytest.mark.unit
    async def test_read_journey_by_id_success(self, journeys_driver, sample_journey):
        """Test reading a journey by ID successfully."""
        # Arrange
        journey_data = sample_journey.model_dump(by_alias=True)
        journeys_driver.collection.find_one = AsyncMock(return_value=journey_data)

        # Act
        result = await journeys_driver.read(str(sample_journey.id))

        # Assert
        assert isinstance(result, Journey)
        assert result.id == sample_journey.id
        assert result.name == sample_journey.name
        journeys_driver.collection.find_one.assert_called_once_with(
            {"_id": sample_journey.id}
        )

    @pytest.mark.unit
    async def test_read_journey_converts_string_id(self, journeys_driver, sample_journey):
        """Test that read converts string ID to ObjectId."""
        # Arrange
        journey_data = sample_journey.model_dump(by_alias=True)
        journeys_driver.collection.find_one = AsyncMock(return_value=journey_data)
        journey_id_str = str(sample_journey.id)

        # Act
        result = await journeys_driver.read(journey_id_str)

        # Assert
        journeys_driver.collection.find_one.assert_called_once()
        call_args = journeys_driver.collection.find_one.call_args[0][0]
        assert isinstance(call_args["_id"], ObjectId)
        assert str(call_args["_id"]) == journey_id_str

    @pytest.mark.unit
    async def test_update_journey_success(self, journeys_driver, sample_journey):
        """Test updating a journey successfully."""
        # Arrange
        journeys_driver.collection.update_one = AsyncMock()
        updated_journey = sample_journey.model_copy()
        updated_journey.name = "Updated Journey Name"
        updated_journey.description = "Updated description"

        # Act
        await journeys_driver.update(str(sample_journey.id), updated_journey)

        # Assert
        journeys_driver.collection.update_one.assert_called_once()
        call_args = journeys_driver.collection.update_one.call_args[0]
        assert call_args[0] == {"_id": sample_journey.id}
        assert call_args[1]["$set"]["name"] == "Updated Journey Name"
        assert call_args[1]["$set"]["description"] == "Updated description"
        assert "id" not in call_args[1]["$set"]

    @pytest.mark.unit
    async def test_update_journey_removes_id_field(self, journeys_driver, sample_journey):
        """Test that update removes the id field from the update data."""
        # Arrange
        journeys_driver.collection.update_one = AsyncMock()

        # Act
        await journeys_driver.update(str(sample_journey.id), sample_journey)

        # Assert
        call_args = journeys_driver.collection.update_one.call_args[0]
        update_data = call_args[1]["$set"]
        assert "id" not in update_data
        assert "_id" not in update_data

    @pytest.mark.unit
    async def test_update_journey_active_status(self, journeys_driver, sample_journey):
        """Test updating a journey's active status."""
        # Arrange
        journeys_driver.collection.update_one = AsyncMock()
        sample_journey.active = False

        # Act
        await journeys_driver.update(str(sample_journey.id), sample_journey)

        # Assert
        call_args = journeys_driver.collection.update_one.call_args[0]
        assert call_args[1]["$set"]["active"] is False

    @pytest.mark.unit
    async def test_update_journey_completed_status(self, journeys_driver, sample_journey):
        """Test updating a journey's completed status."""
        # Arrange
        journeys_driver.collection.update_one = AsyncMock()
        sample_journey.completed = True

        # Act
        await journeys_driver.update(str(sample_journey.id), sample_journey)

        # Assert
        call_args = journeys_driver.collection.update_one.call_args[0]
        assert call_args[1]["$set"]["completed"] is True

    @pytest.mark.unit
    async def test_delete_journey_success(self, journeys_driver, sample_journey_id):
        """Test deleting a journey successfully."""
        # Arrange
        journeys_driver.collection.delete_one = AsyncMock()

        # Act
        await journeys_driver.delete(str(sample_journey_id))

        # Assert
        journeys_driver.collection.delete_one.assert_called_once_with(
            {"_id": sample_journey_id}
        )

    @pytest.mark.unit
    async def test_delete_journey_converts_string_id(self, journeys_driver):
        """Test that delete converts string ID to ObjectId."""
        # Arrange
        journey_id = ObjectId()
        journeys_driver.collection.delete_one = AsyncMock()

        # Act
        await journeys_driver.delete(str(journey_id))

        # Assert
        call_args = journeys_driver.collection.delete_one.call_args[0][0]
        assert isinstance(call_args["_id"], ObjectId)
        assert call_args["_id"] == journey_id

    @pytest.mark.unit
    async def test_delete_user_journeys_success(self, journeys_driver, sample_user_id):
        """Test deleting all journeys for a user."""
        # Arrange
        journeys_driver.collection.delete_many = AsyncMock()

        # Act
        await journeys_driver.delete_user_journeys(str(sample_user_id))

        # Assert
        journeys_driver.collection.delete_many.assert_called_once_with(
            {"user_id": sample_user_id}
        )

    @pytest.mark.unit
    async def test_delete_user_journeys_converts_string_id(self, journeys_driver):
        """Test that delete_user_journeys converts string ID to ObjectId."""
        # Arrange
        user_id = ObjectId()
        journeys_driver.collection.delete_many = AsyncMock()

        # Act
        await journeys_driver.delete_user_journeys(str(user_id))

        # Assert
        call_args = journeys_driver.collection.delete_many.call_args[0][0]
        assert isinstance(call_args["user_id"], ObjectId)
        assert call_args["user_id"] == user_id

    @pytest.mark.unit
    async def test_query_active_journeys(self, journeys_driver, sample_user_id):
        """Test querying for active journeys."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        journeys_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        await journeys_driver.query({"user_id": sample_user_id, "active": True})

        # Assert
        journeys_driver.collection.find.assert_called_once_with(
            {"user_id": sample_user_id, "active": True}
        )

    @pytest.mark.unit
    async def test_query_completed_journeys(self, journeys_driver, sample_user_id):
        """Test querying for completed journeys."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        journeys_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        await journeys_driver.query({"user_id": sample_user_id, "completed": True})

        # Assert
        journeys_driver.collection.find.assert_called_once_with(
            {"user_id": sample_user_id, "completed": True}
        )
