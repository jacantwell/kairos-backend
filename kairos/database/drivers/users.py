from bson import ObjectId
from kairos.models.users import User
from pymongo.asynchronous.database import AsyncDatabase


class UsersDriver:
    """Driver for managing user documents in MongoDB."""

    def __init__(self, database: AsyncDatabase) -> None:
        """Initialize the users driver.

        Args:
            database: The MongoDB async database instance.
        """
        self.collection = database["users"]

    async def create(self, user: User) -> User:
        """Create a new user in the database.

        Args:
            user: The user object to create.

        Returns:
            The created user with the generated ID populated.
        """

        # Convert to dictionary
        user_data = user.model_dump()

        # This allows mongo to generate the objectID
        user_data.pop("id")

        insertion_result = await self.collection.insert_one(user_data)

        # Add the generated ID to the user object
        user.id = insertion_result.inserted_id

        return user

    async def query(self, query: dict) -> list[User]:
        """Query users based on the provided MongoDB query.

        Args:
            query: MongoDB query dictionary.

        Returns:
            List of users matching the query.
        """

        cursor = self.collection.find(query)

        # Convert cursor to list of User objects
        users = await cursor.to_list(length=None)

        return [User.model_validate(user) for user in users]

    async def read(self, id: str) -> User:
        """Retrieve a user by their ID.

        Args:
            id: The user's ObjectId as a string.

        Returns:
            The user object.
        """

        user = await self.collection.find_one({"_id": ObjectId(id)})

        return User.model_validate(user)

    async def update(self, id: str, user: User) -> None:
        """Update an existing user in the database.

        Args:
            id: The user's ObjectId as a string.
            user: The updated user object.
        """

        user_data = user.to_mongo()
        user_data.pop("id", None)

        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": user_data})

    async def delete(self, id: str) -> None:
        """Delete a user from the database.

        Args:
            id: The user's ObjectId as a string.
        """

        await self.collection.delete_one({"_id": ObjectId(id)})
