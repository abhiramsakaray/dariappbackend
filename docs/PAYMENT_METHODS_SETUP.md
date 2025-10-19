# Payment Methods - Quick Setup Guide

## ✅ Setup Instructions

### Step 1: Create Database Table

Run this SQL command in your PostgreSQL database:

```sql
-- Copy and paste this entire block into your psql or database client

CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('bank', 'upi')),
    name VARCHAR(100) NOT NULL,
    details JSONB NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_is_default ON payment_methods(user_id, is_default) WHERE is_default = TRUE;
CREATE INDEX IF NOT EXISTS idx_payment_methods_type ON payment_methods(user_id, type);

CREATE OR REPLACE FUNCTION update_payment_methods_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS payment_methods_updated_at_trigger ON payment_methods;
CREATE TRIGGER payment_methods_updated_at_trigger
    BEFORE UPDATE ON payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_methods_updated_at();
```

### Step 2: Restart Server

The server should already be running. If not:
```bash
uvicorn app.main:app --reload
```

### Step 3: Test the API

Get your JWT token first (login), then test:

```bash
# Test: List payment methods (should be empty initially)
curl -X GET http://10.16.88.251:8000/api/v1/payment-methods \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎉 That's It!

The backend is **100% complete** and ready to use!

See `docs/PAYMENT_METHODS_COMPLETE.md` for:
- Full API documentation
- All endpoints with examples
- Validation rules
- Testing guide
- Mobile app integration examples

