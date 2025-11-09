from typing import List

from bson import ObjectId
from kairos.models.markers import Marker
from pymongo.asynchronous.database import AsyncDatabase


class MarkersDriver:
    """Driver for managing marker documents in MongoDB."""

    def __init__(self, database: AsyncDatabase) -> None:
        """Initialize the markers driver.

        Args:
            database: The MongoDB async database instance.
        """
        self.collection = database["markers"]

    async def create_indexes(self) -> None:
        """Create geospatial indexes for marker coordinates."""
        await self.collection.create_index([("coordinates", "2dsphere")])
        await self.collection.create_index([("journey_id", 1)])
        # await self.collection.create_index([("marker_type", 1)])  # May be useful later

    async def create(self, marker: Marker) -> Marker:
        """Create a new marker in the database.

        Args:
            marker: The marker object to create.

        Returns:
            The created marker with the generated ID populated.
        """

        # Convert to dictionary
        marker_data = marker.to_mongo()

        # This allows mongo to generate the objectID
        marker_data.pop("id")

        insertion_result = await self.collection.insert_one(marker_data)

        # Add the generated ID to the marker object
        marker.id = insertion_result.inserted_id

        return marker

    async def query(self, query: dict) -> list[Marker]:
        """Query markers based on the provided MongoDB query.

        Args:
            query: MongoDB query dictionary.

        Returns:
            List of markers matching the query.
        """

        cursor = self.collection.find(query)

        # Convert cursor to list of Marker objects
        markers = await cursor.to_list(length=None)

        return [Marker.model_validate(marker) for marker in markers]

    async def read(self, id: str) -> Marker:
        """Retrieve a marker by its ID.

        Args:
            id: The marker's ObjectId as a string.

        Returns:
            The marker object.
        """

        marker = await self.collection.find_one({"_id": ObjectId(id)})

        return Marker.model_validate(marker)

    async def update(self, id: str, marker: Marker) -> None:
        """Update an existing marker in the database.

        Args:
            id: The marker's ObjectId as a string.
            marker: The updated marker object.
        """

        marker_data = marker.to_mongo()
        marker_data.pop("id", None)

        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": marker_data})

    async def delete(self, id: str) -> None:
        """Delete a marker from the database.

        Args:
            id: The marker's ObjectId as a string.
        """

        await self.collection.delete_one({"_id": ObjectId(id)})

    async def get_journey_markers(self, journey_id: str) -> List[Marker]:
        """Get all markers for a journey.

        Args:
            journey_id: The journey's ObjectId as a string.

        Returns:
            List of markers belonging to the journey.
        """
        cursor = self.collection.find({"journey_id": ObjectId(journey_id)})
        markers = await cursor.to_list(length=None)
        return [Marker.model_validate(marker) for marker in markers]

    async def delete_journey_markers(self, journey_id: str) -> None:
        """Delete all markers for a journey.

        Args:
            journey_id: The journey's ObjectId as a string.
        """
        await self.collection.delete_many({"journey_id": ObjectId(journey_id)})

    async def delete_user_markers(self, user_id: str) -> None:
        """Delete all markers for a user.

        Args:
            user_id: The user's ObjectId as a string.
        """
        await self.collection.delete_many({"owner_id": ObjectId(user_id)})

    async def get_coordinates_nearby_journeys(
        self, coordinates: List[float], max_distance_meters: int = 100000
    ) -> List[str]:
        """Find journey IDs that have markers near the given coordinates.

        Args:
            coordinates: A list containing [longitude, latitude].
            max_distance_meters: Maximum distance in meters. Defaults to 100000.

        Returns:
            List of journey IDs (as strings) with markers near the coordinates.
        """
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": coordinates},
                    "distanceField": "distance",
                    "maxDistance": max_distance_meters,
                    "spherical": True,
                }
            },
            # {
            #     "$limit": 100  # Limit markers before grouping, not sure if this is correct
            #                    # could result in missing journeys
            # },
            {
                "$group": {
                    "_id": "$journey_id"  # Group by journey_id to get unique journey IDs
                }
            },
            {"$limit": 50},  # Limit final journey results
        ]

        cursor = await self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=50)
        return [result["_id"] for result in results]

    async def get_journey_nearby_journeys(
        self, journey_id: str, max_distance_meters: int = 500000
    ) -> List[str]:
        """Find journey IDs that have markers near any marker in the given journey.

        Args:
            journey_id: The journey's ObjectId as a string.
            max_distance_meters: Maximum distance in meters. Defaults to 500000.

        Returns:
            List of journey IDs (as strings) with markers near the given journey.
        """
        # First get all markers for the journey
        markers_cursor = self.collection.find({"journey_id": ObjectId(journey_id)})
        markers = await markers_cursor.to_list(length=None)

        if not markers:
            return []

        nearby_journey_ids = set()

        for marker in markers:
            coordinates = marker["coordinates"]["coordinates"]
            nearby_ids = await self.get_coordinates_nearby_journeys(
                coordinates, max_distance_meters
            )
            nearby_journey_ids.update(nearby_ids)

        # Remove the original journey ID from results
        nearby_journey_ids.discard(ObjectId(journey_id))

        return [str(jid) for jid in nearby_journey_ids]
