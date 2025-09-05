from bson import ObjectId
from kairos.models.users import User
from pymongo.asynchronous.database import AsyncDatabase


class UsersDriver:

    def __init__(self, database: AsyncDatabase):
        self.collection = database["users"]

    async def create(self, user: User) -> User:

        # Convert to dictionary
        user_data = user.model_dump()

        # This allows mongo to generate the objectID
        user_data.pop("id")

        insertion_result = await self.collection.insert_one(user_data)

        # Add the generated ID to the user object
        user.id = insertion_result.inserted_id

        return user

    async def query(self, query: dict) -> list[User]:

        cursor = self.collection.find(query)

        # Convert cursor to list of User objects
        users = await cursor.to_list(length=None)

        return [User.model_validate(user) for user in users]

    async def read(self, id: str) -> User:

        user = await self.collection.find_one({"_id": ObjectId(id)})

        return User.model_validate(user)

    async def update(self, id: str, user: User) -> None:

        user_data = user.model_dump()
        user_data.pop("id", None)

        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": user_data})

    async def delete(self, id: str) -> None:

        await self.collection.delete_one({"_id": ObjectId(id)})
