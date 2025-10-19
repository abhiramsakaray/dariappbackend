-- Add transaction fee and country tracking columns
-- Run this if the alembic migration doesn't work

ALTER TABLE transactions ADD COLUMN IF NOT EXISTS platform_fee NUMERIC(36, 18);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS total_fee NUMERIC(36, 18);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS from_country VARCHAR(2);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS to_country VARCHAR(2);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS is_international BOOLEAN DEFAULT FALSE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS recipient_phone VARCHAR(20);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS transfer_method VARCHAR(20);
