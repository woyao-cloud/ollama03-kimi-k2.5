#!/bin/bash
# Entrypoint script for Docker container

set -e

echo "🚀 Starting User Management System API..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! nc -z postgres 5432; do
  sleep 0.1
done
echo "✅ Database is ready!"

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Initialize database with default data
echo "📝 Initializing database..."
python scripts/init_db.py

# Start the application
echo "🌟 Starting application..."
exec "$@"
