from bson import ObjectId
from kairos.models.journeys import Journey
from pymongo.asynchronous.database import AsyncDatabase


class JourneysDriver:

    def __init__(self, database: AsyncDatabase):
        self.collection = database["journeys"]

    async def create_indexes(self):
        """
        Create indexes for journey queries
        """
        await self.collection.create_index([("user_id", 1)])


    async def create(self, journey: Journey) -> Journey:

        # Convert to dictionary
        journey_data = journey.to_mongo()

        # This allows mongo to generate the objectID
        journey_data.pop("id")

        insertion_result = await self.collection.insert_one(journey_data)

        # Add the generated ID to the journey object
        journey.id = insertion_result.inserted_id

        return journey

    async def query(self, query: dict) -> list[Journey]:

        cursor = self.collection.find(query)

        # Convert cursor to list of Journey objects
        journeys = await cursor.to_list(length=None)

        return [Journey.model_validate(journey) for journey in journeys]

    async def read(self, id: str) -> Journey:

        journey = await self.collection.find_one({"_id": ObjectId(id)})

        return Journey.model_validate(journey)

    async def update(self, id: str, journey: Journey) -> None:

        journey_data = journey.to_mongo()
        journey_data.pop("id", None)

        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": journey_data})

    async def delete(self, id: str) -> None:

        await self.collection.delete_one({"_id": ObjectId(id)})
