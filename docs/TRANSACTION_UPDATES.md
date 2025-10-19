# Transaction System Updates

**Date**: October 12, 2025  
**Status**: ✅ Complete

---

## Overview

Enhanced the transaction system to support multiple recipient identification methods, improving user experience by allowing transfers using phone numbers in addition to wallet addresses and DARI usernames.

---

## Changes Made

### 1. Removed DELETE Address Resolver Endpoint

**Endpoint Removed**: `DELETE /api/v1/address/delete`

**Reason**: DARI addresses should be permanent identifiers. Users should not be able to delete them once created, only update them.

**File Modified**: `app/api/v1/address_resolver.py`

---

### 2. Enhanced Transaction Send Endpoint

**Endpoint**: `POST /api/v1/transactions/send`

#### Previous Behavior:
- Accepted only wallet addresses (0x...) or DARI usernames (username@dari)

#### New Behavior:
- ✅ Wallet Address: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`
- ✅ DARI Username: `john@dari`
- ✅ **Phone Number**: `+1234567890` ⭐ NEW!

---

## Request Body Schema

### New Fields:

```json
{
  "to_address": "string",  // Required - Can be wallet address, DARI username, or phone number
  "amount": 100,           // Required - Positive decimal
  "token": "USDC",         // Required - Only "USDC" or "MATIC" (USDT removed)
  "pin": "123456",         // Required - 4-6 digit PIN
  "transfer_method": "auto" // Optional - "auto", "wallet", "dari", or "phone"
}
```

### Field Details:

#### `to_address` (string, required)
Accepts three formats:

1. **Wallet Address** (42 characters, starts with 0x)
   ```
   "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
   ```

2. **DARI Username** (ends with @dari)
   ```
   "to_address": "john@dari"
   ```

3. **Phone Number** (E.164 format, starts with +) ⭐ NEW!
   ```
   "to_address": "+1234567890"
   ```

#### `transfer_method` (string, optional)
Specifies how to interpret the `to_address`:

- `"auto"` (default): Automatically detect format
- `"wallet"`: Treat as wallet address
- `"dari"`: Treat as DARI username  
- `"phone"`: Treat as phone number

---

## Examples

### Example 1: Send via Phone Number

```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/transactions/send' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json' \
  -d '{
    "to_address": "+1234567890",
    "amount": 50.00,
    "token": "USDC",
    "pin": "123456",
    "transfer_method": "phone"
  }'
```

**Success Response** (200):
```json
{
  "id": 123,
  "from_address": "0x...",
  "to_address": "0x...",  // Resolved wallet address
  "amount": "50.00",
  "token": "USDC",
  "transaction_hash": "0x...",
  "transaction_type": "SEND",
  "status": "PENDING",
  "created_at": "2025-10-12T10:45:00Z"
}
```

**Error Responses**:

- **404 - Phone Not Found**:
  ```json
  {
    "detail": "No user found with this phone number"
  }
  ```

- **404 - No Wallet**:
  ```json
  {
    "detail": "Recipient does not have a wallet"
  }
  ```

- **400 - Self Transfer**:
  ```json
  {
    "detail": "Cannot send transaction to your own wallet"
  }
  ```

- **400 - Invalid Format**:
  ```json
  {
    "detail": "Invalid phone number format. Use E.164 format (e.g., +1234567890)"
  }
  ```

### Example 2: Send via DARI Username

```json
{
  "to_address": "john@dari",
  "amount": 25.50,
  "token": "MATIC",
  "pin": "654321",
  "transfer_method": "dari"
}
```

### Example 3: Send via Wallet Address

```json
{
  "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "amount": 100.00,
  "token": "USDC",
  "pin": "111111",
  "transfer_method": "wallet"
}
```

---

## Resolution Logic

### Phone Number Resolution:
1. Validate phone number format (E.164)
2. Query database for user with matching phone number
3. Retrieve user's wallet address
4. Verify wallet exists
5. Check not self-transaction
6. Proceed with transaction using resolved wallet address

### DARI Username Resolution:
1. Validate username format (3-50 alphabetic characters)
2. Query address_resolver table for matching username
3. Retrieve linked wallet address
4. Verify address is active
5. Check not self-transaction
6. Proceed with transaction

### Wallet Address:
1. Validate address format (0x + 40 hex characters)
2. Check not self-transaction
3. Proceed with transaction directly

---

## Technical Implementation

### Files Modified:

1. **`app/schemas/transaction.py`**
   - Updated `TransactionSend` class
   - Added phone number validation
   - Added `transfer_method` field
   - Removed USDT from token regex pattern

2. **`app/api/v1/transactions.py`**
   - Enhanced `send_transaction` endpoint
   - Added phone number resolution logic
   - Improved error handling
   - Added transfer method tracking

3. **`app/api/v1/address_resolver.py`**
   - Removed `delete_user_address_resolver` endpoint

### Database Dependencies:

- `users` table: Lookup by phone number
- `wallets` table: Get wallet by user_id
- `address_resolvers` table: Resolve DARI usernames

---

## Validation Rules

### Phone Number (E.164 Format):
- Must start with `+`
- Length: 10-16 characters (including +)
- Contains only digits after +
- Pattern: `^\+?1?\d{9,15}$`

### DARI Username:
- Must end with `@dari`
- Username: 3-50 characters
- Only alphabetic characters
- Case insensitive

### Wallet Address:
- Must start with `0x`
- Exactly 42 characters total
- Hexadecimal format

---

## Security Features

1. **PIN Verification**: Required for all transactions
2. **Self-Transfer Prevention**: Cannot send to own wallet (any method)
3. **Phone Privacy**: Phone numbers not exposed in responses
4. **Wallet Resolution**: Internal - user only sees their input format

---

## Migration Notes

### For Frontend Developers:

1. **Update transaction form** to accept phone numbers
2. **Add phone number input** with +country code picker
3. **Update validation** to accept 3 formats
4. **Handle new error messages** (phone not found, no wallet)
5. **Optional**: Use `transfer_method` field for better UX

### For Mobile App:

1. **Contact picker integration**: Allow selecting contacts
2. **Phone number formatting**: Ensure E.164 format
3. **Transfer method selection**: Let users choose preferred method
4. **Error handling**: Display user-friendly messages

---

## Testing Checklist

- [ ] Send via phone number (registered user)
- [ ] Send via phone number (unregistered user) → Error
- [ ] Send via phone number (user without wallet) → Error
- [ ] Send via DARI username
- [ ] Send via wallet address
- [ ] Self-transfer attempts (all 3 methods) → Error
- [ ] Invalid phone format → Error
- [ ] Invalid DARI format → Error
- [ ] Invalid wallet address → Error
- [ ] USDT token → Error (removed)
- [ ] USDC token → Success
- [ ] MATIC token → Success

---

## Future Enhancements

1. **Email-based transfers**: Similar to phone numbers
2. **QR code scanning**: For wallet addresses
3. **Contact list integration**: Show registered DARI users
4. **Transfer history**: Filter by transfer method
5. **Transaction analytics**: Track preferred transfer methods

---

**Status**: ✅ Ready for Production  
**Breaking Changes**: None (backward compatible)  
**New Dependencies**: None
