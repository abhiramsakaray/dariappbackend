# 🧪 Expo Push Notifications - API Testing Guide

Quick reference for testing the complete push notification system.

---

## 🎯 Quick Tests

### 1. Test Auto-Registration on Login

```bash
# Step 1: Request OTP
POST http://localhost:8000/api/v1/auth/login/request-otp
Content-Type: application/json

{
  "email": "your_email@example.com"
}

# Step 2: Complete login WITH push token (auto-registration)
POST http://localhost:8000/api/v1/auth/login/verify-otp
Content-Type: application/json

{
  "email": "your_email@example.com",
  "otp": "123456",
  "expo_push_token": "ExponentPushToken[test_token_12345]",
  "device_type": "ios",
  "device_name": "Test iPhone 13"
}

# ✅ Expected: Login successful + push token auto-registered
```

### 2. Verify Token Registration

```bash
GET http://localhost:8000/api/v1/push/tokens
Authorization: Bearer YOUR_ACCESS_TOKEN

# ✅ Expected: See your registered token with is_active: true
```

### 3. Send Test Notification

```bash
POST http://localhost:8000/api/v1/push/test
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "title": "Test Notification 🔔",
  "body": "Hello from DARI backend!",
  "data": {
    "test": true
  }
}

# ✅ Expected: {"success": true, "message": "Test notifications sent"}
```

### 4. Test Transaction Notification (Automatic)

```bash
# Send a transaction (notifications sent automatically after success)
POST http://localhost:8000/api/v1/transactions/send
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "to_address": "recipient@dari",
  "amount": "10",
  "token": "USDC",
  "pin": "1234"
}

# ✅ Expected: Transaction succeeds + both sender and receiver get notifications
# Check server logs for:
#   ✓ Payment notification sent to user [recipient_id]
#   ✓ Payment notification sent to user [sender_id]
```

### 5. Test Manual Token Registration

```bash
POST http://localhost:8000/api/v1/push/register
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "expo_push_token": "ExponentPushToken[another_device_token]",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21"
}

# ✅ Expected: Token registered or updated
```

### 6. Unregister Token

```bash
DELETE http://localhost:8000/api/v1/push/unregister
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "expo_push_token": "ExponentPushToken[test_token_12345]"
}

# ✅ Expected: {"success": true, "message": "Push token unregistered"}
```

### 7. Delete Specific Token

```bash
DELETE http://localhost:8000/api/v1/push/tokens/1
Authorization: Bearer YOUR_ACCESS_TOKEN

# ✅ Expected: Token deleted permanently
```

---

## 🔍 What to Check in Server Logs

### Auto-Registration on Login
```
✅ Auto-registered push token for user 123
```

### Transaction Notifications
```
✓ Payment notification sent to user 456 (recipient)
✓ Payment notification sent to user 123 (sender)
```

### KYC Notifications (after approval/rejection)
```
✓ KYC notification sent to user 123
```

### Errors (Non-Blocking)
```
⚠️ Failed to auto-register push token: [error details]
⚠️ Expo notification error: [error details]
```

---

## 📱 Testing with Expo Go App

### 1. Get Your Expo Push Token

In your Expo app:
```javascript
import * as Notifications from 'expo-notifications';

const token = await Notifications.getExpoPushTokenAsync({
  projectId: 'your-project-id',
});
console.log('Expo Push Token:', token.data);
```

### 2. Use Real Token in Tests

Replace `ExponentPushToken[test_token_12345]` with your real token from step 1.

### 3. Send Test Notification

```bash
POST http://localhost:8000/api/v1/push/test
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "title": "Real Test 🔔",
  "body": "You should see this on your device!"
}
```

---

## 🧩 Postman Collection

Import this collection for easy testing:

```json
{
  "info": {
    "name": "DARI - Expo Push Notifications",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Login with Auto-Registration",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"{{user_email}}\",\n  \"otp\": \"{{otp}}\",\n  \"expo_push_token\": \"{{expo_token}}\",\n  \"device_type\": \"ios\",\n  \"device_name\": \"Test iPhone\"\n}"
        },
        "url": "{{base_url}}/api/v1/auth/login/verify-otp"
      }
    },
    {
      "name": "2. Get My Tokens",
      "request": {
        "method": "GET",
        "header": [{"key": "Authorization", "value": "Bearer {{access_token}}"}],
        "url": "{{base_url}}/api/v1/push/tokens"
      }
    },
    {
      "name": "3. Send Test Notification",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Authorization", "value": "Bearer {{access_token}}"},
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"title\": \"Test Notification\",\n  \"body\": \"Hello from backend!\"\n}"
        },
        "url": "{{base_url}}/api/v1/push/test"
      }
    },
    {
      "name": "4. Manual Register Token",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Authorization", "value": "Bearer {{access_token}}"},
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"expo_push_token\": \"{{expo_token}}\",\n  \"device_type\": \"ios\",\n  \"device_name\": \"Test Device\"\n}"
        },
        "url": "{{base_url}}/api/v1/push/register"
      }
    },
    {
      "name": "5. Unregister Token",
      "request": {
        "method": "DELETE",
        "header": [
          {"key": "Authorization", "value": "Bearer {{access_token}}"},
          {"key": "Content-Type", "value": "application/json"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"expo_push_token\": \"{{expo_token}}\"\n}"
        },
        "url": "{{base_url}}/api/v1/push/unregister"
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:8000"},
    {"key": "user_email", "value": "test@example.com"},
    {"key": "otp", "value": "123456"},
    {"key": "expo_token", "value": "ExponentPushToken[xxxxx]"},
    {"key": "access_token", "value": ""}
  ]
}
```

---

## ✅ Expected Responses

### Login with Auto-Registration
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {...},
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  }
}
```

### Get Tokens
```json
{
  "success": true,
  "data": {
    "tokens": [
      {
        "id": 1,
        "expo_push_token": "ExponentPushToken[xxx]",
        "device_type": "ios",
        "device_name": "Test iPhone",
        "is_active": true,
        "created_at": "2025-10-19T10:00:00Z",
        "last_used_at": "2025-10-19T10:05:00Z"
      }
    ],
    "total": 1
  }
}
```

### Test Notification
```json
{
  "success": true,
  "message": "Test notifications sent to 1 device(s)",
  "data": {
    "sent_to": 1,
    "failed": 0
  }
}
```

### Register Token
```json
{
  "success": true,
  "message": "Push token registered successfully",
  "data": {
    "token_id": 1,
    "expo_push_token": "ExponentPushToken[xxx]",
    "is_active": true
  }
}
```

---

## 🐛 Troubleshooting

### "Token registration failed"
- Check token format: must start with `ExponentPushToken[` or `ExpoPushToken[`
- Verify authentication token is valid
- Check device_type is "ios" or "android"

### "No active push tokens found"
- User hasn't registered any tokens yet
- All tokens were unregistered
- Tokens were automatically deactivated due to errors

### "Test notification sent but not received"
- Check if token is real (from actual Expo app)
- Verify device has internet connection
- Check Expo project ID is configured
- Test notifications don't work with fake tokens

### "Transaction successful but no notification"
- Check server logs for notification errors
- Verify recipient has registered push tokens
- Check notification_helpers.py for errors
- Notifications are non-blocking (won't fail transaction)

---

## 📊 Database Queries

### Check all registered tokens
```sql
SELECT * FROM push_tokens WHERE is_active = TRUE;
```

### Check user's tokens
```sql
SELECT * FROM push_tokens WHERE user_id = 123;
```

### Check token usage
```sql
SELECT 
  user_id,
  COUNT(*) as device_count,
  MAX(last_used_at) as last_activity
FROM push_tokens 
WHERE is_active = TRUE
GROUP BY user_id;
```

### Find inactive tokens
```sql
SELECT * FROM push_tokens WHERE is_active = FALSE;
```

---

## 🎯 Integration Checklist

- [ ] Login endpoint returns access_token
- [ ] Auto-registration works (check with GET /push/tokens)
- [ ] Test notification reaches device
- [ ] Transaction notifications sent automatically
- [ ] KYC notifications sent on approve/reject
- [ ] Multi-device support works
- [ ] Unregister on logout works
- [ ] Invalid tokens auto-deactivated

---

## 📞 Quick Reference

| Feature | Endpoint | Method |
|---------|----------|--------|
| Auto-Register | `/auth/login/verify-otp` | POST |
| Manual Register | `/push/register` | POST |
| List Tokens | `/push/tokens` | GET |
| Unregister | `/push/unregister` | DELETE |
| Delete Token | `/push/tokens/{id}` | DELETE |
| Test Notification | `/push/test` | POST |

---

**Ready to test! 🚀**
