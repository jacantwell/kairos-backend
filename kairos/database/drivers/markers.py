from bson import ObjectId
from kairos.models.markers import Marker
from pymongo.asynchronous.database import AsyncDatabase
from typing import List


class MarkersDriver:

    def __init__(self, database: AsyncDatabase):
        self.collection = database["markers"]

    async def create_indexes(self):
        """
        Create geospatial indexes for marker coordinates
        """
        await self.collection.create_index([("coordinates", "2dsphere")])
        await self.collection.create_index([("journey_id", 1)])
        # await self.collection.create_index([("marker_type", 1)])  # May be useful later

    async def create(self, marker: Marker) -> Marker:

        # Convert to dictionary
        marker_data = marker.model_dump()

        # This allows mongo to generate the objectID
        marker_data.pop("id")

        # Convert the journey id to an objectID
        marker_data["journey_id"] = ObjectId(marker.journey_id)

        insertion_result = await self.collection.insert_one(marker_data)

        # Add the generated ID to the marker object
        marker.id = insertion_result.inserted_id

        return marker

    async def query(self, query: dict) -> list[Marker]:

        cursor = self.collection.find(query)

        # Convert cursor to list of Marker objects
        markers = await cursor.to_list(length=None)

        return [Marker.model_validate(marker) for marker in markers]

    async def read(self, id: str) -> Marker:

        marker = await self.collection.find_one({"_id": ObjectId(id)})

        return Marker.model_validate(marker)

    async def update(self, id: str, marker: Marker) -> None:

        marker_data = marker.model_dump()
        marker_data.pop("id", None)

        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": marker_data})

    async def delete(self, id: str) -> None:

        await self.collection.delete_one({"_id": ObjectId(id)})

    async def get_journey_markers(self, journey_id: str) -> List[Marker]:
        """Get all markers for a journey"""
        cursor = self.collection.find({"journey_id": ObjectId(journey_id)})
        markers =  await cursor.to_list(length=None)
        return [Marker.model_validate(marker) for marker in markers]
    
    async def get_coordinates_nearby_journeys(self, coordinates: List[float], max_distance_meters: int = 10000) -> List[str]:
        """
        Find journey IDs that have markers near the given coordinates
        coordinates: [longitude, latitude]
        Returns list of journey IDs
        """
        pipeline = [
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": coordinates
                    },
                    "distanceField": "distance",
                    "maxDistance": max_distance_meters,
                    "spherical": True
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
            {
                "$limit": 50  # Limit final journey results
            }
        ]
        
        cursor =  await self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=50)
        return [result["_id"] for result in results]
    
    async def get_journey_nearby_journeys(self, journey_id: str, max_distance_meters: int = 10000) -> List[str]:
        """
        Find journey IDs that have markers near any marker in the given journey
        Returns list of journey IDs
        """
        # First get all markers for the journey
        markers_cursor = self.collection.find({"journey_id": ObjectId(journey_id)})
        markers = await markers_cursor.to_list(length=None)
        
        print(markers)

        if not markers:
            return []
        
        nearby_journey_ids = set()
        
        for marker in markers:
            coordinates = marker["coordinates"]["coordinates"]
            nearby_ids = await self.get_coordinates_nearby_journeys(coordinates, max_distance_meters)
            nearby_journey_ids.update(nearby_ids)
        
        # Remove the original journey ID from results
        nearby_journey_ids.discard(ObjectId(journey_id))
        
        return [str(jid) for jid in nearby_journey_ids]
