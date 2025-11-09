# Database Architecture Documentation

## Overview

The Kairos backend uses MongoDB as its primary database, leveraging its geospatial capabilities for location-based queries. The database layer is structured using a driver pattern that abstracts collection operations and provides type-safe interfaces.

## Connection Management

### Database Client

**Location:** `kairos/database/main.py`

```python
class Database:
    def __init__(self, client: AsyncMongoClient, database: str):
        self.client = client
        self.database = client[database]
        
        # Initialize drivers
        self.users = UsersDriver(self.database)
        self.journeys = JourneysDriver(self.database)
        self.markers = MarkersDriver(self.database)
```

### Connection URI

```python
mongo_uri = f"mongodb+srv://{username}:{password}@{host}/?retryWrites=true&w=majority"
```

**Features:**
- Retry writes enabled
- Write concern: majority
- Async driver via `pymongo.asynchronous`

### Lifespan Management

The database connection is managed in the FastAPI lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database = get_database()
    await database.setup_indexes()
    app.state.database = database
    
    yield
    
    # Shutdown
    await database.client.close()
```

#### Business Rules

1. **Owner Validation**
   - `owner_id` set automatically from authenticated user
   - Cannot create markers for other users' journeys

2. **Cascade Deletion**
   - Deleting a journey deletes all its markers
   - Deleting a user deletes all their markers

3. **Coordinate Bounds**
   - Longitude: -180 to 180
   - Latitude: -90 to 90

## Driver Pattern

### Base CRUD Operations

Each driver implements standard CRUD operations:

```python
class BaseDriver:
    async def create(self, model: T) -> T
    async def read(self, id: str) -> T
    async def update(self, id: str, model: T) -> None
    async def delete(self, id: str) -> None
    async def query(self, query: dict) -> list[T]
```

## MongoDB Model Helpers

### PyObjectId Type

**Location:** `kairos/models/id.py`

Custom Pydantic type for MongoDB ObjectIds:

```python
class PyObjectId(str):
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
```

**Features:**
- Validates ObjectId strings
- Serializes to string for JSON responses
- Deserializes from string in requests

### MongoModel Base Class

**Location:** `kairos/models/base.py`

Base class for all MongoDB models:

```python
class MongoModel(BaseModel):
    def to_mongo(self, **kwargs) -> dict:
        """Convert model to MongoDB document format"""
        data = self.model_dump(**kwargs)
        
        # Convert ObjectId fields
        for field_name, field_info in self.__class__.model_fields.items():
            field_value = getattr(self, field_name)
            
            if isinstance(field_value, ObjectId):
                dict_key = field_info.alias or field_name
                data[dict_key] = field_value
        
        return data
```

**Usage:**

```python
class User(MongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: str
    name: str

# In driver
user_data = user.to_mongo()
user_data.pop("id")  # Remove before insert
await collection.insert_one(user_data)
```

## Error Handling

### Common Exceptions

```python
from pymongo.errors import (
    DuplicateKeyError,
    ConnectionFailure,
    OperationFailure
)

# Handle duplicate email
try:
    await db.users.create(user)
except DuplicateKeyError:
    raise HTTPException(
        status_code=400,
        detail="Email already registered"
    )

# Handle connection issues
try:
    await db.ping()
except ConnectionFailure:
    raise HTTPException(
        status_code=503,
        detail="Database unavailable"
    )
```

### Validation in Drivers

```python
async def read(self, id: str) -> Journey:
    if not ObjectId.is_valid(id):
        raise ValueError("Invalid ID format")
    
    journey = await self.collection.find_one({"_id": ObjectId(id)})
    
    if not journey:
        raise ValueError("Journey not found")
    
    return Journey.model_validate(journey)
```
