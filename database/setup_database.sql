-- Database setup script for DARI Wallet V2
-- Run this in PostgreSQL as a superuser (postgres)

-- Create user if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'dari_user') THEN
        CREATE USER dari_user WITH PASSWORD 'dari_password';
    END IF;
END $$;

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE dari_wallet_v2 OWNER dari_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dari_wallet_v2')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dari_wallet_v2 TO dari_user;

-- Connect to the new database and grant schema privileges
\c dari_wallet_v2

-- Grant privileges on schema and future tables
GRANT ALL ON SCHEMA public TO dari_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dari_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dari_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dari_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dari_user;

-- Verify user and database
\du dari_user
\l dari_wallet_v2