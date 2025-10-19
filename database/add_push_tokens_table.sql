-- Push Tokens Table for Expo Push Notifications
-- Stores device push notification tokens for sending notifications to users

CREATE TABLE IF NOT EXISTS push_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Expo push token from device
    expo_push_token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Device information
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('ios', 'android')),
    device_name VARCHAR(100),
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_push_tokens_user_id ON push_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_push_tokens_expo_token ON push_tokens(expo_push_token);
CREATE INDEX IF NOT EXISTS idx_push_tokens_active ON push_tokens(user_id, is_active) WHERE is_active = TRUE;

-- Unique constraint for user + token combination
CREATE UNIQUE INDEX IF NOT EXISTS idx_push_tokens_user_token ON push_tokens(user_id, expo_push_token);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_push_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
DROP TRIGGER IF EXISTS push_tokens_updated_at_trigger ON push_tokens;
CREATE TRIGGER push_tokens_updated_at_trigger
    BEFORE UPDATE ON push_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_push_tokens_updated_at();

-- Comments for documentation
COMMENT ON TABLE push_tokens IS 'Expo push notification tokens for user devices';
COMMENT ON COLUMN push_tokens.expo_push_token IS 'Expo push token from device (format: ExponentPushToken[xxx])';
COMMENT ON COLUMN push_tokens.device_type IS 'Device platform: ios or android';
COMMENT ON COLUMN push_tokens.device_name IS 'Device model name (e.g., iPhone 14, Pixel 6)';
COMMENT ON COLUMN push_tokens.is_active IS 'Whether token is active and should receive notifications';
COMMENT ON COLUMN push_tokens.last_used_at IS 'Last time a notification was sent to this token';
