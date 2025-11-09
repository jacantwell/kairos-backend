"""Unit tests for UsersDriver."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from kairos.database.drivers.users import UsersDriver
from kairos.models.users import User


class TestUsersDriver:
    """Test suite for UsersDriver class."""

    @pytest.fixture
    def users_driver(self, mock_database):
        """Create a UsersDriver instance with mock database."""
        mock_database.__getitem__ = MagicMock(return_value=AsyncMock())
        driver = UsersDriver(mock_database)
        driver.collection = AsyncMock()
        return driver

    @pytest.mark.unit
    async def test_create_user_success(self, users_driver, sample_user):
        """Test creating a new user successfully."""
        # Arrange
        new_user_id = ObjectId()
        sample_user.id = None
        users_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=new_user_id)
        )

        # Act
        result = await users_driver.create(sample_user)

        # Assert
        assert result.id == new_user_id
        users_driver.collection.insert_one.assert_called_once()
        call_args = users_driver.collection.insert_one.call_args[0][0]
        assert "id" not in call_args
        assert call_args["email"] == sample_user.email
        assert call_args["name"] == sample_user.name

    @pytest.mark.unit
    async def test_create_user_removes_id(self, users_driver, sample_user):
        """Test that create removes the id field before insertion."""
        # Arrange
        new_user_id = ObjectId()
        sample_user.id = ObjectId()  # Set an ID that should be removed
        users_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=new_user_id)
        )

        # Act
        result = await users_driver.create(sample_user)

        # Assert
        call_args = users_driver.collection.insert_one.call_args[0][0]
        assert "id" not in call_args
        assert result.id == new_user_id

    @pytest.mark.unit
    async def test_query_users_empty_result(self, users_driver):
        """Test querying users with no results."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        users_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await users_driver.query({"email": "nonexistent@example.com"})

        # Assert
        assert result == []
        users_driver.collection.find.assert_called_once_with(
            {"email": "nonexistent@example.com"}
        )

    @pytest.mark.unit
    async def test_query_users_with_results(self, users_driver, sample_user):
        """Test querying users with results."""
        # Arrange
        user_data = sample_user.model_dump(by_alias=True)
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[user_data])
        users_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await users_driver.query({"email": sample_user.email})

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], User)
        assert result[0].email == sample_user.email
        assert result[0].name == sample_user.name

    @pytest.mark.unit
    async def test_query_users_multiple_results(self, users_driver):
        """Test querying users returning multiple results."""
        # Arrange
        user_id_1 = ObjectId()
        user_id_2 = ObjectId()
        users_data = [
            {
                "_id": user_id_1,
                "email": "user1@example.com",
                "name": "User 1",
                "password": "hash1",
                "is_verified": True,
            },
            {
                "_id": user_id_2,
                "email": "user2@example.com",
                "name": "User 2",
                "password": "hash2",
                "is_verified": False,
            },
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=users_data)
        users_driver.collection.find = MagicMock(return_value=mock_cursor)

        # Act
        result = await users_driver.query({"is_verified": True})

        # Assert
        assert len(result) == 2
        assert all(isinstance(u, User) for u in result)

    @pytest.mark.unit
    async def test_read_user_by_id_success(self, users_driver, sample_user):
        """Test reading a user by ID successfully."""
        # Arrange
        user_data = sample_user.model_dump(by_alias=True)
        users_driver.collection.find_one = AsyncMock(return_value=user_data)

        # Act
        result = await users_driver.read(str(sample_user.id))

        # Assert
        assert isinstance(result, User)
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        users_driver.collection.find_one.assert_called_once_with(
            {"_id": sample_user.id}
        )

    @pytest.mark.unit
    async def test_read_user_converts_string_id(self, users_driver, sample_user):
        """Test that read converts string ID to ObjectId."""
        # Arrange
        user_data = sample_user.model_dump(by_alias=True)
        users_driver.collection.find_one = AsyncMock(return_value=user_data)
        user_id_str = str(sample_user.id)

        # Act
        result = await users_driver.read(user_id_str)

        # Assert
        users_driver.collection.find_one.assert_called_once()
        call_args = users_driver.collection.find_one.call_args[0][0]
        assert isinstance(call_args["_id"], ObjectId)
        assert str(call_args["_id"]) == user_id_str

    @pytest.mark.unit
    async def test_update_user_success(self, users_driver, sample_user):
        """Test updating a user successfully."""
        # Arrange
        users_driver.collection.update_one = AsyncMock()
        updated_user = sample_user.model_copy()
        updated_user.name = "Updated Name"

        # Act
        await users_driver.update(str(sample_user.id), updated_user)

        # Assert
        users_driver.collection.update_one.assert_called_once()
        call_args = users_driver.collection.update_one.call_args[0]
        assert call_args[0] == {"_id": sample_user.id}
        assert call_args[1]["$set"]["name"] == "Updated Name"
        assert "id" not in call_args[1]["$set"]

    @pytest.mark.unit
    async def test_update_user_removes_id_field(self, users_driver, sample_user):
        """Test that update removes the id field from the update data."""
        # Arrange
        users_driver.collection.update_one = AsyncMock()

        # Act
        await users_driver.update(str(sample_user.id), sample_user)

        # Assert
        call_args = users_driver.collection.update_one.call_args[0]
        update_data = call_args[1]["$set"]
        assert "id" not in update_data
        assert "_id" not in update_data

    @pytest.mark.unit
    async def test_delete_user_success(self, users_driver, sample_user_id):
        """Test deleting a user successfully."""
        # Arrange
        users_driver.collection.delete_one = AsyncMock()

        # Act
        await users_driver.delete(str(sample_user_id))

        # Assert
        users_driver.collection.delete_one.assert_called_once_with(
            {"_id": sample_user_id}
        )

    @pytest.mark.unit
    async def test_delete_user_converts_string_id(self, users_driver):
        """Test that delete converts string ID to ObjectId."""
        # Arrange
        user_id = ObjectId()
        users_driver.collection.delete_one = AsyncMock()

        # Act
        await users_driver.delete(str(user_id))

        # Assert
        call_args = users_driver.collection.delete_one.call_args[0][0]
        assert isinstance(call_args["_id"], ObjectId)
        assert call_args["_id"] == user_id

    @pytest.mark.unit
    async def test_create_preserves_user_fields(self, users_driver):
        """Test that create preserves all user fields."""
        # Arrange
        new_user = User(
            email="new@example.com",
            name="New User",
            password="hashedpassword",
            phonenumber="+1234567890",
            instagram="newuser",
            country="CA",
            is_verified=False,
        )
        new_user_id = ObjectId()
        users_driver.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=new_user_id)
        )

        # Act
        result = await users_driver.create(new_user)

        # Assert
        call_args = users_driver.collection.insert_one.call_args[0][0]
        assert call_args["email"] == "new@example.com"
        assert call_args["phonenumber"] == "+1234567890"
        assert call_args["instagram"] == "newuser"
        assert call_args["country"] == "CA"
        assert call_args["is_verified"] is False
        assert result.id == new_user_id

    @pytest.mark.unit
    async def test_query_with_complex_filter(self, users_driver):
        """Test querying users with complex MongoDB filter."""
        # Arrange
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        users_driver.collection.find = MagicMock(return_value=mock_cursor)
        complex_query = {
            "is_verified": True,
            "country": {"$in": ["US", "CA"]},
        }

        # Act
        await users_driver.query(complex_query)

        # Assert
        users_driver.collection.find.assert_called_once_with(complex_query)
