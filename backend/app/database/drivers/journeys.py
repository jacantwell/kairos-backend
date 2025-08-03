from bson import ObjectId
from pymongo.database import Collection, Database

from app.models.journey import Journey


class JourneysDriver:

    def __init__(self, database: Database):
        self.collection: Collection = database["journeys"]

    def _collection_setup(self):
        """
        Setup function that defines the collections indexes
        """

        self.collection.createIndex({"route_history.coordinates": "2dsphere"})
        self.collection.createIndex({"planned_route.coordinates": "2dsphere"})

    async def create(self, journey: Journey) -> Journey:

        # Convert to dictionary
        journey_data = journey.model_dump()

        # This allows mongo to generate the objectID
        journey_data.pop("id")

        insertion_result = await self.collection.insert_one(journey_data)

        # Add the generated ID to the journey object
        journey.id = insertion_result.inserted_id

        return journey

    async def query(self, query: dict) -> list[Journey]:

        cursor = self.collection.find(query)

        journeys = await cursor.to_list(length=None)

        return [Journey.model_validate(journey) for journey in journeys]

    async def read(self, id: str) -> Journey:

        journey = await self.collection.find_one({"_id": ObjectId(id)})

        return Journey.model_validate(journey)

    async def delete(self, id: str) -> None:

        await self.collection.delete_one({"_id": ObjectId(id)})
