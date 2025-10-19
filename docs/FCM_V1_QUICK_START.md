# 🎯 Quick Start: Firebase V1 API (5 Minutes)

## Your Firebase Console Shows

```
✅ Firebase Cloud Messaging API (V1) - Enabled
❌ Cloud Messaging API (Legacy) - Disabled
```

**→ You need to use V1 API (Service Account method)**

---

## 📋 Step-by-Step Guide

### 1️⃣ Download Service Account Key (2 min)

1. Open: https://console.firebase.google.com/
2. Select your project
3. Click ⚙️ (Settings) → **Project settings**
4. Go to **"Service accounts"** tab
5. Click **"Generate new private key"** button
6. Click **"Generate key"** in popup
7. JSON file downloads automatically
8. Rename it to: `firebase-service-account.json`
9. Move to: `D:\Projects\DARI MVP EXPO\DARI V2\`

**File location should be:**
```
D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json
```

---

### 2️⃣ Add to .env File (1 min)

Open your `.env` file and add:

```env
# Firebase Cloud Messaging V1 API
FCM_PROJECT_ID=YOUR_PROJECT_ID_HERE
FCM_SERVICE_ACCOUNT_PATH=D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json
```

**How to find your Project ID:**
- In Firebase Console → Project settings → General tab
- Look for "Project ID" (NOT "Project name")
- Example: `dari-wallet-v2` or `dari-mobile-app-12345`

**Example .env:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://...

# Firebase Cloud Messaging V1 API
FCM_PROJECT_ID=dari-wallet-v2
FCM_SERVICE_ACCOUNT_PATH=D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json

# Other settings...
SECRET_KEY=your_secret_key
```

---

### 3️⃣ Install Dependency (1 min)

Open terminal in your project folder:

```bash
pip install google-auth
```

---

### 4️⃣ Add to .gitignore (30 sec)

Open `.gitignore` file and add:

```gitignore
# Firebase service account - DO NOT COMMIT!
firebase-service-account.json
*-firebase-adminsdk-*.json
```

---

### 5️⃣ Restart Server (30 sec)

```bash
# Stop current server (Ctrl+C if running)

# Start server
uvicorn app.main:app --reload
```

---

## ✅ Verify It Works

Look at the terminal when server starts. You should see:

**SUCCESS:**
```
✓ FCM V1 API configured (Service Account)
```

**If you see this instead:**
```
ℹ️  FCM not configured - Push notifications disabled
```

**→ Double-check:**
- [ ] `.env` file has both `FCM_PROJECT_ID` and `FCM_SERVICE_ACCOUNT_PATH`
- [ ] File path is correct and file exists
- [ ] Project ID matches your Firebase project
- [ ] Restart the server after adding to `.env`

---

## 🧪 Test Push Notification

### From Mobile App:

1. Make sure mobile app registered FCM token
2. Send a transaction
3. You should receive instant push notification

### Check Backend Logs:

When notification is sent, you'll see:
```
✓ Push notification sent (V1 API)
```

Or if there's an error:
```
✗ FCM V1 failed: 401 - Unauthorized
```

---

## 🐛 Common Issues & Fixes

### Issue: "google-auth library not installed"

**Fix:**
```bash
pip install google-auth
```

### Issue: "Service account file not found"

**Fix:**
- Check file exists: `dir "D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json"`
- Use absolute path, not relative
- Check for typos in file name

### Issue: "Failed to get FCM access token"

**Fix:**
1. Verify JSON file is valid (open in notepad, should be valid JSON)
2. Regenerate key from Firebase Console
3. Check file permissions

### Issue: "401 Unauthorized"

**Fix:**
1. Wrong project ID → Get correct one from Firebase Console
2. Service account has no permission → Regenerate key
3. JSON file from wrong project → Download again

### Issue: "404 Not Found"

**Fix:**
- `FCM_PROJECT_ID` is wrong
- Check Firebase Console → Settings → General → Project ID
- Update `.env` with exact project ID

---

## 📁 Final File Structure

```
D:\Projects\DARI MVP EXPO\DARI V2\
├── app/
├── docs/
├── .env                              ← Added FCM settings here
├── .gitignore                        ← Added firebase-service-account.json
├── firebase-service-account.json     ← Downloaded from Firebase ⚠️ DON'T COMMIT
└── requirements.txt                  ← Updated with google-auth
```

---

## 🎯 Checklist

- [ ] Downloaded service account JSON from Firebase
- [ ] Renamed to `firebase-service-account.json`
- [ ] Saved in project root folder
- [ ] Added `FCM_PROJECT_ID` to `.env`
- [ ] Added `FCM_SERVICE_ACCOUNT_PATH` to `.env`
- [ ] Verified project ID matches Firebase Console
- [ ] Ran `pip install google-auth`
- [ ] Added `firebase-service-account.json` to `.gitignore`
- [ ] Restarted server
- [ ] Saw "✓ FCM V1 API configured" in logs
- [ ] Tested by sending transaction
- [ ] Received push notification on mobile

---

## 🚀 You're Done!

Your backend now supports:
- ✅ Modern Firebase V1 API
- ✅ OAuth2 authentication
- ✅ Future-proof (not deprecated)
- ✅ Secure push notifications

**Next:** Update your mobile app to register FCM tokens
- See: `docs/MOBILE_INTEGRATION_GUIDE.md`

---

## 💡 Pro Tips

1. **Backup the JSON file** - Save copy in secure location
2. **Never commit to git** - It contains sensitive credentials
3. **Use environment variables in production** - Don't hardcode paths
4. **Regenerate if compromised** - Easy to create new key in Firebase
5. **Monitor logs** - Check for "✓ Push notification sent" messages

---

## 📞 Need Help?

**Docs:**
- This guide: `docs/FCM_V1_QUICK_START.md`
- Detailed: `docs/FCM_V1_SETUP.md`
- Full guide: `docs/FCM_SETUP_GUIDE.md`

**Common commands:**
```bash
# Check if file exists
dir "D:\Projects\DARI MVP EXPO\DARI V2\firebase-service-account.json"

# Install dependency
pip install google-auth

# Restart server
uvicorn app.main:app --reload

# Check logs
# Look for "✓ FCM V1 API configured"
```

---

**Status:** ✅ Ready to Use  
**Time:** 5 minutes  
**Difficulty:** Easy
