# Notification System Enhancements

## Overview
This document describes the improvements made to the DARI notification system to provide better user experience with:
1. **Removed emojis** from notification titles
2. **User-preferred currency display** (not USDC by default)
3. **Real-time push notifications** via Firebase Cloud Messaging (FCM)

## Changes Made

### 1. Emoji Removal ✓

**Files Modified:**
- `app/services/notification_service.py`

**Changes:**
- Removed all emoji characters from notification titles
- Changed titles to clean text:
  - ~~"💸 Transaction Sent"~~ → "Transaction Sent"
  - ~~"💰 Payment Received"~~ → "Payment Received"
  - ~~"✅ Transaction Confirmed"~~ → "Transaction Confirmed"
  - ~~"❌ Transaction Failed"~~ → "Transaction Failed"

### 2. User Currency Preference ✓

**Problem:** Notifications were showing USDC amounts even when users preferred other currencies (INR, EUR, etc.)

**Solution:** Display amounts in user's `default_currency` as the primary value

**Implementation:**
```python
# Show user's preferred currency first
if user_currency != "USD" and amount_in_user_currency:
    primary_amount_display = f"{amount_in_user_currency} {user_currency}"
    secondary_amount_display = f"{amount} {token_symbol}"  # Optional
else:
    primary_amount_display = f"{amount} {token_symbol}"
```

**Example Notifications:**

For user with `default_currency = "INR"`:
```
You received 8,275.50 INR from abhi@dari (100 USDC)
```

For user with `default_currency = "USD"`:
```
You received 100 USDC from abhi@dari
```

### 3. Firebase Cloud Messaging (FCM) Integration ✓

**New Files Created:**
- `app/services/firebase_service.py` - FCM integration service
- `alembic/versions/add_fcm_device_token.py` - Database migration

**Files Modified:**
- `app/models/user.py` - Added `fcm_device_token` field
- `app/services/notification_service.py` - Integrated FCM push notifications
- `app/api/v1/users.py` - Added FCM token management endpoints
- `app/core/config.py` - Added `FCM_SERVER_KEY` configuration

**Database Changes:**
```sql
ALTER TABLE users ADD COLUMN fcm_device_token VARCHAR(500);
```

## API Endpoints

### Register/Update FCM Device Token
```http
POST /api/v1/users/fcm-token
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "fcm_device_token": "firebase_device_token_string_from_mobile_app"
}
```

**Response:**
```json
{
  "success": true,
  "message": "FCM device token updated successfully"
}
```

### Remove FCM Device Token (Logout)
```http
DELETE /api/v1/users/fcm-token
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "message": "FCM device token removed successfully"
}
```

## Firebase Setup

### 1. Get FCM Server Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (or create new one)
3. Go to **Project Settings** (gear icon)
4. Navigate to **Cloud Messaging** tab
5. Copy the **Server key** (under Cloud Messaging API)

### 2. Configure Backend

Add to your `.env` file:
```env
FCM_SERVER_KEY=your_firebase_server_key_here
```

### 3. Mobile App Integration

#### React Native (Expo)
```bash
npm install expo-notifications expo-device
```

```javascript
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

// Request permissions and get token
async function registerForPushNotifications() {
  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      alert('Failed to get push token for push notification!');
      return;
    }
    
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    
    // Send to backend
    await fetch('https://api.dari.com/api/v1/users/fcm-token', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ fcm_device_token: token })
    });
    
    return token;
  }
}

// Handle notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});
```

#### React Native (Firebase)
```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
```

```javascript
import messaging from '@react-native-firebase/messaging';

async function requestUserPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    const token = await messaging().getToken();
    
    // Send to backend
    await fetch('https://api.dari.com/api/v1/users/fcm-token', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ fcm_device_token: token })
    });
  }
}
```

## Notification Flow

### Complete Flow Diagram
```
Transaction Created
       ↓
[Blockchain Confirmation]
       ↓
Backend creates notification
       ↓
    ┌──────┴──────┐
    ↓             ↓
In-App DB    Push (FCM)
    ↓             ↓
Mobile App   Mobile App
 (Pull)       (Real-time)
```

### Notification Types

1. **Transaction Sent**
   - Title: "Transaction Sent"
   - Body: "You sent {amount} {currency} to {recipient}"
   - Sent to: Sender
   
2. **Payment Received**
   - Title: "Payment Received"
   - Body: "You received {amount} {currency} from {sender}"
   - Sent to: Receiver
   
3. **Transaction Confirmed**
   - Title: "Transaction Confirmed"
   - Body: "Your transaction of {amount} {currency} has been confirmed"
   - Sent to: Both sender and receiver

4. **Transaction Failed**
   - Title: "Transaction Failed"
   - Body: "Your transaction of {amount} {currency} has failed"
   - Sent to: Sender

### Push Notification Payload

```json
{
  "to": "fcm_device_token",
  "notification": {
    "title": "Payment Received",
    "body": "You received 8,275.50 INR from abhi@dari",
    "sound": "default",
    "badge": 1
  },
  "data": {
    "type": "transaction",
    "notification_type": "received",
    "amount": "8275.50",
    "currency": "INR",
    "from_to": "abhi@dari",
    "transaction_id": "123"
  },
  "priority": "high"
}
```

## Testing

### 1. Run Database Migration
```bash
alembic upgrade head
```

### 2. Test FCM Token Registration
```bash
curl -X POST http://localhost:8000/api/v1/users/fcm-token \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fcm_device_token": "test_token_123"}'
```

### 3. Test Notification Creation
```bash
# Make a test transaction
curl -X POST http://localhost:8000/api/v1/transactions/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_identifier": "recipient@dari",
    "amount": 100,
    "token_id": 1
  }'
```

### 4. Check Notification Response
```bash
# Get notifications
curl http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:
```json
{
  "notifications": [
    {
      "id": 1,
      "type": "transaction_sent",
      "title": "Transaction Sent",
      "message": "You sent 8,275.50 INR to recipient@dari (100 USDC)",
      "extra_data": {
        "amount": "100",
        "token_symbol": "USDC",
        "amount_in_user_currency": "8275.50",
        "user_currency": "INR"
      },
      "created_at": "2025-10-15T00:00:00Z"
    }
  ]
}
```

## Troubleshooting

### No Push Notifications Received

1. **Check FCM Server Key**
   ```bash
   # Verify env variable is set
   echo $FCM_SERVER_KEY
   ```

2. **Check Device Token Registration**
   ```sql
   SELECT id, email, fcm_device_token FROM users WHERE id = YOUR_USER_ID;
   ```

3. **Check Backend Logs**
   ```
   ✓ Push notification sent to user 123
   ```
   or
   ```
   ⚠️  FCM_SERVER_KEY not configured - skipping push notification
   ```

4. **Test FCM Manually**
   ```bash
   curl -X POST https://fcm.googleapis.com/fcm/send \
     -H "Authorization: Bearer YOUR_FCM_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "to": "device_token",
       "notification": {
         "title": "Test",
         "body": "Test notification"
       }
     }'
   ```

### Currency Not Showing Correctly

1. **Check User Default Currency**
   ```sql
   SELECT id, email, default_currency FROM users WHERE id = YOUR_USER_ID;
   ```

2. **Update User Currency**
   ```bash
   curl -X PUT http://localhost:8000/api/v1/users/profile \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"default_currency": "INR"}'
   ```

3. **Verify Currency Conversion Service**
   - Check if `currency_service` is working
   - Verify exchange rates are being fetched

## Security Considerations

1. **FCM Server Key**: Keep this secret! Never expose in client-side code
2. **Device Token Validation**: Backend validates tokens before sending
3. **Rate Limiting**: FCM has rate limits - handle appropriately
4. **Token Expiry**: Tokens may expire - mobile app should refresh periodically

## Performance

- **Push notifications**: Near real-time (< 1 second)
- **In-app notifications**: Instant (database write)
- **Email notifications**: 2-5 seconds (asynchronous)

## Future Enhancements

1. **Notification Preferences**: Allow users to enable/disable specific notification types
2. **Multi-Device Support**: Store multiple FCM tokens per user
3. **Rich Notifications**: Add images, action buttons
4. **Notification History**: Sync read status across devices
5. **Sound Customization**: Custom notification sounds per type

## Migration Checklist

- [x] Remove emojis from notification titles
- [x] Implement user currency preference display
- [x] Add FCM device token field to database
- [x] Create Firebase service for push notifications
- [x] Add FCM token management endpoints
- [x] Integrate FCM into notification service
- [x] Add configuration for FCM server key
- [x] Create database migration
- [ ] Deploy and test on production
- [ ] Update mobile app to register FCM tokens
- [ ] Monitor FCM delivery rates

## Documentation Links

- [Firebase Cloud Messaging Documentation](https://firebase.google.com/docs/cloud-messaging)
- [Expo Push Notifications](https://docs.expo.dev/push-notifications/overview/)
- [React Native Firebase](https://rnfirebase.io/)
