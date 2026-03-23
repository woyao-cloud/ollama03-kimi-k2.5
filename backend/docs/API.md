# User Management System API Documentation

## Overview

This is a comprehensive User Management System API built with FastAPI, featuring JWT authentication, role-based access control (RBAC), and audit logging.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

The API uses OAuth2 Password Bearer authentication with JWT tokens.

### Obtaining Tokens

**Endpoint**: `POST /api/v1/auth/login`

**Request**:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "username": "your_username",
    "email": "user@example.com",
    "roles": ["user"]
  }
}
```

### Using Tokens

Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Refresh

Access tokens expire after 30 minutes. Use the refresh token to get new tokens:

**Endpoint**: `POST /api/v1/auth/refresh`

**Request**:
```json
{
  "refresh_token": "your_refresh_token"
}
```

## User Endpoints

### Register User

**Endpoint**: `POST /api/v1/auth/register`

**Request**:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Requirements**:
- Username: 3-50 characters, unique
- Email: Valid email format, unique
- Password: Minimum 8 characters, must contain uppercase, lowercase, and digit

### List Users

**Endpoint**: `GET /api/v1/users`

**Query Parameters**:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `is_active`: Filter by active status
- `is_verified`: Filter by verified status

**Response**:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Get User

**Endpoint**: `GET /api/v1/users/{user_id}`

### Update User

**Endpoint**: `PUT /api/v1/users/{user_id}`

**Request**:
```json
{
  "first_name": "Updated",
  "last_name": "Name",
  "is_active": true
}
```

### Delete User

**Endpoint**: `DELETE /api/v1/users/{user_id}`

### Assign Roles to User

**Endpoint**: `POST /api/v1/users/{user_id}/roles`

**Request**:
```json
{
  "role_ids": ["uuid1", "uuid2"]
}
```

## Role Endpoints

### List Roles

**Endpoint**: `GET /api/v1/roles`

### Create Role

**Endpoint**: `POST /api/v1/roles`

**Request**:
```json
{
  "name": "moderator",
  "description": "Moderator role with limited admin access",
  "is_default": false,
  "permission_ids": ["uuid1", "uuid2"]
}
```

### Get Role

**Endpoint**: `GET /api/v1/roles/{role_id}`

### Update Role

**Endpoint**: `PUT /api/v1/roles/{role_id}`

### Delete Role

**Endpoint**: `DELETE /api/v1/roles/{role_id}`

### Assign Permissions to Role

**Endpoint**: `POST /api/v1/roles/{role_id}/permissions`

**Request**:
```json
{
  "permission_ids": ["uuid1", "uuid2", "uuid3"]
}
```

## Permission Endpoints

### List Permissions

**Endpoint**: `GET /api/v1/permissions`

**Query Parameters**:
- `resource`: Filter by resource (e.g., "users", "roles")

### Create Permission

**Endpoint**: `POST /api/v1/permissions`

**Request**:
```json
{
  "name": "custom:action",
  "resource": "custom",
  "action": "action"
}
```

### Check Permission

**Endpoint**: `POST /api/v1/permissions/check`

**Request**:
```json
{
  "resource": "users",
  "action": "read"
}
```

**Response**:
```json
{
  "has_permission": true,
  "resource": "users",
  "action": "read"
}
```

### Initialize System Permissions

**Endpoint**: `POST /api/v1/permissions/initialize`

Creates default system permissions (users:*, roles:*, permissions:*).

## Permission System

### Format

Permissions follow the format `resource:action`:

- `users:read` - Read user information
- `users:write` - Create/update users
- `users:delete` - Delete users
- `roles:read` - Read roles
- `roles:write` - Create/update roles
- `permissions:read` - Read permissions

### Wildcards

- `users:*` - All actions on users
- `*:*` - All permissions (superuser)

## Error Responses

### 400 Bad Request
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request data"
  }
}
```

### 401 Unauthorized
```json
{
  "error": {
    "code": "authentication_error",
    "message": "Invalid or expired token"
  }
}
```

### 403 Forbidden
```json
{
  "error": {
    "code": "authorization_error",
    "message": "Insufficient permissions"
  }
}
```

### 404 Not Found
```json
{
  "error": {
    "code": "not_found",
    "message": "Resource not found"
  }
}
```

### 409 Conflict
```json
{
  "error": {
    "code": "conflict_error",
    "message": "Resource already exists"
  }
}
```

### 429 Too Many Requests
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Too many requests, please try again later",
    "details": {
      "retry_after": 300
    }
  }
}
```

## Rate Limiting

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| General (unauthenticated) | 100 | 1 hour |
| General (authenticated) | 1000 | 1 hour |
| Login attempts | 5 | 5 minutes |
| Password reset | 3 | 1 hour |

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Security

### Password Requirements

- Minimum 8 characters
- Maximum 128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### Account Lockout

After 5 failed login attempts, accounts are locked for 30 minutes.

### Password Hashing

Passwords are hashed using Argon2id with:
- Memory cost: 64 MB
- Time cost: 3 iterations
- Parallelism: 4 threads

## SDK Examples

### Python

```python
import httpx

BASE_URL = "http://localhost:8000"

# Login
async def login(username: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        return response.json()

# Make authenticated request
async def get_users(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

### JavaScript/TypeScript

```typescript
const BASE_URL = "http://localhost:8000";

// Login
async function login(username: string, password: string) {
  const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return await response.json();
}

// Make authenticated request
async function getUsers(token: string) {
  const response = await fetch(`${BASE_URL}/api/v1/users`, {
    headers: { "Authorization": `Bearer ${token}` },
  });
  return await response.json();
}
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Get users (replace TOKEN with actual token)
curl http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer TOKEN"
```

## Changelog

### v0.1.0
- Initial release
- JWT authentication
- RBAC system
- User/Role/Permission management
- Audit logging
- Rate limiting
