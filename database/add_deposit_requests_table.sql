-- ============================================
-- DARI Wallet V2 - Deposit Requests Table
-- ============================================
-- Description: Add deposit_requests table for USDC deposit functionality
-- Author: DARI Team
-- Date: 2025-10-12
-- ============================================

-- Create enum type for deposit status
DO $$ BEGIN
    CREATE TYPE depositstatus AS ENUM (
        'PENDING',      -- Waiting for user to send USDC to relayer
        'RECEIVED',     -- Relayer received USDC
        'PROCESSING',   -- Transferring USDC to user wallet
        'COMPLETED',    -- Transfer completed successfully
        'EXPIRED',      -- Request expired (10 minutes timeout)
        'FAILED'        -- Transfer failed
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create deposit_requests table
CREATE TABLE IF NOT EXISTS deposit_requests (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- User information
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_wallet_address VARCHAR(42) NOT NULL,
    
    -- Deposit details
    deposit_id VARCHAR(50) UNIQUE NOT NULL,
    amount NUMERIC(36, 18) NOT NULL CHECK (amount > 0),
    token VARCHAR(10) NOT NULL DEFAULT 'USDC',
    
    -- Relayer information
    relayer_address VARCHAR(42) NOT NULL,
    
    -- Status tracking
    status depositstatus NOT NULL DEFAULT 'PENDING',
    
    -- Transaction tracking
    deposit_tx_hash VARCHAR(66) NULL,          -- User -> Relayer transaction hash
    transfer_tx_hash VARCHAR(66) NULL,         -- Relayer -> User transaction hash
    
    -- Amounts
    received_amount NUMERIC(36, 18) NULL,      -- Actual amount received by relayer
    transferred_amount NUMERIC(36, 18) NULL,   -- Amount sent to user wallet
    
    -- QR code data (JSON string)
    qr_data TEXT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE NULL,
    completed_at TIMESTAMP WITH TIME ZONE NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Error tracking
    error_message TEXT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_deposit_requests_deposit_id ON deposit_requests(deposit_id);
CREATE INDEX IF NOT EXISTS idx_deposit_requests_user_id ON deposit_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_deposit_requests_status ON deposit_requests(status);
CREATE INDEX IF NOT EXISTS idx_deposit_requests_expires_at ON deposit_requests(expires_at);
CREATE INDEX IF NOT EXISTS idx_deposit_requests_created_at ON deposit_requests(created_at DESC);

-- Create function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_deposit_requests_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS trigger_deposit_requests_updated_at ON deposit_requests;
CREATE TRIGGER trigger_deposit_requests_updated_at
    BEFORE UPDATE ON deposit_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_deposit_requests_updated_at();

-- Add comments for documentation
COMMENT ON TABLE deposit_requests IS 'Stores USDC deposit requests via relayer wallet with 10-minute timeout';
COMMENT ON COLUMN deposit_requests.deposit_id IS 'Unique identifier for the deposit request (format: DEP-YYYYMMDDHHMMSS-XXXX)';
COMMENT ON COLUMN deposit_requests.amount IS 'Expected USDC amount to be deposited';
COMMENT ON COLUMN deposit_requests.relayer_address IS 'Relayer wallet address where user sends USDC';
COMMENT ON COLUMN deposit_requests.status IS 'Current status of the deposit request';
COMMENT ON COLUMN deposit_requests.deposit_tx_hash IS 'Transaction hash of user sending USDC to relayer';
COMMENT ON COLUMN deposit_requests.transfer_tx_hash IS 'Transaction hash of relayer sending USDC to user';
COMMENT ON COLUMN deposit_requests.qr_data IS 'JSON data for QR code generation';
COMMENT ON COLUMN deposit_requests.expires_at IS 'Expiration time (created_at + 10 minutes)';
COMMENT ON COLUMN deposit_requests.retry_count IS 'Number of retry attempts for failed transfers';

-- Grant permissions (adjust user as needed)
-- GRANT SELECT, INSERT, UPDATE ON deposit_requests TO dari_user;
-- GRANT USAGE, SELECT ON SEQUENCE deposit_requests_id_seq TO dari_user;

-- ============================================
-- Verification Queries
-- ============================================

-- Check if table was created successfully
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'deposit_requests';

-- Check columns
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'deposit_requests'
ORDER BY ordinal_position;

-- Check indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'deposit_requests';

-- Check enum values
SELECT 
    enumlabel 
FROM pg_enum 
WHERE enumtypid = (
    SELECT oid 
    FROM pg_type 
    WHERE typname = 'depositstatus'
)
ORDER BY enumsortorder;

COMMIT;

-- ============================================
-- Sample Data (Optional - for testing)
-- ============================================

-- Uncomment to insert sample deposit request
/*
INSERT INTO deposit_requests (
    user_id,
    user_wallet_address,
    deposit_id,
    amount,
    token,
    relayer_address,
    status,
    expires_at,
    qr_data
) VALUES (
    1,  -- Replace with actual user_id
    '0x1234567890123456789012345678901234567890',  -- User wallet
    'DEP-20251012120000-TEST',
    100.00,
    'USDC',
    '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',  -- Relayer address
    'PENDING',
    NOW() + INTERVAL '10 minutes',
    '{"address":"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb","amount":"100","token":"USDC","network":"Polygon","deposit_id":"DEP-20251012120000-TEST","chain_id":137}'
);
*/
