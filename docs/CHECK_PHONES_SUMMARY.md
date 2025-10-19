# Check Phones Endpoint - Implementation Summary

## Date: October 13, 2025

## Overview
Created a new endpoint to check which phone numbers from a contact list are registered DARI users. This enables the mobile app to show which contacts can receive DARI payments.

## Endpoint

**POST** `/api/v1/users/check-phones`

## Request/Response

### Request
```json
{
  "phones": ["+917207276059", "+919876543210", "+911234567890"]
}
```

### Response
```json
{
  "dari_users": [
    {
      "phone": "+917207276059",
      "full_name": "Abhiram Sakaray",
      "dari_address": "abhi@dari",
      "full_address": "abhi@dari"
    }
  ]
}
```

## Features

✅ **Batch Processing** - Check multiple phone numbers in one request
✅ **User Information** - Returns full name and DARI address
✅ **Active Users Only** - Only returns users with `is_active = true`
✅ **LEFT JOIN** - Handles users without DARI addresses (returns null)
✅ **Authentication Required** - Prevents unauthorized contact discovery

## Implementation

### Files Created/Modified

1. **app/schemas/user.py** - Added 3 new schemas:
   - `CheckPhonesRequest` - Request body with list of phones
   - `DariUserInfo` - User information structure
   - `CheckPhonesResponse` - Response with dari_users list

2. **app/api/v1/users.py** - Added:
   - Import for `AddressResolver` model
   - Import for new schemas
   - `check_phones()` endpoint function

3. **docs/CHECK_PHONES_ENDPOINT.md** - Complete documentation

### Database Query

```python
select(User, AddressResolver)
  .outerjoin(AddressResolver, User.id == AddressResolver.user_id)
  .where(User.phone.in_(request.phones))
  .where(User.is_active == True)
```

## Use Cases

### 1. Contact List Integration
```javascript
const dariUsers = await checkDariContacts(['+917207276059', ...]);
// Show DARI badge for registered users
```

### 2. Quick Send
```javascript
// Use dari_address for quick payment
sendPayment(dariUser.dari_address, amount);
```

### 3. Invite Feature
```javascript
// Find non-DARI contacts to invite
const nonDariUsers = allContacts.filter(c => !dariPhones.includes(c.phone));
```

## Response Fields

| Field         | Type         | Description                          |
|--------------|--------------|--------------------------------------|
| phone        | string       | User's phone number                  |
| full_name    | string\|null | User's full name (from KYC/profile) |
| dari_address | string\|null | Short DARI address (e.g., "abhi@dari") |
| full_address | string\|null | Full DARI address (same as dari_address) |

**Note:** Fields may be `null` if:
- User hasn't set up DARI address → `dari_address` and `full_address` are null
- User hasn't completed KYC → `full_name` is null

## Mobile App Integration

### Step 1: Get Device Contacts
```javascript
import Contacts from 'react-native-contacts';

const getDeviceContacts = async () => {
  const contacts = await Contacts.getAll();
  return contacts.map(c => c.phoneNumbers[0]?.number).filter(Boolean);
};
```

### Step 2: Check DARI Users
```javascript
const phoneNumbers = await getDeviceContacts();
const dariUsers = await checkDariContacts(phoneNumbers);
```

### Step 3: Display in UI
```jsx
<FlatList
  data={dariUsers}
  renderItem={({ item }) => (
    <ContactCard
      name={item.full_name}
      address={item.dari_address}
      phone={item.phone}
      onSend={() => handleSend(item)}
    />
  )}
/>
```

## Security

✅ **Authentication Required** - Protects against unauthorized access
✅ **Only Returns Requested Phones** - No data leakage
✅ **Active Users Only** - Banned/inactive users excluded
✅ **No Sensitive Data** - Only returns public profile info

**Recommendation:** Add rate limiting in production to prevent abuse.

## Testing

### Using Swagger UI
1. Go to `http://localhost:8000/docs`
2. Authorize with JWT token
3. Find POST `/api/v1/users/check-phones` under "Users" section
4. Try it with test phones

### Using cURL
```bash
curl -X POST "http://localhost:8000/api/v1/users/check-phones" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phones": ["+917207276059"]}'
```

## Performance

### Recommended Batch Size
- **Optimal:** 50-100 numbers per request
- **Maximum:** No hard limit, but consider splitting large contact lists

### Caching Strategy
```javascript
// Cache results for 5 minutes
const CACHE_DURATION = 5 * 60 * 1000;
```

## Status

✅ **COMPLETE** - Endpoint implemented and documented
✅ **TESTED** - Syntax check passed
⏳ **PENDING** - Server restart required
⏳ **NEXT** - Mobile app integration

## Deployment

**Restart Server:**
```bash
# Restart your uvicorn server to load the new endpoint
Ctrl+C (stop server)
uvicorn app.main:main --reload --host 0.0.0.0 --port 8000
```

## Files Changed

1. ✅ `app/schemas/user.py` - Added 3 new Pydantic models
2. ✅ `app/api/v1/users.py` - Added check_phones endpoint
3. ✅ `docs/CHECK_PHONES_ENDPOINT.md` - Complete documentation
4. ✅ `docs/CHECK_PHONES_SUMMARY.md` - This summary file
