# Kairos Backend - Developer Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Development Workflow](#development-workflow)
6. [API Documentation](#api-documentation)
7. [Database Design](#database-design)
8. [Authentication & Security](#authentication--security)
9. [Deployment](#deployment)
10. [Testing](#testing)
11. [Contributing](#contributing)

## Overview

Kairos is a bikepacking journey tracking application backend built with FastAPI, MongoDB, and deployed on AWS Lambda. The application allows users to create journeys, add markers (both past and planned), and discover other bikepackers near their routes using geospatial queries.

**Current Deployment:** https://7zpmbpgf7d.execute-api.eu-west-2.amazonaws.com/docs

### Tech Stack

- **Framework:** FastAPI 0.115.13
- **Language:** Python 3.12+
- **Database:** MongoDB (Atlas)
- **Authentication:** JWT (PyJWT)
- **Password Hashing:** Bcrypt + Passlib
- **Email Service:** Resend
- **Deployment:** AWS Lambda (via Mangum)
- **Infrastructure:** AWS CloudFormation
- **Container:** Docker (ECR)
- **Dependency Management:** Poetry

## Architecture

### High-Level Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│  API Gateway │─────▶│   Lambda    │
│ Application │◀─────│   (HTTP)     │◀─────│  (FastAPI)  │
└─────────────┘      └──────────────┘      └─────────────┘
                                                    │
                                                    ▼
                                            ┌─────────────┐
                                            │  MongoDB    │
                                            │   Atlas     │
                                            └─────────────┘
```

### Application Layers

1. **API Layer** (`kairos/api/`)
   - Route handlers organized by resource
   - Request validation via Pydantic
   - Dependency injection for database and auth

2. **Core Layer** (`kairos/core/`)
   - Configuration management
   - Security utilities (JWT, password hashing)
   - Application-wide settings

3. **Database Layer** (`kairos/database/`)
   - MongoDB connection management
   - Driver pattern for collections
   - CRUD operations abstraction

4. **Models Layer** (`kairos/models/`)
   - Pydantic models for validation
   - MongoDB document schemas
   - Type definitions

## Project Structure

```
kairos/
├── kairos/                      # Main application package
│   ├── api/                     # API routes and dependencies
│   │   ├── routes/              # Route handlers by resource
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── users.py         # User management
│   │   │   ├── journeys.py      # Journey CRUD
│   │   │   └── root.py          # Health checks
│   │   ├── deps.py              # Dependency injection
│   │   └── main.py              # Router aggregation
│   │
│   ├── core/                    # Core functionality
│   │   ├── config.py            # Settings and configuration
│   │   └── security.py          # JWT and password utilities
│   │
│   ├── database/                # Database layer
│   │   ├── drivers/             # Collection-specific drivers
│   │   │   ├── users.py         # User operations
│   │   │   ├── journeys.py      # Journey operations
│   │   │   └── markers.py       # Marker operations with geo queries
│   │   └── main.py              # Database connection and setup
│   │
│   ├── models/                  # Data models
│   │   ├── base.py              # Base model with MongoDB helpers
│   │   ├── id.py                # Custom ObjectId type
│   │   ├── users.py             # User schema
│   │   ├── journeys.py          # Journey schema
│   │   ├── markers.py           # Marker schema with GeoJSON
│   │   └── security.py          # Token schemas
│   │
│   └── main.py                  # FastAPI app and Lambda handler
│
├── scripts/                     # Utility scripts
│   ├── deploy/                  # Deployment scripts
│   │   ├── build.sh             # Docker build
│   │   ├── push.sh              # ECR push
│   │   ├── deploy.sh            # CloudFormation deploy
│   │   └── run.sh               # Local Docker run
│   └── start_server.sh          # Local development server
│
├── .github/workflows/           # CI/CD
│   └── deploy_backend.yml       # Automated deployment
│
├── Dockerfile                   # Lambda container definition
├── template.yaml                # CloudFormation template
├── pyproject.toml               # Poetry dependencies
├── poetry.lock                  # Locked dependencies
├── .env.example                 # Environment variable template
└── README.md                    # This file
```

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Poetry (Python package manager)
- MongoDB Atlas account (or local MongoDB)
- Docker (for deployment)
- AWS CLI (for deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd kairos
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```env
   # MongoDB
   MONGO_HOST=cluster0.mongodb.net
   MONGO_USERNAME=your_username
   MONGO_PASSWORD=your_password
   MONGO_DB_NAME=kairos
   
   # Email (Resend)
   RESEND_API_KEY=your_resend_api_key
   
   # Security
   SECRET_KEY=your_secret_key_for_jwt
   ```

5. **Run the development server**
   ```bash
   sh scripts/start_server.sh
   ```

   The API will be available at http://127.0.0.1:8000
   
   API documentation at http://127.0.0.1:8000/docs

### Database Setup

The application automatically creates necessary indexes on startup:

- **Journey Index:** `user_id` for fast user journey lookups
- **Marker Geo Index:** `2dsphere` on coordinates for spatial queries
- **Marker Journey Index:** `journey_id` for journey marker lookups

## Development Workflow

### Code Style

The project uses **Black** for code formatting and **isort** for import sorting.

```bash
# Format code
poetry run black kairos/

# Sort imports
poetry run isort kairos/

# Format and sort
poetry run black kairos/ && poetry run isort kairos/
```

Configuration in `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
src_paths = ["app"]
```

### Adding New Features

#### 1. Creating a New API Endpoint

Example: Adding a "comments" feature

**Step 1:** Create the model (`kairos/models/comments.py`)
```python
from datetime import datetime
from typing import Optional
from kairos.models.base import MongoModel
from kairos.models.id import PyObjectId
from pydantic import Field

class Comment(MongoModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    journey_id: PyObjectId
    user_id: PyObjectId
    text: str
    created_at: datetime = Field(default_factory=datetime.now)
```

**Step 2:** Create the driver (`kairos/database/drivers/comments.py`)
```python
from bson import ObjectId
from kairos.models.comments import Comment
from pymongo.asynchronous.database import AsyncDatabase

class CommentsDriver:
    def __init__(self, database: AsyncDatabase):
        self.collection = database["comments"]
    
    async def create(self, comment: Comment) -> Comment:
        comment_data = comment.to_mongo()
        comment_data.pop("id")
        result = await self.collection.insert_one(comment_data)
        comment.id = result.inserted_id
        return comment
    
    async def query(self, query: dict) -> list[Comment]:
        cursor = self.collection.find(query)
        comments = await cursor.to_list(length=None)
        return [Comment.model_validate(c) for c in comments]
```

**Step 3:** Add driver to database (`kairos/database/main.py`)
```python
from kairos.database.drivers import CommentsDriver

class Database:
    def __init__(self, client: AsyncMongoClient, database: str):
        # ... existing code ...
        self.comments = CommentsDriver(self.database)
```

**Step 4:** Create routes (`kairos/api/routes/comments.py`)
```python
from fastapi import APIRouter
from kairos.api.deps import CurrentUserDep, DatabaseDep
from kairos.models.comments import Comment

router = APIRouter(prefix="/comments", tags=["comments"])

@router.post("/")
async def create_comment(
    db: DatabaseDep, 
    user: CurrentUserDep, 
    comment: Comment
) -> Comment:
    comment.user_id = user.id
    return await db.comments.create(comment)
```

**Step 5:** Register routes (`kairos/api/main.py`)
```python
from kairos.api.routes import comments_router

api_router.include_router(comments_router)
```

### Working with MongoDB

#### Custom Queries

```python
# In a driver class
async def find_active_journeys(self, user_id: str):
    return await self.collection.find({
        "user_id": ObjectId(user_id),
        "active": True
    }).to_list(length=None)
```

#### Aggregation Pipelines

```python
async def get_journey_stats(self, journey_id: str):
    pipeline = [
        {"$match": {"journey_id": ObjectId(journey_id)}},
        {"$group": {
            "_id": "$marker_type",
            "count": {"$sum": 1}
        }}
    ]
    cursor = await self.collection.aggregate(pipeline)
    return await cursor.to_list(length=None)
```

#### Geospatial Queries

The `MarkersDriver` includes geospatial query examples:

```python
# Find markers within distance
async def get_coordinates_nearby_journeys(
    self, 
    coordinates: List[float],  # [longitude, latitude]
    max_distance_meters: int = 100000
) -> List[str]:
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": coordinates},
                "distanceField": "distance",
                "maxDistance": max_distance_meters,
                "spherical": True,
            }
        },
        {"$group": {"_id": "$journey_id"}},
        {"$limit": 50}
    ]
    # ... implementation
```

### API Documentation

When running locally or deployed:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`

## Database Design

### Geospatial Design

The application uses MongoDB's geospatial features for finding nearby journeys:

1. **Coordinates Format:** GeoJSON Point format `[longitude, latitude]`
2. **Distance Calculations:** Spherical (accounts for Earth's curvature)
3. **Default Search Radius:** 100km (100,000 meters)
4. **Performance:** Optimized with 2dsphere index

## Authentication & Security

### JWT Token System

The application uses a dual-token system:

1. **Access Token**
   - Short-lived (60 minutes)
   - Used for API authentication
   - Scope: `access`

2. **Refresh Token**
   - Long-lived (8 days)
   - Used to obtain new access tokens
   - Scope: `refresh`

### Token Structure

```python
{
  "exp": 1234567890,      # Expiration timestamp
  "sub": "user_id",       # Subject (user ID)
  "scope": "access"       # Token type
}
```

### Security Configuration

Located in `kairos/core/config.py`:

```python
class Settings(BaseSettings):
    SECRET_KEY: str  # JWT signing key
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 15
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
```

### Password Hashing

- **Algorithm:** Bcrypt
- **Library:** Passlib with bcrypt backend
- **Automatic:** Passwords hashed on registration and update

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed)
```

### Email Verification

1. User registers with email
2. Verification token sent via Resend
3. Token valid for 15 minutes
4. User clicks link with token
5. `is_verified` flag set to `true`

### Password Reset Flow

1. User requests reset via email
2. Reset token sent (15 min expiry)
3. User clicks link and provides new password
4. Token validated and password updated

### Protected Routes

Use the `CurrentUserDep` dependency:

```python
from kairos.api.deps import CurrentUserDep

@router.get("/protected")
async def protected_route(user: CurrentUserDep):
    # user is automatically validated and injected
    return {"user_id": str(user.id)}
```

### CORS Configuration

Configured in `kairos/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["*"] by default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Deployment

### Architecture

- **Container:** Docker image built from `Dockerfile`
- **Registry:** AWS ECR (Elastic Container Registry)
- **Compute:** AWS Lambda (via Mangum adapter)
- **API Gateway:** AWS API Gateway v2 (HTTP)
- **IaC:** AWS CloudFormation

### Environment Configuration

The application detects its environment automatically:

```python
ENVIRONMENT: Literal["local", "staging", "production"] = "local"
```

### Manual Deployment

#### 1. Build Docker Image
```bash
sh scripts/deploy/build.sh
```

#### 2. Push to ECR
```bash
sh scripts/deploy/push.sh
```

#### 3. Deploy with CloudFormation
```bash
aws cloudformation deploy \
  --capabilities CAPABILITY_IAM \
  --stack-name kairos-backend \
  --template-file template.yaml \
  --region eu-west-2 \
  --parameter-overrides \
    ImageUri="<ecr-uri>@<digest>" \
    MongoUsername="..." \
    MongoPassword="..." \
    MongoHost="..." \
    MongoDbName="..." \
    MailUsername="..." \
    ResendApiKey="..." \
    SecretKey="..."
```

### Automated Deployment (GitHub Actions)

The `.github/workflows/deploy_backend.yml` workflow automatically:

1. Builds Docker image on push to `main`
2. Pushes to ECR
3. Deploys via CloudFormation
4. Outputs API Gateway URL
5. Triggers client repo update with version

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `MONGO_USERNAME`
- `MONGO_PASSWORD`
- `MONGO_HOST`
- `MONGO_DB_NAME`
- `MAIL_USERNAME`
- `RESEND_API_KEY`
- `SECRET_KEY`
- `KAIROS_API_CLIENT_TS_PAT` (for triggering client updates)

### CloudFormation Resources

Defined in `template.yaml`:

- **LambdaExecutionRole:** IAM role with CloudWatch Logs permissions
- **LambdaFunction:** Container-based Lambda (15s timeout, 256MB memory)
- **ApiGateway:** HTTP API Gateway
- **ApiIntegration:** Lambda proxy integration
- **ApiRoute:** Catch-all route `ANY /{proxy+}`
- **ApiDeployment & ApiStage:** Default stage deployment
- **LambdaPermission:** Allows API Gateway to invoke Lambda

### Monitoring

Lambda logs are automatically sent to CloudWatch Logs:
- Log Group: `/aws/lambda/<function-name>`
- Retention: Default (indefinite)

### Performance Considerations

**Lambda Configuration:**
- **Timeout:** 15 seconds (API Gateway max is 30s)
- **Memory:** 256 MB (adjust based on load)
- **Cold Start:** ~2-3 seconds with Poetry/dependencies

**Optimization Tips:**
- Keep dependencies minimal
- Use connection pooling for MongoDB
- Consider Lambda SnapStart if available
- Monitor memory usage and adjust

## Troubleshooting

### Common Issues

#### MongoDB Connection Errors

**Problem:** `Database connection failed`

**Solutions:**
- Check MongoDB Atlas IP whitelist (add `0.0.0.0/0` for testing)
- Verify credentials in `.env`
- Ensure MongoDB cluster is running
- Check network connectivity

#### JWT Token Errors

**Problem:** `Could not validate credentials`

**Solutions:**
- Ensure `SECRET_KEY` is set and consistent
- Check token expiration
- Verify token is in format: `Bearer <token>`

#### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'kairos'`

**Solutions:**
```bash
# Reinstall dependencies
poetry install

# Verify you're in the correct directory
pwd  # Should be project root

# Run with poetry
poetry run uvicorn kairos.main:app
```

#### Docker Build Failures

**Problem:** Poetry installation fails in Docker

**Solutions:**
- Clear Docker cache: `docker builder prune`
- Check Poetry version in Dockerfile
- Ensure `poetry.lock` is committed

### Getting Help

- **API Docs:** http://localhost:8000/docs (when running)
- **MongoDB Issues:** Check connection string format
- **AWS Issues:** Verify CloudFormation stack events
- **Dependencies:** `poetry show` lists all installed packages

