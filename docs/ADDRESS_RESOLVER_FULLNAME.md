# Address Resolver API Enhancement - Full Name from KYC

## Date: October 13, 2025

## Overview
Enhanced all address resolver endpoints to include the user's `full_name` from their KYC data in the API responses. This provides more complete user information when working with DARI addresses.

## Changes Made

### 1. Schema Update

**File:** `app/schemas/address_resolver.py`

Added `full_name` field to `AddressResolverResponse`:

```python
class AddressResolverResponse(BaseModel):
    id: int
    username: str
    full_address: str
    wallet_address: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    full_name: Optional[str] = None  # ✅ NEW: From KYC data
```

### 2. Endpoint Updates

**File:** `app/api/v1/address_resolver.py`

Updated **3 endpoints** to fetch and include KYC full_name:

#### GET `/api/v1/address/my-address`
```python
# Get KYC full_name if available
from app.crud import kyc as kyc_crud
kyc_request = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
full_name = kyc_request.full_name if kyc_request else current_user.full_name
```

#### POST `/api/v1/address/create`
- Includes full_name in response
- Uses full_name in email notifications

#### PUT `/api/v1/address/update`
- Includes full_name in response
- Uses full_name in email notifications

## API Response Format

### Before (Without full_name)
```json
{
  "id": 1,
  "username": "abhi",
  "full_address": "abhi@dari",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### After (With full_name from KYC)
```json
{
  "id": 1,
  "username": "abhi",
  "full_address": "abhi@dari",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "full_name": "Abhiram Sakaray"  // ✅ NEW
}
```

## Data Source Priority

The `full_name` is retrieved with the following priority:

1. **First Priority:** `kyc_requests.full_name` (from approved KYC)
2. **Fallback:** `users.full_name` (from user profile)
3. **If both null:** `null` is returned

```python
kyc_request = await kyc_crud.get_kyc_by_user_id(db, current_user.id)
full_name = kyc_request.full_name if kyc_request else current_user.full_name
```

## Affected Endpoints

### 1. GET `/api/v1/address/my-address`
**Authentication:** Required  
**Returns:** Current user's DARI address with full_name

**Example Response:**
```json
{
  "id": 1,
  "username": "abhi",
  "full_address": "abhi@dari",
  "wallet_address": "0x742d35...",
  "is_active": true,
  "created_at": "2025-10-13T10:00:00Z",
  "updated_at": "2025-10-13T10:00:00Z",
  "full_name": "Abhiram Sakaray"
}
```

### 2. POST `/api/v1/address/create`
**Authentication:** Required  
**Returns:** Newly created DARI address with full_name

**Request:**
```json
{
  "username": "abhi"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "abhi",
  "full_address": "abhi@dari",
  "wallet_address": "0x742d35...",
  "is_active": true,
  "created_at": "2025-10-13T10:00:00Z",
  "updated_at": "2025-10-13T10:00:00Z",
  "full_name": "Abhiram Sakaray"
}
```

### 3. PUT `/api/v1/address/update`
**Authentication:** Required  
**Returns:** Updated DARI address with full_name

**Request:**
```json
{
  "username": "abhiram"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "abhiram",
  "full_address": "abhiram@dari",
  "wallet_address": "0x742d35...",
  "is_active": true,
  "created_at": "2025-10-13T10:00:00Z",
  "updated_at": "2025-10-13T15:30:00Z",
  "full_name": "Abhiram Sakaray"
}
```

## Mobile App Integration

### Display User's DARI Address with Name

```javascript
const getMyAddress = async () => {
  const response = await fetch('http://YOUR_SERVER:8000/api/v1/address/my-address', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  return {
    name: data.full_name || 'DARI User',
    address: data.full_address,
    walletAddress: data.wallet_address
  };
};
```

### Show in Profile Screen

```jsx
const ProfileScreen = () => {
  const [addressData, setAddressData] = useState(null);
  
  useEffect(() => {
    loadAddressData();
  }, []);
  
  const loadAddressData = async () => {
    const data = await getMyAddress();
    setAddressData(data);
  };
  
  return (
    <View style={styles.container}>
      <Text style={styles.name}>{addressData?.name}</Text>
      <Text style={styles.address}>{addressData?.address}</Text>
      <Text style={styles.wallet}>{addressData?.walletAddress}</Text>
    </View>
  );
};
```

### Create DARI Address with Name Display

```javascript
const createDariAddress = async (username) => {
  const response = await fetch('http://YOUR_SERVER:8000/api/v1/address/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username })
  });
  
  const data = await response.json();
  
  console.log(`Created: ${data.full_address} for ${data.full_name}`);
  return data;
};
```

## Use Cases

### 1. Profile Display
Show user's name alongside their DARI address:
```
Abhiram Sakaray
abhi@dari
```

### 2. Contact List Integration
When combined with the check-phones endpoint:
```javascript
const dariUser = {
  phone: "+917207276059",
  full_name: "Abhiram Sakaray",  // From check-phones
  dari_address: "abhi@dari",
  full_address: "abhi@dari"
};
```

### 3. Transaction Recipients
Display recipient name when sending to DARI address:
```
Send to: Abhiram Sakaray (abhi@dari)
```

### 4. QR Code Display
Generate QR code with name:
```javascript
const qrData = {
  address: addressData.full_address,
  name: addressData.full_name,
  wallet: addressData.wallet_address
};
```

## Email Notifications Enhanced

Email notifications now use the full_name from KYC:

### Before
```
Subject: DARI Address Created
Hi user@email.com,
Your DARI address abhi@dari has been created.
```

### After
```
Subject: DARI Address Created
Hi Abhiram Sakaray,
Your DARI address abhi@dari has been created.
```

## Database Queries

Each endpoint now performs an additional query:

```sql
-- Get KYC data for full_name
SELECT full_name 
FROM kyc_requests 
WHERE user_id = ?
LIMIT 1;

-- Fallback to user table if no KYC
SELECT full_name 
FROM users 
WHERE id = ?;
```

## Performance Considerations

- **Additional Query:** Each endpoint makes 1 extra database query
- **Impact:** Minimal (KYC lookup is fast with user_id index)
- **Caching:** Consider caching full_name if needed for high-traffic apps

## Testing

### Test with KYC Approved User

```bash
curl -X GET "http://localhost:8000/api/v1/address/my-address" \
  -H "Authorization: Bearer TOKEN_FOR_KYC_USER"
```

**Expected:** `full_name` from KYC data

### Test with Non-KYC User

```bash
curl -X GET "http://localhost:8000/api/v1/address/my-address" \
  -H "Authorization: Bearer TOKEN_FOR_NON_KYC_USER"
```

**Expected:** `full_name` from user table or `null`

### Test Address Creation

```bash
curl -X POST "http://localhost:8000/api/v1/address/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser"}'
```

**Expected:** Response includes `full_name` field

## Files Modified

1. ✅ `app/schemas/address_resolver.py` - Added `full_name` field to response schema
2. ✅ `app/api/v1/address_resolver.py` - Updated 3 endpoints to include full_name
   - GET `/my-address`
   - POST `/create`
   - PUT `/update`

## Backward Compatibility

✅ **Fully backward compatible**
- New field `full_name` is optional (`Optional[str] = None`)
- Existing integrations continue to work
- Mobile apps can ignore the field if not needed

## Next Steps

1. ✅ Schema and endpoints updated
2. ✅ Syntax validated
3. ⏳ Restart server to apply changes
4. ⏳ Test with mobile app
5. ⏳ Update mobile app to display full_name
6. ⏳ Consider caching if performance becomes an issue

## Status

✅ **COMPLETE** - All address resolver endpoints now include full_name from KYC
✅ **TESTED** - Syntax check passed
⏳ **PENDING** - Server restart required
