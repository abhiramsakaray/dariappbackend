-- Payment Methods Table
-- Stores user payment methods (Bank Accounts and UPI) for withdrawals and refunds

CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Payment method type: 'bank' or 'upi'
    type VARCHAR(20) NOT NULL CHECK (type IN ('bank', 'upi')),
    
    -- Display name for the payment method
    name VARCHAR(100) NOT NULL,
    
    -- Payment details stored as JSON
    -- For bank: {"bank_name": "...", "account_number": "...", "ifsc_code": "...", "account_holder_name": "..."}
    -- For UPI: {"upi_name": "...", "upi_id": "..."}
    details JSONB NOT NULL,
    
    -- Default payment method flag (only one per user should be true)
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Verification status (for future use)
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_is_default ON payment_methods(user_id, is_default) WHERE is_default = TRUE;
CREATE INDEX IF NOT EXISTS idx_payment_methods_type ON payment_methods(user_id, type);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_payment_methods_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
DROP TRIGGER IF EXISTS payment_methods_updated_at_trigger ON payment_methods;
CREATE TRIGGER payment_methods_updated_at_trigger
    BEFORE UPDATE ON payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_methods_updated_at();

-- Comments for documentation
COMMENT ON TABLE payment_methods IS 'User payment methods for withdrawals and refunds';
COMMENT ON COLUMN payment_methods.type IS 'Payment method type: bank or upi';
COMMENT ON COLUMN payment_methods.name IS 'Display name (e.g., bank name or UPI provider)';
COMMENT ON COLUMN payment_methods.details IS 'JSON object containing payment details';
COMMENT ON COLUMN payment_methods.is_default IS 'Whether this is the default payment method';
COMMENT ON COLUMN payment_methods.is_verified IS 'Whether the payment method has been verified';
