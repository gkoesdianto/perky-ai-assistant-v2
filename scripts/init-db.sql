-- Database initialization script for Perky AI Assistant v2
-- This script runs automatically when PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types if needed
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('user', 'admin', 'moderator');
    END IF;
END $$;

-- Create audit function for tracking changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create initial schema (optional, for organization)
CREATE SCHEMA IF NOT EXISTS perky;

-- Set search path
SET search_path TO perky, public;

-- Add any initial schema setup here
-- Note: Alembic will handle most table creation, but we can add
-- database-level configurations, functions, and initial data here

-- Example: Create a table for system configuration (if not managed by Alembic)
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default system configurations
INSERT INTO system_config (key, value, description)
VALUES
    ('system_version', '2.0.0', 'Current system version'),
    ('maintenance_mode', 'false', 'System maintenance mode flag'),
    ('max_file_upload_size', '10485760', 'Maximum file upload size in bytes (10MB)')
ON CONFLICT (key) DO NOTHING;

-- Create trigger for updating timestamps
DROP TRIGGER IF EXISTS update_system_config_updated_at ON system_config;
CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your user)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO perky_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO perky_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO perky_user;

-- Initial setup complete
-- Tables will be created by Alembic migrations
