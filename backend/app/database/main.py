import os

from pymongo import AsyncMongoClient

from app.database.drivers import JourneysDriver
from app.database.drivers import UsersDriver


class Database():
    
    async def __init__(self, client: AsyncMongoClient, database: str):
        # Create a connection for this class instance
        self.client = client.aconnect()
        self.database = client[database]

        # Define drivers that contain database operations
        self.users = UsersDriver(self.database)
        self.journeys = JourneysDriver(self.database)

def database_factory():

    username = os.getenv("MONGO_USERNAME")
    password = os.getenv("MONGO_PASSWORD")
    host = os.getenv("MONGO_HOST")
    db_name = os.getenv("MONGO_DB_NAME")

    if not all([username, password, host, db_name]):
        raise EnvironmentError("Missing one or more MongoDB environment variables.")

    # Build URI for MongoDB Atlas or standalone
    mongo_uri = f"mongodb+srv://{username}:{password}@{host}/?retryWrites=true&w=majority"

    client = AsyncMongoClient(mongo_uri)
    database = Database(client, mongo_uri)
    
    return database

