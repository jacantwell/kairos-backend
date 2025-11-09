# API Reference Documentation

## Base URL

- **Production:** `https://7zpmbpgf7d.execute-api.eu-west-2.amazonaws.com`
- **Local Development:** `http://127.0.0.1:8000`

## API Version

All endpoints are prefixed with `/api/v1`

## Interactive Documentation

- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`

## Authentication

The API uses JWT (JSON Web Tokens) for authentication with a dual-token system.

### Token Types

1. **Access Token**
   - Lifetime: 60 minutes
   - Used for: API requests
   - Header: `Authorization: Bearer <access_token>`

2. **Refresh Token**
   - Lifetime: 8 days
   - Used for: Obtaining new access tokens
   - Endpoint: `POST /auth/refresh`

### Authentication Header Format

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created
- `204 No Content` - Request succeeded, no content to return
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - Valid token but insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Authentication Endpoints

### POST /auth/token

Login and obtain access and refresh tokens.

**Request:**

```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Note:** Despite the field name `username`, you should provide the user's email address.

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**

- `400 Bad Request` - Incorrect username or password
- `422 Unprocessable Entity` - Missing required fields

**Example (cURL):**

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=user@example.com&password=mypassword"
```

---

### POST /auth/refresh

Obtain a new access token using a refresh token.

**Request:**

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**

- `401 Unauthorized` - Refresh token has expired
- `403 Forbidden` - Invalid refresh token

**Note:** Currently, refresh token rotation is not implemented. The same refresh token is returned.

---

## Best Practices

### Authentication

1. **Store Tokens Securely:**
   - Use HttpOnly cookies for web apps
   - Use secure storage for mobile apps
   - Never store in localStorage (XSS risk)

2. **Refresh Token Handling:**
   - Refresh access tokens before expiry
   - Implement automatic retry on 401 errors

3. **Logout:**
   - Clear stored tokens on client side
   - Consider implementing token blacklist for server-side logout

### Error Handling

1. **Check Status Codes:**
   ```javascript
   if (response.status === 401) {
     // Try refreshing token
   }
   ```

2. **Parse Error Messages:**
   ```javascript
   const error = await response.json();
   console.error(error.detail);
   ```

### Geospatial Data

1. **Coordinate Order:**
   - Always use `[longitude, latitude]`
   - Longitude: -180 to 180
   - Latitude: -90 to 90

2. **Validation:**
   ```javascript
   function isValidCoordinate(lon, lat) {
     return lon >= -180 && lon <= 180 && 
            lat >= -90 && lat <= 90;
   }
   ```