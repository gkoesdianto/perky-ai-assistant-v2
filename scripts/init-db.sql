-- Initial database setup script for Perky AI Assistant
-- This script runs automatically when PostgreSQL container starts

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial schema (optional, for organization)
CREATE SCHEMA IF NOT EXISTS perky;

-- Set search path
SET search_path TO perky, public;

-- Initial setup complete
-- Tables will be created by Alembic migrations
