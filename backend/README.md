# User Management System - Backend

FastAPI backend for user management system with JWT authentication, RBAC permissions, and audit logging.

## Technology Stack

- **Framework**: FastAPI + Python 3.11+
- **Database**: PostgreSQL / SQLite (testing)
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Authentication**: JWT + OAuth2
- **Caching**: Redis
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: Black + Ruff + mypy

## Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API routes
│   │   ├── endpoints/    # API endpoints
│   │   └── router.py     # Route aggregation
│   ├── core/             # Security, logging, exceptions
│   ├── domain/           # Domain models
│   ├── application/      # Application services
│   ├── infrastructure/   # Database, cache, external services
│   ├── schemas/          # Pydantic schemas
│   ├── config.py         # Application configuration
│   └── main.py           # Application entry point
├── alembic/              # Database migrations
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── pyproject.toml        # Dependencies and tool config
└── alembic.ini          # Alembic configuration
```

## Quick Start

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Initialize Database

```bash
alembic upgrade head
```

### 5. Run Application

```bash
# Development with auto-reload
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Development

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .
ruff check . --fix

# Type check
mypy .

# Run all checks
black . && ruff check . && mypy .
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_models.py -v
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## API Documentation

When running in development mode, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | postgresql+asyncpg://... |
| `JWT_SECRET_KEY` | JWT signing key | required |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 |
| `LOG_LEVEL` | Logging level | INFO |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | http://localhost:3000 |

See `.env.example` for complete list.

## Architecture

### Layered Architecture

1. **API Layer**: HTTP request handling
2. **Application Layer**: Business logic coordination
3. **Domain Layer**: Core business rules
4. **Infrastructure Layer**: External dependencies

### Authentication Flow

1. User submits credentials to `/auth/login`
2. Server validates and returns access + refresh tokens
3. Client uses access token in Authorization header
4. Token expires → use refresh token to get new access token

### RBAC Permissions

- Users have roles
- Roles have permissions
- Permissions define resource + action
- API endpoints check required permissions

## License

MIT
