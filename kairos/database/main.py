import os

from kairos.database.drivers import JourneysDriver, UsersDriver, MarkersDriver
from pymongo import AsyncMongoClient


class Database:

    def __init__(self, client: AsyncMongoClient, database: str):
        # Create a connection for this class instance
        self.client = client
        self.database = client[database]

        # Define drivers that contain database operations
        self.users = UsersDriver(self.database)
        self.journeys = JourneysDriver(self.database)
        self.markers = MarkersDriver(self.database)

    async def setup_indexes(self):
        """
        Set up database indexes. This should be called during app startup.
        """
        await self.journeys.create_indexes()
        await self.markers.create_indexes()

    async def ping(self) -> str:
        """
        Ping the database to check if it's reachable.
        """
        try:
            await self.client.admin.command("ping")
            return "Pong"
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")


def get_database() -> Database:

    username = os.getenv("MONGO_USERNAME")
    password = os.getenv("MONGO_PASSWORD")
    host = os.getenv("MONGO_HOST")
    db_name = os.getenv("MONGO_DB_NAME")

    if not all([username, password, host, db_name]):
        raise EnvironmentError("Missing one or more MongoDB environment variables.")

    # Build URI for MongoDB Atlas or standalone
    mongo_uri = (
        f"mongodb+srv://{username}:{password}@{host}/?retryWrites=true&w=majority"
    )

    client = AsyncMongoClient(mongo_uri)
    assert db_name is not None  # I dont know why the if not all doesn't catch this
    database = Database(client, db_name)

    return database
