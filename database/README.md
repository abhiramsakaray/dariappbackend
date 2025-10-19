# Database Files

This folder contains database setup and migration SQL files.

## Files

### Setup Scripts
- **setup_database.sql** - Initial database setup and schema creation

### Migration Scripts
- **add_transaction_columns.sql** - Adds fee and country tracking columns to transactions table
- **add_deposit_requests_table.sql** - Adds deposit_requests table for USDC deposit functionality via relayer

## Database Schema Overview

### Main Tables
- **users** - User accounts with email, phone, password
- **wallets** - Polygon blockchain wallets (encrypted private keys)
- **tokens** - Supported tokens (USDC, MATIC)
- **transactions** - Transaction records with fee breakdown
- **deposit_requests** - USDC deposit requests via relayer (10-minute timeout)
- **address_resolvers** - DARI username to wallet mappings (@dari addresses)
- **kyc_requests** - KYC verification data
- **qr_codes** - Generated QR codes for payments
- **notifications** - User notifications
- **user_files** - KYC document storage

## Database Migrations

We use **Alembic** for database migrations. Migration files are in the `alembic/versions/` directory.

### Running Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Database Configuration

Database connection is configured via environment variables:
- `DATABASE_URL` - Async PostgreSQL connection (postgresql+asyncpg://...)
- `DATABASE_URL_SYNC` - Sync PostgreSQL connection (postgresql://...)

See `.env.example` for configuration examples.
