from bson import ObjectId
from kairos.models.journeys import Journey
from pymongo.asynchronous.database import AsyncDatabase


class JourneysDriver:
    """Driver for managing journey documents in MongoDB."""

    def __init__(self, database: AsyncDatabase) -> None:
        """Initialize the journeys driver.

        Args:
            database: The MongoDB async database instance.
        """
        self.collection = database["journeys"]

    async def create_indexes(self) -> None:
        """Create indexes for journey queries."""
        await self.collection.create_index([("user_id", 1)])

    async def create(self, journey: Journey) -> Journey:
        """Create a new journey in the database.

        Args:
            journey: The journey object to create.

        Returns:
            The created journey with the generated ID populated.
        """

        # Convert to dictionary
        journey_data = journey.to_mongo()

        # This allows mongo to generate the objectID
        journey_data.pop("id")

        insertion_result = await self.collection.insert_one(journey_data)

        # Add the generated ID to the journey object
        journey.id = insertion_result.inserted_id

        return journey

    async def query(self, query: dict) -> list[Journey]:
        """Query journeys based on the provided MongoDB query.

        Args:
            query: MongoDB query dictionary.

        Returns:
            List of journeys matching the query.
        """

        cursor = self.collection.find(query)

        # Convert cursor to list of Journey objects
        journeys = await cursor.to_list(length=None)

        return [Journey.model_validate(journey) for journey in journeys]

    async def read(self, id: str) -> Journey:
        """Retrieve a journey by its ID.

        Args:
            id: The journey's ObjectId as a string.

        Returns:
            The journey object.
        """

        journey = await self.collection.find_one({"_id": ObjectId(id)})

        return Journey.model_validate(journey)

    async def update(self, id: str, journey: Journey) -> None:
        """Update an existing journey in the database.

        Args:
            id: The journey's ObjectId as a string.
            journey: The updated journey object.
        """

        journey_data = journey.to_mongo()
        journey_data.pop("id", None)

        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": journey_data})

    async def delete(self, id: str) -> None:
        """Delete a journey from the database.

        Args:
            id: The journey's ObjectId as a string.
        """

        await self.collection.delete_one({"_id": ObjectId(id)})

    async def delete_user_journeys(self, user_id: str) -> None:
        """Delete all journeys for a user.

        Args:
            user_id: The user's ObjectId as a string.
        """
        await self.collection.delete_many({"user_id": ObjectId(user_id)})
