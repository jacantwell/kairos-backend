# Kairos Backend Test Suite

This directory contains comprehensive unit tests for the Kairos backend project.

## Test Structure

```
tests/
├── api/                  # API endpoint tests
│   ├── test_auth.py     # Authentication endpoint tests
│   ├── test_users.py    # User management endpoint tests
│   ├── test_journeys.py # Journey endpoint tests
│   └── test_root.py     # Health check endpoint tests
├── database/             # Database driver tests
│   ├── test_users_driver.py     # UsersDriver tests
│   ├── test_journeys_driver.py  # JourneysDriver tests
│   └── test_markers_driver.py   # MarkersDriver tests
├── conftest.py          # Pytest fixtures and configuration
└── README.md            # This file
```

## Running Tests

### Run all tests
```bash
poetry run pytest tests/
```

### Run with coverage
```bash
poetry run pytest tests/ --cov=kairos --cov-report=html --cov-report=term-missing
```

### Run specific test file
```bash
poetry run pytest tests/api/test_auth.py -v
```

### Run specific test class or method
```bash
poetry run pytest tests/api/test_auth.py::TestAuthEndpoints::test_login_success -v
```

## Test Coverage

The test suite includes:

- **API Endpoints**: 73+ tests covering all REST API endpoints
  - Authentication (login, token refresh)
  - User management (registration, verification, password reset)
  - Journey management (CRUD operations, active/completed status)
  - Marker management (CRUD, geospatial queries)
  - Health checks

- **Database Drivers**: 56+ tests covering all database operations
  - UsersDriver: CRUD operations, queries
  - JourneysDriver: CRUD operations, user journey management
  - MarkersDriver: CRUD operations, geospatial queries, journey relationships

## Test Categories

Tests are marked with pytest markers:
- `@pytest.mark.unit`: Unit tests (all current tests)
- `@pytest.mark.integration`: Integration tests (for future use)
- `@pytest.mark.slow`: Slow-running tests (for future use)

## Fixtures

Common fixtures are defined in `conftest.py`:
- `mock_db`: Mock database instance
- `sample_user`: Sample user for testing
- `sample_journey`: Sample journey for testing
- `sample_marker`: Sample marker for testing
- `access_token`: Valid access token
- `refresh_token`: Valid refresh token
- `expired_token`: Expired token for testing

## Known Issues

Some tests have fixture dependency issues that need to be resolved. These tests are currently marked as errors but don't affect the passing tests.

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Use descriptive test names (test_<action>_<expected_result>)
3. Include docstrings explaining what each test does
4. Mock external dependencies (database, email service, etc.)
5. Aim for 100% code coverage of new features
