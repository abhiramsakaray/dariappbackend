# Check Phones Endpoint

## Overview
Added a new endpoint to check which phone numbers from a contact list are registered DARI users. This is useful for the mobile app to show which contacts can receive payments through DARI.

## Endpoint Details

### POST `/api/v1/users/check-phones`

**Authentication Required:** Yes (Bearer token)

**Description:** Check which phone numbers from the provided list are registered and active DARI users. Returns user information including full name and DARI address for each registered user.

## Request Format

```json
{
  "phones": [
    "+917207276059",
    "+919876543210",
    "+911234567890"
  ]
}
```

**Request Body:**
- `phones` (array of strings, required): List of phone numbers to check. Must include at least one phone number.

## Response Format

### Success Response (200 OK)

```json
{
  "dari_users": [
    {
      "phone": "+917207276059",
      "full_name": "Abhiram Sakaray",
      "dari_address": "abhi@dari",
      "full_address": "abhi@dari"
    },
    {
      "phone": "+919876543210",
      "full_name": "John Doe",
      "dari_address": "john@dari",
      "full_address": "john@dari"
    }
  ]
}
```

**Response Fields:**
- `dari_users` (array): List of registered DARI users found
  - `phone` (string): The phone number
  - `full_name` (string|null): User's full name from KYC/profile
  - `dari_address` (string|null): Short DARI address (e.g., "abhi@dari")
  - `full_address` (string|null): Full DARI address (same as dari_address)

**Notes:**
- Only returns users who are registered AND active (`is_active = true`)
- If a phone number is not registered, it won't appear in the response
- If a user hasn't set up their DARI address yet, `dari_address` and `full_address` will be `null`
- `full_name` may be `null` if the user hasn't completed KYC or set their name

## Error Responses

### 401 Unauthorized - Invalid/Missing Token
```json
{
  "detail": "Could not validate credentials"
}
```

### 422 Validation Error - Invalid Request
```json
{
  "detail": [
    {
      "loc": ["body", "phones"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Usage Examples

### 1. React Native - Check Contacts

```javascript
const checkDariContacts = async (phoneNumbers) => {
  try {
    const response = await fetch('http://YOUR_SERVER:8000/api/v1/users/check-phones', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        phones: phoneNumbers
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to check contacts');
    }
    
    const data = await response.json();
    return data.dari_users;
  } catch (error) {
    console.error('Error checking contacts:', error);
    return [];
  }
};

// Usage
const contactPhones = ['+917207276059', '+919876543210', '+911234567890'];
const dariUsers = await checkDariContacts(contactPhones);

console.log(`Found ${dariUsers.length} DARI users in contacts`);
dariUsers.forEach(user => {
  console.log(`${user.full_name} (${user.phone}) - ${user.dari_address}`);
});
```

### 2. Display DARI Contacts in Mobile App

```jsx
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, Image } from 'react-native';

const DariContactsScreen = () => {
  const [dariUsers, setDariUsers] = useState([]);
  
  useEffect(() => {
    loadDariContacts();
  }, []);
  
  const loadDariContacts = async () => {
    // Get phone numbers from device contacts
    const deviceContacts = await getDeviceContacts(); // Your implementation
    const phoneNumbers = deviceContacts.map(c => c.phoneNumber);
    
    // Check which are DARI users
    const users = await checkDariContacts(phoneNumbers);
    setDariUsers(users);
  };
  
  const renderDariUser = ({ item }) => (
    <View style={styles.userCard}>
      <Image 
        source={{ uri: `https://ui-avatars.com/api/?name=${item.full_name}` }}
        style={styles.avatar}
      />
      <View style={styles.userInfo}>
        <Text style={styles.name}>{item.full_name || 'DARI User'}</Text>
        <Text style={styles.address}>{item.dari_address || item.phone}</Text>
      </View>
      <TouchableOpacity 
        style={styles.sendButton}
        onPress={() => navigateToSend(item)}
      >
        <Text style={styles.sendButtonText}>Send</Text>
      </TouchableOpacity>
    </View>
  );
  
  return (
    <View style={styles.container}>
      <Text style={styles.header}>
        DARI Contacts ({dariUsers.length})
      </Text>
      <FlatList
        data={dariUsers}
        keyExtractor={item => item.phone}
        renderItem={renderDariUser}
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            No DARI users found in your contacts
          </Text>
        }
      />
    </View>
  );
};
```

### 3. Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/users/check-phones" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phones": ["+917207276059", "+919876543210"]
  }'
```

## Use Cases

### 1. Contact List Integration
Show which contacts can receive DARI payments:
- Display DARI badge/icon next to registered users
- Enable quick send button for DARI users
- Show DARI address for easy sending

### 2. Quick Send Feature
Allow users to quickly send to contacts:
```javascript
const sendToContact = async (dariUser, amount) => {
  // Use their dari_address for sending
  await sendTransaction({
    recipient: dariUser.dari_address || dariUser.phone,
    amount: amount
  });
};
```

### 3. Invite Non-Users
Identify which contacts are not DARI users:
```javascript
const getNonDariUsers = (allContacts, dariUsers) => {
  const dariPhones = dariUsers.map(u => u.phone);
  return allContacts.filter(c => !dariPhones.includes(c.phoneNumber));
};

// Show "Invite to DARI" button for non-users
```

## Performance Considerations

### Batch Processing
- The endpoint accepts multiple phone numbers in one request
- More efficient than checking each phone individually
- Recommended batch size: 50-100 numbers per request

### Caching Strategy
```javascript
// Cache results for a short period
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
let cachedResults = null;
let cacheTimestamp = 0;

const checkDariContactsWithCache = async (phones) => {
  const now = Date.now();
  
  if (cachedResults && (now - cacheTimestamp) < CACHE_DURATION) {
    // Filter cached results for requested phones
    return cachedResults.filter(u => phones.includes(u.phone));
  }
  
  // Fetch fresh data
  const users = await checkDariContacts(phones);
  cachedResults = users;
  cacheTimestamp = now;
  
  return users;
};
```

## Security Considerations

1. **Authentication Required**: Prevents unauthorized contact discovery
2. **Rate Limiting**: Consider implementing rate limits to prevent abuse
3. **Privacy**: Only returns phone numbers that were sent in the request
4. **Active Users Only**: Only returns users with `is_active = true`

## Database Query

The endpoint performs an efficient JOIN query:

```sql
SELECT users.*, address_resolvers.*
FROM users
LEFT JOIN address_resolvers ON users.id = address_resolvers.user_id
WHERE users.phone IN ('+917207276059', '+919876543210', ...)
  AND users.is_active = true;
```

## Testing

### Test Data
```json
{
  "phones": [
    "+917207276059",  // Registered user
    "+919999999999",  // Not registered
    "+911234567890"   // Registered user
  ]
}
```

### Expected Response
```json
{
  "dari_users": [
    {
      "phone": "+917207276059",
      "full_name": "Abhiram Sakaray",
      "dari_address": "abhi@dari",
      "full_address": "abhi@dari"
    },
    {
      "phone": "+911234567890",
      "full_name": "Test User",
      "dari_address": "test@dari",
      "full_address": "test@dari"
    }
  ]
}
```

Note: `+919999999999` is not in the response because it's not registered.

## Implementation Details

### File Locations
- **Endpoint**: `app/api/v1/users.py` - `check_phones()` function
- **Request Schema**: `app/schemas/user.py` - `CheckPhonesRequest`
- **Response Schema**: `app/schemas/user.py` - `CheckPhonesResponse`, `DariUserInfo`

### Database Tables Used
- `users` - User account information
- `address_resolvers` - DARI address mappings

## Next Steps

1. ✅ Endpoint created and tested for syntax
2. ⏳ Test with real contact data
3. ⏳ Integrate into mobile app contact screen
4. ⏳ Add contact permission handling in mobile app
5. ⏳ Implement caching strategy for performance
6. ⏳ Consider adding rate limiting for production
