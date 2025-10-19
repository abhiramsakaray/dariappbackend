# Manual Database Setup - Deposit Requests Table

## Quick Setup

Run this command in your PostgreSQL database:

```bash
psql -U dariwallettest -d dariwallet_v2 -f database/add_deposit_requests_table.sql
```

Or connect to PostgreSQL and run:

```bash
psql -U dariwallettest -d dariwallet_v2
```

Then paste the contents of `add_deposit_requests_table.sql`.

## What This Creates

### 1. Enum Type: `depositstatus`
- `PENDING` - Waiting for user to send USDC
- `RECEIVED` - Relayer received USDC
- `PROCESSING` - Transferring to user wallet
- `COMPLETED` - Transfer completed
- `EXPIRED` - 10-minute timeout reached
- `FAILED` - Transfer failed

### 2. Table: `deposit_requests`

**Key Columns:**
- `deposit_id` - Unique identifier (e.g., DEP-20251012120000-A1B2)
- `user_id` - References users table
- `amount` - USDC amount to deposit
- `relayer_address` - Where user sends USDC
- `status` - Current status (enum)
- `expires_at` - Expiration time (created_at + 10 minutes)
- `qr_data` - JSON data for QR code generation

**Transaction Tracking:**
- `deposit_tx_hash` - User → Relayer transaction
- `transfer_tx_hash` - Relayer → User transaction

**Timestamps:**
- `created_at` - When deposit request created
- `expires_at` - When it expires (10 minutes)
- `received_at` - When funds received
- `completed_at` - When transfer completed
- `updated_at` - Auto-updated on changes

### 3. Indexes
- `idx_deposit_requests_deposit_id` - Fast lookup by deposit ID
- `idx_deposit_requests_user_id` - Fast lookup by user
- `idx_deposit_requests_status` - Fast filtering by status
- `idx_deposit_requests_expires_at` - Fast expiration checks
- `idx_deposit_requests_created_at` - Chronological sorting

### 4. Triggers
- `trigger_deposit_requests_updated_at` - Auto-updates `updated_at` timestamp

## Verification

After running the SQL file, verify the table was created:

```sql
-- Check table exists
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'deposit_requests';

-- Check columns
\d deposit_requests

-- Check indexes
\di deposit_requests*

-- Check enum values
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'depositstatus');
```

## Alternative: Using Alembic

Instead of manual SQL, you can use Alembic migrations:

```bash
# Run the migration
alembic upgrade head
```

The migration file is at:
`alembic/versions/dep001_add_deposit_requests_table.py`

## Rollback (If Needed)

To remove the deposit_requests table:

```sql
-- Drop table
DROP TABLE IF EXISTS deposit_requests CASCADE;

-- Drop enum type
DROP TYPE IF EXISTS depositstatus;
```

## Next Steps

1. ✅ Create the table (using SQL file or Alembic)
2. ✅ Restart your FastAPI server
3. ✅ Start Celery worker for background processing
4. ✅ Test the deposit API endpoints

See `docs/DEPOSIT_API.md` for API documentation and testing instructions.
