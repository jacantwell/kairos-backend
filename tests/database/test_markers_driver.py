"""Unit tests for MarkersDriver."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from kairos.database.drivers.markers import MarkersDriver
from kairos.models.markers import Coordinates, Marker


class TestMarkersDriver:
    """Test suite for MarkersDriver class."""

    @pytest.fixture
    def markers_driver(self, mock_database):
        """Create a MarkersDriver instance with mock database."""
        mock_database.__getitem__ = MagicMock(return_value=AsyncMock())
        driver = MarkersDriver(mock_database)
        driver.collection = AsyncMock()
        return driver

    @pytest.mark.unit
    async def test_create_indexes(self, markers_driver):
        """Test creating indexes for markers collection."""
        # Arrange
        markers_driver.collection.create_index = AsyncMock()

        # Act
        await markers_driver.create_indexes()

        # Assert
        assert markers_driver.collection.create_index.call_count == 2
        calls = markers_driver.collection.create_index.call_args_list
        assert calls[0][0][0] == [("coordinates", "2dsphere")]
        assert calls[1][0][0] == [("journey_id", 1)]

    @pytest.mark.unit
    async def test_create_marker_success(self, markers_driver, sample_marker):
        """Test creating a new marker successfully."""
        # Arrange
        new_marker_id = ObjectId()
        sample_marker.id = None
        markers_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=new_marker_id)
        )

        # Act
        result = await markers_driver.create(sample_marker)

        # Assert
        assert result.id == new_marker_id
        markers_driver.collection.insert_one.assert_called_once()
        call_args = markers_driver.collection.insert_one.call_args[0][0]
        assert "id" not in call_args
        assert call_args["name"] == sample_marker.name
        assert call_args["marker_type"] == sample_marker.marker_type

    @pytest.mark.unit
    async def test_create_marker_removes_id(self, markers_driver, sample_marker):
        """Test that create removes the id field before insertion."""
        # Arrange
        new_marker_id = ObjectId()
        sample_marker.id = ObjectId()  # Set an ID that should be removed
        markers_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=new_marker_id)
        )

        # Act
        result = await markers_driver.create(sample_marker)

        # Assert
        call_args = markers_driver.collection.insert_one.call_args[0][0]
        assert "id" not in call_args
        assert result.id == new_marker_id

    @pytest.mark.unit
    async def test_query_markers_empty_result(self, markers_driver):
        """Test querying markers with no results."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await markers_driver.query({"name": "Nonexistent Marker"})

        # Assert
        assert result == []
        markers_driver.collection.find.assert_called_once_with(
            {"name": "Nonexistent Marker"}
        )

    @pytest.mark.unit
    async def test_query_markers_with_results(self, markers_driver, sample_marker):
        """Test querying markers with results."""
        # Arrange
        marker_data = sample_marker.model_dump(by_alias=True)
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[marker_data])
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await markers_driver.query({"journey_id": sample_marker.journey_id})

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], Marker)
        assert result[0].name == sample_marker.name
        assert result[0].journey_id == sample_marker.journey_id

    @pytest.mark.unit
    async def test_read_marker_by_id_success(self, markers_driver, sample_marker):
        """Test reading a marker by ID successfully."""
        # Arrange
        marker_data = sample_marker.model_dump(by_alias=True)
        markers_driver.collection.find_one = AsyncMock(return_value=marker_data)

        # Act
        result = await markers_driver.read(str(sample_marker.id))

        # Assert
        assert isinstance(result, Marker)
        assert result.id == sample_marker.id
        assert result.name == sample_marker.name
        markers_driver.collection.find_one.assert_called_once_with(
            {"_id": sample_marker.id}
        )

    @pytest.mark.unit
    async def test_read_marker_converts_string_id(self, markers_driver, sample_marker):
        """Test that read converts string ID to ObjectId."""
        # Arrange
        marker_data = sample_marker.model_dump(by_alias=True)
        markers_driver.collection.find_one = AsyncMock(return_value=marker_data)
        marker_id_str = str(sample_marker.id)

        # Act
        result = await markers_driver.read(marker_id_str)

        # Assert
        markers_driver.collection.find_one.assert_called_once()
        call_args = markers_driver.collection.find_one.call_args[0][0]
        assert isinstance(call_args["_id"], ObjectId)
        assert str(call_args["_id"]) == marker_id_str

    @pytest.mark.unit
    async def test_update_marker_success(self, markers_driver, sample_marker):
        """Test updating a marker successfully."""
        # Arrange
        markers_driver.collection.update_one = AsyncMock()
        updated_marker = sample_marker.model_copy()
        updated_marker.name = "Updated Marker Name"
        updated_marker.notes = "Updated notes"

        # Act
        await markers_driver.update(str(sample_marker.id), updated_marker)

        # Assert
        markers_driver.collection.update_one.assert_called_once()
        call_args = markers_driver.collection.update_one.call_args[0]
        assert call_args[0] == {"_id": sample_marker.id}
        assert call_args[1]["$set"]["name"] == "Updated Marker Name"
        assert call_args[1]["$set"]["notes"] == "Updated notes"
        assert "id" not in call_args[1]["$set"]

    @pytest.mark.unit
    async def test_update_marker_removes_id_field(self, markers_driver, sample_marker):
        """Test that update removes the id field from the update data."""
        # Arrange
        markers_driver.collection.update_one = AsyncMock()

        # Act
        await markers_driver.update(str(sample_marker.id), sample_marker)

        # Assert
        call_args = markers_driver.collection.update_one.call_args[0]
        update_data = call_args[1]["$set"]
        assert "id" not in update_data
        assert "_id" not in update_data

    @pytest.mark.unit
    async def test_delete_marker_success(self, markers_driver, sample_marker_id):
        """Test deleting a marker successfully."""
        # Arrange
        markers_driver.collection.delete_one = AsyncMock()

        # Act
        await markers_driver.delete(str(sample_marker_id))

        # Assert
        markers_driver.collection.delete_one.assert_called_once_with(
            {"_id": sample_marker_id}
        )

    @pytest.mark.unit
    async def test_delete_marker_converts_string_id(self, markers_driver):
        """Test that delete converts string ID to ObjectId."""
        # Arrange
        marker_id = ObjectId()
        markers_driver.collection.delete_one = AsyncMock()

        # Act
        await markers_driver.delete(str(marker_id))

        # Assert
        call_args = markers_driver.collection.delete_one.call_args[0][0]
        assert isinstance(call_args["_id"], ObjectId)
        assert call_args["_id"] == marker_id

    @pytest.mark.unit
    async def test_get_journey_markers_success(self, markers_driver, sample_journey_id):
        """Test getting all markers for a journey."""
        # Arrange
        marker_id_1 = ObjectId()
        marker_id_2 = ObjectId()
        markers_data = [
            {
                "_id": marker_id_1,
                "name": "Marker 1",
                "journey_id": sample_journey_id,
                "marker_type": "past",
                "coordinates": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
                "notes": "First marker",
            },
            {
                "_id": marker_id_2,
                "name": "Marker 2",
                "journey_id": sample_journey_id,
                "marker_type": "plan",
                "coordinates": {"type": "Point", "coordinates": [-122.4085, 37.7855]},
                "notes": "Second marker",
            },
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=markers_data)
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await markers_driver.get_journey_markers(str(sample_journey_id))

        # Assert
        assert len(result) == 2
        assert all(isinstance(m, Marker) for m in result)
        markers_driver.collection.find.assert_called_once_with(
            {"journey_id": sample_journey_id}
        )

    @pytest.mark.unit
    async def test_get_journey_markers_empty(self, markers_driver, sample_journey_id):
        """Test getting markers for a journey with no markers."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await markers_driver.get_journey_markers(str(sample_journey_id))

        # Assert
        assert result == []

    @pytest.mark.unit
    async def test_delete_journey_markers_success(self, markers_driver, sample_journey_id):
        """Test deleting all markers for a journey."""
        # Arrange
        markers_driver.collection.delete_many = AsyncMock()

        # Act
        await markers_driver.delete_journey_markers(str(sample_journey_id))

        # Assert
        markers_driver.collection.delete_many.assert_called_once_with(
            {"journey_id": sample_journey_id}
        )

    @pytest.mark.unit
    async def test_delete_user_markers_success(self, markers_driver, sample_user_id):
        """Test deleting all markers for a user."""
        # Arrange
        markers_driver.collection.delete_many = AsyncMock()

        # Act
        await markers_driver.delete_user_markers(str(sample_user_id))

        # Assert
        markers_driver.collection.delete_many.assert_called_once_with(
            {"owner_id": sample_user_id}
        )

    @pytest.mark.unit
    async def test_get_coordinates_nearby_journeys_success(self, markers_driver):
        """Test finding nearby journeys by coordinates."""
        # Arrange
        journey_id_1 = ObjectId()
        journey_id_2 = ObjectId()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(
            return_value=[{"_id": journey_id_1}, {"_id": journey_id_2}]
        )
        markers_driver.collection.aggregate = AsyncMock(return_value=mock_cursor)
        coordinates = [-122.4194, 37.7749]
        max_distance = 100000

        # Act
        result = await markers_driver.get_coordinates_nearby_journeys(
            coordinates, max_distance
        )

        # Assert
        assert len(result) == 2
        assert result == [journey_id_1, journey_id_2]
        markers_driver.collection.aggregate.assert_called_once()

        # Verify pipeline structure
        call_args = markers_driver.collection.aggregate.call_args[0][0]
        assert len(call_args) == 3
        assert "$geoNear" in call_args[0]
        assert call_args[0]["$geoNear"]["near"]["coordinates"] == coordinates
        assert call_args[0]["$geoNear"]["maxDistance"] == max_distance
        assert "$group" in call_args[1]
        assert "$limit" in call_args[2]

    @pytest.mark.unit
    async def test_get_coordinates_nearby_journeys_default_distance(self, markers_driver):
        """Test finding nearby journeys with default distance."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        markers_driver.collection.aggregate = AsyncMock(return_value=mock_cursor)
        coordinates = [-122.4194, 37.7749]

        # Act
        await markers_driver.get_coordinates_nearby_journeys(coordinates)

        # Assert
        call_args = markers_driver.collection.aggregate.call_args[0][0]
        assert call_args[0]["$geoNear"]["maxDistance"] == 100000

    @pytest.mark.unit
    async def test_get_coordinates_nearby_journeys_empty(self, markers_driver):
        """Test finding nearby journeys with no results."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        markers_driver.collection.aggregate = AsyncMock(return_value=mock_cursor)

        # Act
        result = await markers_driver.get_coordinates_nearby_journeys(
            [-122.4194, 37.7749]
        )

        # Assert
        assert result == []

    @pytest.mark.unit
    async def test_get_journey_nearby_journeys_success(self, markers_driver):
        """Test finding nearby journeys for a given journey."""
        # Arrange
        journey_id = ObjectId()
        nearby_journey_id_1 = ObjectId()
        nearby_journey_id_2 = ObjectId()

        # Mock find for journey markers
        journey_markers = [
            {
                "_id": ObjectId(),
                "journey_id": journey_id,
                "coordinates": {"coordinates": [-122.4194, 37.7749]},
            },
            {
                "_id": ObjectId(),
                "journey_id": journey_id,
                "coordinates": {"coordinates": [-122.4085, 37.7855]},
            },
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=journey_markers)
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Mock aggregate for nearby journeys
        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list = AsyncMock(
            side_effect=[
                [{"_id": nearby_journey_id_1}, {"_id": journey_id}],
                [{"_id": nearby_journey_id_2}],
            ]
        )
        markers_driver.collection.aggregate = AsyncMock(return_value=mock_agg_cursor)

        # Act
        result = await markers_driver.get_journey_nearby_journeys(str(journey_id))

        # Assert
        assert len(result) == 2
        assert str(nearby_journey_id_1) in result
        assert str(nearby_journey_id_2) in result
        assert str(journey_id) not in result  # Original journey should be excluded

    @pytest.mark.unit
    async def test_get_journey_nearby_journeys_no_markers(self, markers_driver):
        """Test finding nearby journeys when journey has no markers."""
        # Arrange
        journey_id = ObjectId()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await markers_driver.get_journey_nearby_journeys(str(journey_id))

        # Assert
        assert result == []

    @pytest.mark.unit
    async def test_get_journey_nearby_journeys_custom_distance(self, markers_driver):
        """Test finding nearby journeys with custom max distance."""
        # Arrange
        journey_id = ObjectId()
        max_distance = 200000

        journey_markers = [
            {
                "_id": ObjectId(),
                "journey_id": journey_id,
                "coordinates": {"coordinates": [-122.4194, 37.7749]},
            }
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=journey_markers)
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        mock_agg_cursor = AsyncMock()
        mock_agg_cursor.to_list = AsyncMock(return_value=[])
        markers_driver.collection.aggregate = AsyncMock(return_value=mock_agg_cursor)

        # Act
        await markers_driver.get_journey_nearby_journeys(str(journey_id), max_distance)

        # Assert
        # Verify that aggregate was called with the custom max_distance
        call_args = markers_driver.collection.aggregate.call_args[0][0]
        assert call_args[0]["$geoNear"]["maxDistance"] == max_distance

    @pytest.mark.unit
    async def test_query_markers_by_type(self, markers_driver, sample_journey_id):
        """Test querying markers by marker type."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        markers_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        await markers_driver.query({"marker_type": "past"})

        # Assert
        markers_driver.collection.find.assert_called_once_with({"marker_type": "past"})

    @pytest.mark.unit
    async def test_create_marker_with_coordinates(self, markers_driver):
        """Test creating a marker with specific coordinates."""
        # Arrange
        marker_id = ObjectId()
        journey_id = ObjectId()
        marker = Marker(
            name="Test Marker",
            journey_id=journey_id,
            marker_type="plan",
            coordinates=Coordinates(type="Point", coordinates=[-74.006, 40.7128]),
            notes="New York City",
        )
        markers_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=marker_id)
        )

        # Act
        result = await markers_driver.create(marker)

        # Assert
        call_args = markers_driver.collection.insert_one.call_args[0][0]
        assert call_args["coordinates"]["type"] == "Point"
        assert call_args["coordinates"]["coordinates"] == [-74.006, 40.7128]
