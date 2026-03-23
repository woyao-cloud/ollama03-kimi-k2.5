-- Database initialization script
-- This script is automatically executed when PostgreSQL container starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema if not exists (tables will be created by Alembic)
-- This script is mainly for setting up extensions and initial configuration

-- Set timezone
SET TIMEZONE='UTC';

-- Create custom types if needed
-- Note: Main table creation is handled by Alembic migrations

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO devuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO devuser;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed for user_management';
END $$;
