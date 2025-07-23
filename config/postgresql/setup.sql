-- PostgreSQL setup script for Real Estate CRM
-- Run this script as postgres superuser

-- Create database user
CREATE USER odoo WITH CREATEDB PASSWORD 'your_secure_password_here';

-- Create database
CREATE DATABASE real_estate_crm WITH OWNER odoo ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE real_estate_crm TO odoo;

-- Connect to the database
\c real_estate_crm;

-- Create required extensions
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- PostGIS extension for geographic features (optional)
-- CREATE EXTENSION IF NOT EXISTS "postgis";

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO odoo;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO odoo;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO odoo;

-- Performance tuning settings (adjust based on your server specs)
-- These should be added to postgresql.conf

-- Memory settings
-- shared_buffers = 256MB
-- effective_cache_size = 1GB
-- work_mem = 4MB
-- maintenance_work_mem = 64MB

-- Connection settings
-- max_connections = 100
-- superuser_reserved_connections = 3

-- Logging settings
-- log_destination = 'stderr'
-- logging_collector = on
-- log_directory = 'pg_log'
-- log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
-- log_rotation_age = 1d
-- log_rotation_size = 10MB
-- log_min_messages = warning
-- log_min_error_statement = error
-- log_min_duration_statement = 1000

-- Checkpoint settings
-- checkpoint_segments = 32
-- checkpoint_completion_target = 0.9
-- wal_buffers = 16MB

-- Query optimization
-- random_page_cost = 1.1
-- effective_io_concurrency = 2

-- Create indexes for better performance (run after Odoo installation)
-- These will be created automatically by Odoo, but listed here for reference

/*
-- Property search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_state ON real_estate_property(state);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_type ON real_estate_property(property_type_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_price ON real_estate_property(expected_price);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_location ON real_estate_property(city, state_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_bedrooms ON real_estate_property(bedrooms);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_created ON real_estate_property(create_date);

-- Lead indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_state ON real_estate_lead(stage_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_agent ON real_estate_lead(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_created ON real_estate_lead(create_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lead_partner ON real_estate_lead(partner_id);

-- Appointment indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointment_date ON real_estate_appointment(appointment_date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointment_agent ON real_estate_appointment(agent_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointment_state ON real_estate_appointment(state);

-- Commission indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_commission_agent ON real_estate_commission(agent_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_commission_date ON real_estate_commission(date_earned);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_commission_state ON real_estate_commission(state);

-- Full-text search indexes for property descriptions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_property_search 
ON real_estate_property USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
*/

-- Backup and maintenance recommendations
-- 1. Set up regular backups using pg_dump
-- 2. Monitor database size and performance
-- 3. Run VACUUM ANALYZE regularly
-- 4. Monitor slow queries
-- 5. Keep PostgreSQL updated

COMMIT;