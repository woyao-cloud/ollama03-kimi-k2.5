# Local Development Setup Guide

This guide helps you set up the User Management API for local development and debugging.

## Prerequisites

- Python 3.11+
- Docker Desktop or Docker Engine
- Make (optional but recommended)

## Quick Start (5 minutes)

```bash
cd backend

# 1. Start infrastructure (PostgreSQL + Redis)
make db-start

# 2. Install dependencies
make dev-install

# 3. Run migrations
make migrate

# 4. Load seed data
make seed-db

# 5. Start development server
make run-dev
```

API is now running at `http://localhost:8000`

---

## Detailed Setup

### Option 1: Using Make (Recommended)

All common tasks are available via Make commands:

```bash
make help           # Show all available commands
make setup          # Complete initial setup
make db-start       # Start PostgreSQL and Redis
make migrate        # Run database migrations
make seed-db        # Load test data
make run-dev        # Start with auto-reload
```

### Option 2: Manual Setup

#### Step 1: Start Infrastructure Services

```bash
# Using docker-compose directly
docker-compose up -d postgres redis

# Or with Make
make db-start
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379

#### Step 2: Configure Environment

```bash
# Copy the local development environment file
cp .env.local .env

# The default configuration should work out of the box
# Edit .env if you need to customize ports or credentials
```

#### Step 3: Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

#### Step 4: Initialize Database

```bash
# Run migrations to create tables
alembic upgrade head

# Load seed data for development
python scripts/init_db.py
```

#### Step 5: Start the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Or with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Development Workflow

### Daily Development Commands

```bash
# Start your day - spin up infrastructure
make db-start

# Run migrations (if there are new changes)
make migrate

# Start the development server
make run-dev

# Run tests
make test

# Run tests with coverage
make test-cov

# Format and lint code before committing
make format
make lint

# Stop at end of day
make db-stop
```

### Database Management

```bash
# Reset database (WARNING: deletes all data)
make db-reset

# Access PostgreSQL shell directly
make db-shell

# Or use docker-compose
docker-compose exec postgres psql -U devuser -d user_management
```

### View Logs

```bash
# Database logs
make db-logs

# All container logs
make docker-logs
```

---

## Debugging

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Debug with debugpy",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "justMyCode": false
    }
  ]
}
```

### Using debugpy

```bash
# Install debugpy
pip install debugpy

# Run with debug server
make debug
# or
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --reload
```

Then attach your debugger to `localhost:5678`.

---

## Test Data

The seed data creates the following accounts:

| Username | Email | Password | Roles |
|----------|-------|----------|-------|
| `admin` | admin@example.com | TestPassword123! | admin, superuser |
| `testuser` | test@example.com | TestPassword123! | user |

### Available Permissions

```
users:create, users:read, users:update, users:delete
roles:create, roles:read, roles:update, roles:delete
permissions:create, permissions:read, permissions:update, permissions:delete
```

---

## Database Management with PgAdmin

A PgAdmin instance is included for easy database management:

1. Start all services: `docker-compose up -d`
2. Open browser: http://localhost:5050
3. Login credentials:
   - Email: `admin@example.com`
   - Password: `admin123`
4. Add PostgreSQL server:
   - Name: `Local PostgreSQL`
   - Host: `postgres`
   - Port: `5432`
   - Username: `devuser`
   - Password: `devpassword`

---

## Common Issues

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Restart services
docker-compose restart postgres redis
```

### Migration Errors

```bash
# Reset migrations (careful - drops data)
make db-reset
make migrate

# Or check migration status
alembic current
alembic history --verbose
```

### Port Already in Use

```bash
# Find process using port 5432
lsof -i :5432  # macOS/Linux
netstat -ano | findstr :5432  # Windows

# Stop conflicting service or change port in .env
```

---

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000 | - |
| API Docs (Swagger) | http://localhost:8000/docs | - |
| API Docs (ReDoc) | http://localhost:8000/redoc | - |
| PostgreSQL | localhost:5432 | devuser/devpassword |
| Redis | localhost:6379 | redisdev |
| PgAdmin | http://localhost:5050 | admin@example.com/admin123 |

---

## Environment Configuration

See `.env.local` for all available options. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://devuser:devpassword@localhost:5432/user_management` |
| `REDIS_URL` | Redis connection | `redis://:redisdev@localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing key | (dev key) |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging verbosity | `DEBUG` |

---

## API Testing

### Using curl

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=TestPassword123!"

# Get current user (replace TOKEN with actual token)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"

# List users
curl http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer TOKEN"
```

### Using HTTPie (recommended)

```bash
# Login
http POST :8000/api/v1/auth/login username=admin password=TestPassword123!

# Store token
TOKEN=$(http :8000/api/v1/auth/login username=admin password=TestPassword123! | jq -r .access_token)

# Use token
http :8000/api/v1/auth/me "Authorization:Bearer $TOKEN"
```

---

## Next Steps

1. Explore the API documentation at http://localhost:8000/docs
2. Review the code structure in `app/`
3. Run tests with `make test`
4. Start building features!

For production deployment, see `DEPLOYMENT_GUIDE.md`.
