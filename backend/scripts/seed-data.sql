-- Seed data for local development
-- This script inserts test data after tables are created

-- Note: This script runs after init-db.sql but requires tables to exist
-- It's designed to work with the Alembic migration system
-- Run this after: alembic upgrade head

DO $$
DECLARE
    admin_role_id UUID;
    user_role_id UUID;
    test_user_id UUID;
    admin_user_id UUID;
BEGIN
    -- Check if tables exist
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'roles') THEN

        -- ============================================
        -- Create default roles if they don't exist
        -- ============================================

        -- Admin role
        INSERT INTO roles (id, name, description, is_default, created_at, updated_at)
        SELECT uuid_generate_v4(), 'admin', 'Administrator with full system access', false, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'admin')
        RETURNING id INTO admin_role_id;

        -- User role
        INSERT INTO roles (id, name, description, is_default, created_at, updated_at)
        SELECT uuid_generate_v4(), 'user', 'Standard user with limited access', true, NOW(), NOW
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'user')
        RETURNING id INTO user_role_id;

        -- Superuser role
        INSERT INTO roles (id, name, description, is_default, created_at, updated_at)
        SELECT uuid_generate_v4(), 'superuser', 'Superuser with all permissions', false, NOW(), NOW
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'superuser');

        -- Moderator role
        INSERT INTO roles (id, name, description, is_default, created_at, updated_at)
        SELECT uuid_generate_v4(), 'moderator', 'Content moderator', false, NOW(), NOW
        WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = 'moderator');

        RAISE NOTICE 'Default roles created';
    END IF;

    -- Check if permissions table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'permissions') THEN

        -- ============================================
        -- Create system permissions if they don't exist
        -- ============================================

        -- Users permissions
        INSERT INTO permissions (id, name, resource, action, created_at, updated_at) VALUES
            (uuid_generate_v4(), 'users:create', 'users', 'create', NOW(), NOW),
            (uuid_generate_v4(), 'users:read', 'users', 'read', NOW(), NOW),
            (uuid_generate_v4(), 'users:update', 'users', 'update', NOW(), NOW),
            (uuid_generate_v4(), 'users:delete', 'users', 'delete', NOW(), NOW)
        ON CONFLICT (name) DO NOTHING;

        -- Roles permissions
        INSERT INTO permissions (id, name, resource, action, created_at, updated_at) VALUES
            (uuid_generate_v4(), 'roles:create', 'roles', 'create', NOW(), NOW),
            (uuid_generate_v4(), 'roles:read', 'roles', 'read', NOW(), NOW),
            (uuid_generate_v4(), 'roles:update', 'roles', 'update', NOW(), NOW),
            (uuid_generate_v4(), 'roles:delete', 'roles', 'delete', NOW(), NOW)
        ON CONFLICT (name) DO NOTHING;

        -- Permissions permissions (meta!)
        INSERT INTO permissions (id, name, resource, action, created_at, updated_at) VALUES
            (uuid_generate_v4(), 'permissions:create', 'permissions', 'create', NOW(), NOW),
            (uuid_generate_v4(), 'permissions:read', 'permissions', 'read', NOW(), NOW),
            (uuid_generate_v4(), 'permissions:update', 'permissions', 'update', NOW(), NOW),
            (uuid_generate_v4(), 'permissions:delete', 'permissions', 'delete', NOW(), NOW)
        ON CONFLICT (name) DO NOTHING;

        RAISE NOTICE 'System permissions created';

        -- ============================================
        -- Assign all permissions to admin role
        -- ============================================
        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'role_permissions') THEN
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name = 'admin'
            ON CONFLICT DO NOTHING;

            RAISE NOTICE 'Permissions assigned to admin role';
        END IF;
    END IF;

    -- Check if users table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN

        -- ============================================
        -- Create test users
        -- ============================================

        -- Note: Password hashes are for 'TestPassword123!'
        -- In production, use proper password hashing

        -- Admin user
        INSERT INTO users (id, username, email, password_hash, first_name, last_name, is_active, is_verified, created_at, updated_at)
        SELECT
            uuid_generate_v4(),
            'admin',
            'admin@example.com',
            '$argon2id$v=19$m=65536,t=3,p=4$Z2Z6Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3$hashed_password_placeholder',
            'Admin',
            'User',
            true,
            true,
            NOW(),
            NOW
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
        RETURNING id INTO admin_user_id;

        -- Test user
        INSERT INTO users (id, username, email, password_hash, first_name, last_name, is_active, is_verified, created_at, updated_at)
        SELECT
            uuid_generate_v4(),
            'testuser',
            'test@example.com',
            '$argon2id$v=19$m=65536,t=3,p=4$Z2Z6Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3Z3Y3$hashed_password_placeholder',
            'Test',
            'User',
            true,
            true,
            NOW(),
            NOW
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'testuser')
        RETURNING id INTO test_user_id;

        RAISE NOTICE 'Test users created';

        -- ============================================
        -- Assign roles to users
        -- ============================================
        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_roles') THEN
            -- Assign admin role to admin user
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM users u, roles r
            WHERE u.username = 'admin' AND r.name = 'admin'
            ON CONFLICT DO NOTHING;

            -- Assign superuser role to admin user
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM users u, roles r
            WHERE u.username = 'admin' AND r.name = 'superuser'
            ON CONFLICT DO NOTHING;

            -- Assign user role to test user
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.id, r.id
            FROM users u, roles r
            WHERE u.username = 'testuser' AND r.name = 'user'
            ON CONFLICT DO NOTHING;

            RAISE NOTICE 'Roles assigned to users';
        END IF;
    END IF;

    RAISE NOTICE 'Seed data loaded successfully!';

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error loading seed data: %', SQLERRM;
END $$;
