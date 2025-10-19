# Firebase Cloud Messaging (FCM) Setup Guide

## 🚀 Quick Start (Recommended: V1 API with Service Account)

Firebase has **two APIs**:
- ✅ **V1 API** (Recommended) - Uses Service Account (more secure, not deprecated)
- ⚠️ **Legacy API** - Uses Server Key (simpler but deprecated June 2024)

I'll show you both methods. **Use V1 API for new projects.**

---

## Method 1: V1 API with Service Account (Recommended)

### 1. Go to Firebase Console

1. **Visit Firebase Console**
   - Go to: https://console.firebase.google.com/
   - Sign in with your Google account

2. **Select or Create Project**
   - If you don't have a project: Click **"Add project"**
   - If you have a project: Select it from the list
   - Note your **Project ID** (e.g., `dari-wallet-v2`)

### 2. Generate Service Account Key

1. **Go to Project Settings**
   - Click the **gear icon** (⚙️) next to "Project Overview"
   - Select **"Project settings"**

2. **Navigate to Service Accounts**
   - Click the **"Service accounts"** tab
   - You'll see your service account email (e.g., `firebase-adminsdk-xxxxx@dari-wallet-v2.iam.gserviceaccount.com`)

3. **Generate New Private Key**
   - Click **"Generate new private key"** button
   - Confirm by clicking **"Generate key"**
   - A JSON file will download (e.g., `dari-wallet-v2-firebase-adminsdk-xxxxx.json`)
   
4. **Save the JSON File**
   - Move it to a secure location in your project
   - Example: `D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json`
   - ⚠️ **NEVER commit this file to git!** Add to `.gitignore`

### 3. Configure Backend (V1 API)

**Add to your `.env` file:**
```env
# FCM V1 API (Recommended)
FCM_PROJECT_ID=dari-wallet-v2
FCM_SERVICE_ACCOUNT_PATH=D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json
```

**Install required package:**
```bash
pip install google-auth
```

**Add to `.gitignore`:**
```gitignore
# Firebase service account
firebase-service-account.json
*.json
```

---

## Method 2: Legacy API with Server Key (Simpler but Deprecated)

⚠️ **Note:** This method is deprecated and will stop working after June 2024. Use only if you need quick testing.

### 1. Enable Legacy API

1. **Go to Firebase Console** → Your Project
2. **Project Settings** → **Cloud Messaging** tab
3. **Enable Cloud Messaging API (Legacy)** if disabled

### 2. Get Server Key

- Under "Cloud Messaging API (Legacy)" section
- Copy the **Server key**
   
Example format:
```
AAAAxxxxxxx:APA91bHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Configure Backend (Legacy API)

**Add to your `.env` file:**
```env
# FCM Legacy API (Deprecated - for testing only)
FCM_SERVER_KEY=AAAAxxxxxxx:APA91bHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🔧 Installation & Setup

### 1. Install Dependencies
```bash
pip install google-auth
```

### 2. Restart Your Server
```bash
# Stop current server
Ctrl+C

# Start server again
uvicorn app.main:app --reload
```

## ✅ Verify Setup

### Check Logs on Server Start

**V1 API (Service Account):**
```
✓ FCM V1 API configured (Service Account)
```

**Legacy API (Server Key):**
```
⚠️  FCM Legacy API configured (Server Key) - Consider migrating to V1
```

**Not Configured:**
```
ℹ️  FCM not configured - Push notifications disabled
```

### Check Logs When Notification Sent

**Success:**
```
✓ Push notification sent (V1 API)
```
or
```
✓ Push notification sent (Legacy API)
```

**Failure:**
```
✗ FCM V1 failed: 401 - Unauthorized
```

### Test FCM Manually

```bash
curl -X POST https://fcm.googleapis.com/fcm/send \
  -H "Authorization: Bearer YOUR_FCM_SERVER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test_device_token",
    "notification": {
      "title": "Test Notification",
      "body": "This is a test from DARI backend"
    }
  }'
```

Expected response:
```json
{
  "multicast_id": 123456789,
  "success": 1,
  "failure": 0,
  "canonical_ids": 0,
  "results": [{"message_id": "0:1234567890%abc123"}]
}
```

## Mobile App Setup

### For React Native with Expo

1. **Install dependencies**
   ```bash
   npx expo install expo-notifications expo-device
   ```

2. **Request permission and get token**
   ```javascript
   import * as Notifications from 'expo-notifications';
   
   async function registerForPushNotifications() {
     const { status } = await Notifications.requestPermissionsAsync();
     
     if (status === 'granted') {
       const token = (await Notifications.getExpoPushTokenAsync()).data;
       
       // Send to DARI backend
       await fetch('YOUR_API_URL/api/v1/users/fcm-token', {
         method: 'POST',
         headers: {
           'Authorization': `Bearer ${yourAccessToken}`,
           'Content-Type': 'application/json'
         },
         body: JSON.stringify({ fcm_device_token: token })
       });
     }
   }
   ```

3. **Call on app start**
   ```javascript
   useEffect(() => {
     registerForPushNotifications();
   }, []);
   ```

### For React Native with Firebase

1. **Install dependencies**
   ```bash
   npm install @react-native-firebase/app
   npm install @react-native-firebase/messaging
   ```

2. **Get FCM token**
   ```javascript
   import messaging from '@react-native-firebase/messaging';
   
   async function getToken() {
     const fcmToken = await messaging().getToken();
     
     // Send to DARI backend
     await fetch('YOUR_API_URL/api/v1/users/fcm-token', {
       method: 'POST',
       headers: {
         'Authorization': `Bearer ${yourAccessToken}`,
         'Content-Type': 'application/json'
       },
       body: JSON.stringify({ fcm_device_token: fcmToken })
     });
   }
   ```

## Environment Variables Summary

Add these to your `.env` file:

```env
# Firebase Cloud Messaging
FCM_SERVER_KEY=YOUR_FCM_SERVER_KEY_HERE

# Example (don't use this - get your own from Firebase Console):
# FCM_SERVER_KEY=AAAAxxxxxxx:APA91bHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Troubleshooting

### "FCM_SERVER_KEY not configured"
- Check your `.env` file has the `FCM_SERVER_KEY` variable
- Restart your server after adding it
- Verify the key format (starts with "AAAA")

### "Push notification failed"
- Verify your FCM server key is correct
- Check if the device token is valid
- Ensure Firebase Cloud Messaging API is enabled in your project

### "Notification not appearing on device"
- Check device notification permissions
- Verify the mobile app sent the device token to backend
- Check backend logs for push notification status

## Alternative: OneSignal (Easier Setup)

If you want an easier alternative to Firebase:

1. **Sign up at OneSignal**: https://onesignal.com/
2. **Get REST API Key** from Settings
3. **Update backend** to use OneSignal instead of FCM

Benefits:
- Easier setup (no Firebase project needed)
- Built-in analytics
- Multi-platform support (iOS, Android, Web)
- Free tier available

## Need Help?

- Firebase FCM Docs: https://firebase.google.com/docs/cloud-messaging
- Expo Push Notifications: https://docs.expo.dev/push-notifications/
- OneSignal Docs: https://documentation.onesignal.com/
