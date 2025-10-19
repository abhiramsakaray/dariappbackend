# 🎉 Firebase V1 API Update - Complete

## What Changed

Your Firebase Console shows:
```
Firebase Cloud Messaging API (V1) ✅ Enabled  (Recommended)
Cloud Messaging API (Legacy)      ❌ Disabled (Deprecated)
```

I've updated the DARI backend to support **BOTH APIs**:

### ✅ V1 API (Your Current Setup) - **RECOMMENDED**
- Uses Service Account JSON file
- OAuth2 authentication
- Not deprecated
- More secure
- **This is what you should use**

### ⚠️ Legacy API (Fallback)
- Uses Server Key string
- Simple authentication  
- Deprecated June 2024
- Less secure
- Only for quick testing

---

## 🔄 What Was Updated

### Files Modified (3 files)

1. **`app/services/firebase_service.py`**
   - Added V1 API support with service account
   - Added OAuth2 token generation
   - Auto-detects which API to use
   - Falls back to Legacy if V1 not configured

2. **`app/core/config.py`**
   - Added `FCM_PROJECT_ID` setting
   - Added `FCM_SERVICE_ACCOUNT_PATH` setting  
   - Kept `FCM_SERVER_KEY` for backward compatibility

3. **`requirements.txt`**
   - Added `google-auth==2.27.0` for V1 API

### Files Created (2 docs)

1. **`docs/FCM_V1_SETUP.md`** - Quick comparison & your specific setup steps
2. **`docs/FCM_SETUP_GUIDE.md`** - Updated with both API methods

---

## 🚀 Setup for V1 API (5 minutes)

### Step 1: Get Service Account Key from Firebase

1. Go to: https://console.firebase.google.com/
2. Select your project
3. **Settings** (⚙️) → **Project settings** → **Service accounts** tab
4. Click **"Generate new private key"**
5. Download the JSON file (e.g., `dari-wallet-v2-firebase-adminsdk-xxxxx.json`)
6. Save it as: `firebase-service-account.json` in your project root

### Step 2: Configure .env

Add to your `.env` file:

```env
# Firebase V1 API (Recommended)
FCM_PROJECT_ID=dari-wallet-v2
FCM_SERVICE_ACCOUNT_PATH=D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json

# Note: Replace 'dari-wallet-v2' with your actual Firebase project ID
# Find it in Firebase Console → Project settings → General tab
```

### Step 3: Install google-auth

```bash
pip install google-auth
```

### Step 4: Add to .gitignore

**IMPORTANT:** Never commit service account to git!

Add to `.gitignore`:
```gitignore
# Firebase
firebase-service-account.json
*-firebase-adminsdk-*.json
```

### Step 5: Restart Server

```bash
uvicorn app.main:app --reload
```

You should see:
```
✓ FCM V1 API configured (Service Account)
```

---

## ✅ Verification

### On Server Start

Look for one of these messages:

**Success (V1 API):**
```
✓ FCM V1 API configured (Service Account)
```

**Success (Legacy API):**
```
⚠️  FCM Legacy API configured (Server Key) - Consider migrating to V1
```

**Not Configured:**
```
ℹ️  FCM not configured - Push notifications disabled
```

### When Sending Notification

**V1 API:**
```
✓ Push notification sent (V1 API)
```

**Legacy API:**
```
✓ Push notification sent (Legacy API)
```

---

## 🔧 Configuration Options

### Option 1: V1 API (Recommended)

```env
FCM_PROJECT_ID=your-project-id
FCM_SERVICE_ACCOUNT_PATH=/path/to/firebase-service-account.json
```

**Pros:**
- ✅ Not deprecated
- ✅ More secure (OAuth2)
- ✅ Future-proof
- ✅ Works with your current Firebase setup

**Cons:**
- Requires service account JSON file
- Slightly more complex setup

### Option 2: Legacy API (For Testing Only)

```env
FCM_SERVER_KEY=AAAAxxxxxxx:APA91bH...
```

**Pros:**
- Simpler setup (just one string)
- Quick to test

**Cons:**
- ⚠️ Deprecated (stops working June 2024)
- ⚠️ Less secure
- ⚠️ Not recommended for production

### Option 3: Both (Automatic Fallback)

```env
# V1 API (will use this if available)
FCM_PROJECT_ID=your-project-id
FCM_SERVICE_ACCOUNT_PATH=/path/to/service-account.json

# Legacy API (fallback if V1 fails)
FCM_SERVER_KEY=AAAAxxxxxxx:APA91bH...
```

---

## 📋 How the Auto-Detection Works

```python
# Backend automatically chooses:

if FCM_PROJECT_ID and FCM_SERVICE_ACCOUNT_PATH:
    → Use V1 API (Service Account)
    
elif FCM_SERVER_KEY:
    → Use Legacy API (Server Key)
    
else:
    → Push notifications disabled
```

---

## 🐛 Troubleshooting

### "google-auth library not installed"

**Fix:**
```bash
pip install google-auth
```

### "Failed to get FCM access token"

**Check:**
- Service account JSON file exists at specified path
- File path is absolute (not relative)
- JSON file is valid (not corrupted)
- Service account has correct permissions

**Test file path:**
```bash
# Windows
dir "D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json"

# Linux/Mac
ls -l /path/to/firebase-service-account.json
```

### "FCM V1 failed: 401 - Unauthorized"

**Possible causes:**
1. Wrong project ID
2. Service account doesn't have permission
3. JSON file is from different project

**Fix:**
1. Verify `FCM_PROJECT_ID` matches your Firebase project
2. Regenerate service account key
3. Check service account has "Firebase Cloud Messaging Admin" role

### "FCM V1 failed: 404 - Not Found"

**Cause:** Wrong project ID in `FCM_PROJECT_ID`

**Fix:**
- Go to Firebase Console → Project settings
- Copy the exact **Project ID** (not project name)
- Update `.env` file

---

## 📦 Dependencies

### New Dependency Added

```txt
google-auth==2.27.0
```

**Install command:**
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install google-auth
```

---

## 🔐 Security Best Practices

### Protect Service Account File

```bash
# Linux/Mac - Restrict permissions
chmod 600 firebase-service-account.json
chown app-user:app-user firebase-service-account.json

# Windows - Grant read-only to specific user
icacls firebase-service-account.json /grant "AppUser:R"
icacls firebase-service-account.json /inheritance:r
```

### Never Commit to Git

Add to `.gitignore`:
```gitignore
# Firebase service account
firebase-service-account.json
*-firebase-adminsdk-*.json
*.json
!package.json
!tsconfig.json
```

### Environment Variables for Production

**Render/Heroku/Cloud:**
```bash
FCM_PROJECT_ID=dari-wallet-v2
FCM_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
```

Upload JSON file separately through dashboard or CI/CD.

---

## 📊 Comparison: Before vs After

### Before (Initial Implementation)
```
✗ Only supported Legacy API (Server Key)
✗ Would break when Legacy API deprecated
✗ Less secure authentication
```

### After (Current Implementation)
```
✓ Supports V1 API (Service Account)
✓ Supports Legacy API (fallback)
✓ Auto-detects which API to use
✓ Future-proof (won't break when Legacy deprecated)
✓ More secure (OAuth2 tokens)
```

---

## 🎯 Next Steps

1. **Get Service Account JSON** from Firebase Console
2. **Save to project folder** as `firebase-service-account.json`
3. **Update .env** with `FCM_PROJECT_ID` and `FCM_SERVICE_ACCOUNT_PATH`
4. **Install google-auth**: `pip install google-auth`
5. **Add to .gitignore**: `firebase-service-account.json`
6. **Restart server** and verify logs show "V1 API configured"
7. **Test notification** by making a transaction

---

## 📚 Documentation

- **Quick Setup:** `docs/FCM_V1_SETUP.md` ← **START HERE**
- **Detailed Guide:** `docs/FCM_SETUP_GUIDE.md`
- **Mobile Integration:** `docs/MOBILE_INTEGRATION_GUIDE.md`
- **Full Features:** `docs/NOTIFICATION_ENHANCEMENTS.md`

---

## ✨ Summary

**What you need to do:**
1. Download service account JSON from Firebase Console
2. Add 2 lines to `.env` file
3. Run `pip install google-auth`
4. Restart server

**What you get:**
- ✅ Modern V1 API support
- ✅ Works with your current Firebase setup
- ✅ Backward compatible with Legacy API
- ✅ Future-proof implementation
- ✅ More secure authentication

**Time needed:** 5 minutes

---

**Status:** ✅ **Ready to Use**  
**Updated:** October 19, 2025  
**Supports:** Firebase V1 API + Legacy API
