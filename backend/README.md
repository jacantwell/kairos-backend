# Backend Developer Guide

This backend is built with **FastAPI**, **Pydantic**, **MongoDB** (via `pymongo`), and managed using **Poetry**. It serves as the API and data layer for the project.

## 🛠️ Tech Stack

- **FastAPI**: Web framework for building APIs
- **Pydantic**: Data validation and settings management
- **MongoDB**: NoSQL database
- **pymongo**: MongoDB driver for Python
- **Uvicorn**: ASGI server for running FastAPI
- **Poetry**: Dependency and environment management

## 🚀 Getting Started

### 1. Install Dependencies

Make sure you have [Poetry](https://python-poetry.org/docs/#installation) installed.

```sh
cd backend
poetry install
```

### 2. Environment Variables

Copy the example environment file and fill in your MongoDB credentials:

```sh
cp .env.example .env
# Edit .env with your MongoDB details
```

### 3. Run the local Development Server

Use the provided script to start the server with hot-reload:

```sh
sh scripts/start_server.sh
```

### 4. Project Structure

```
app/
├── main.py             # FastAPI app entrypoint
├── api/                # API routers
├── models/             # Pydantic models
├── database/           # MongoDB drivers and connection logic
├── core/               # Configuration and settings
```

