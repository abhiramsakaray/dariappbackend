# FCM Setup: V1 API vs Legacy API

## Quick Comparison

| Feature | V1 API (Service Account) | Legacy API (Server Key) |
|---------|-------------------------|------------------------|
| **Status** | ✅ Recommended | ⚠️ Deprecated (June 2024) |
| **Security** | ✅ More secure (OAuth2) | ⚠️ Less secure (static key) |
| **Setup Complexity** | Medium | Easy |
| **Authentication** | Service Account JSON | Server Key string |
| **Future Support** | Yes | No (deprecated) |
| **What You Have** | ✅ Enabled | ❌ Disabled |

## Your Current Firebase Setup

Based on your screenshot:
```
Firebase Cloud Messaging API (V1) ✅ Enabled
Cloud Messaging API (Legacy)      ❌ Disabled
```

**Recommendation:** Use **V1 API with Service Account**

---

## Setup Instructions for YOUR Project

### Step 1: Get Service Account Key

1. **Go to:** https://console.firebase.google.com/
2. **Select your project:** `dari-wallet-v2` (or your project name)
3. **Click:** ⚙️ Settings → **Project settings**
4. **Tab:** **Service accounts**
5. **Click:** **"Generate new private key"** button
6. **Download:** `dari-wallet-v2-firebase-adminsdk-xxxxx.json`
7. **Save to:** `D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json`

### Step 2: Configure .env

Add these lines to your `.env` file:

```env
# Firebase Cloud Messaging V1 API
FCM_PROJECT_ID=dari-wallet-v2
FCM_SERVICE_ACCOUNT_PATH=D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json
```

Replace `dari-wallet-v2` with your actual Firebase project ID (you can see it in the Firebase Console).

### Step 3: Install Dependencies

```bash
pip install google-auth
```

### Step 4: Add to .gitignore

**IMPORTANT:** Never commit the service account file to git!

Add to `.gitignore`:
```gitignore
# Firebase
firebase-service-account.json
*-firebase-adminsdk-*.json
```

### Step 5: Restart Server

```bash
# Stop server (Ctrl+C)
# Start server
uvicorn app.main:app --reload
```

You should see:
```
✓ FCM V1 API configured (Service Account)
```

---

## Alternative: Quick Test with Legacy API

If you want to quickly test before setting up V1 API:

### 1. Enable Legacy API in Firebase

1. Go to Firebase Console → Your Project
2. Settings → Cloud Messaging
3. **Enable "Cloud Messaging API (Legacy)"**
4. Copy the **Server key**

### 2. Add to .env

```env
FCM_SERVER_KEY=AAAAxxxxxxx:APA91bH...
```

### 3. Restart Server

You'll see:
```
⚠️  FCM Legacy API configured (Server Key) - Consider migrating to V1
```

**Note:** This is for testing only. Legacy API is deprecated.

---

## Troubleshooting

### "FCM not configured"
**Check:**
- [ ] `.env` file has the variables
- [ ] File paths are correct (absolute paths recommended)
- [ ] Server was restarted after adding variables

### "google-auth library not installed"
**Fix:**
```bash
pip install google-auth
```

### "Service account file not found"
**Fix:**
- Check the path in `FCM_SERVICE_ACCOUNT_PATH`
- Use absolute path (not relative)
- Verify file exists: `dir "D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json"`

### "Failed to get FCM access token"
**Check:**
- Service account JSON file is valid
- Service account has correct permissions
- File is not corrupted

### "401 Unauthorized"
**Fix:**
- Regenerate service account key
- Check project ID matches your Firebase project
- Verify service account has "Firebase Cloud Messaging API Admin" role

---

## Production Deployment

### Environment Variables

**Option 1: Hosting Platform (Render, Heroku, etc.)**
```bash
# In your hosting dashboard, add:
FCM_PROJECT_ID=dari-wallet-v2
FCM_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
```

**Option 2: Direct Server**
```bash
# In /etc/environment or ~/.bashrc
export FCM_PROJECT_ID="dari-wallet-v2"
export FCM_SERVICE_ACCOUNT_PATH="/var/www/dari-backend/firebase-service-account.json"
```

### Secure the Service Account File

```bash
# Set proper permissions (Linux/Mac)
chmod 600 firebase-service-account.json
chown dari-user:dari-user firebase-service-account.json

# Windows
icacls firebase-service-account.json /grant "dari-user:R"
icacls firebase-service-account.json /inheritance:r
```

---

## Summary

**For your project, do this:**

1. ✅ Generate service account JSON from Firebase Console
2. ✅ Save to `firebase-service-account.json`
3. ✅ Add `FCM_PROJECT_ID` and `FCM_SERVICE_ACCOUNT_PATH` to `.env`
4. ✅ Run `pip install google-auth`
5. ✅ Add `*.json` to `.gitignore`
6. ✅ Restart server

**You'll get:**
- ✅ Modern V1 API (not deprecated)
- ✅ More secure authentication
- ✅ Future-proof implementation
- ✅ Production-ready setup

**Time needed:** 5 minutes
