# SendGrid Setup Guide

**Date:** October 19, 2025  
**Purpose:** Fix email sending on Render (SMTP ports blocked)  
**Solution:** Use SendGrid HTTP API (no SMTP ports needed)

## Why SendGrid?

### Problem
Render's free tier **blocks ALL SMTP ports**:
- Port 465 (SSL) - BLOCKED ❌
- Port 587 (TLS) - BLOCKED ❌  
- Port 25 (Plain) - BLOCKED ❌

### Solution
SendGrid uses **HTTP API** instead of SMTP:
- ✅ No SMTP ports needed
- ✅ Works on ALL cloud platforms
- ✅ FREE - 100 emails per day
- ✅ Better deliverability
- ✅ Email analytics included

## Step 1: Sign Up (2 minutes)

1. **Go to SendGrid:**
   - Visit: https://signup.sendgrid.com
   
2. **Create Account:**
   - Enter your email
   - Create password
   - Fill in basic info
   - Click "Create Account"

3. **Verify Email:**
   - Check your inbox
   - Click verification link
   - Complete setup

## Step 2: Get API Key (1 minute)

1. **Login to SendGrid Dashboard:**
   - https://app.sendgrid.com

2. **Navigate to API Keys:**
   - Click **Settings** (left sidebar)
   - Click **API Keys**

3. **Create API Key:**
   - Click **"Create API Key"** button
   - Name: `DARI Wallet Backend`
   - Permission: Select **"Full Access"**
   - Click **"Create & View"**

4. **Copy API Key:**
   - **IMPORTANT:** Copy the key immediately!
   - It starts with `SG.`
   - Example: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to see it again!

## Step 3: Add to Render (1 minute)

1. **Go to Render Dashboard:**
   - https://dashboard.render.com
   - Select `dariappbackend` service
   - Click **Environment** tab

2. **Add Environment Variables:**

   **Variable 1:**
   ```
   Key:   SENDGRID_API_KEY
   Value: SG.your_api_key_here
   ```

   **Variable 2:**
   ```
   Key:   USE_SENDGRID
   Value: true
   ```

   **Variable 3 (Keep existing):**
   ```
   Key:   FROM_EMAIL
   Value: info@dariorganization.com
   ```

   **Variable 4 (Keep existing):**
   ```
   Key:   OTP_EMAIL_ENABLED
   Value: true
   ```

3. **Save Changes:**
   - Click **"Save Changes"** (top right)
   - Render will auto-redeploy (~2-3 minutes)

## Step 4: Verify Sender Email (Optional but Recommended)

1. **Go to SendGrid Dashboard:**
   - Click **Settings** → **Sender Authentication**

2. **Verify Single Sender:**
   - Click **"Verify a Single Sender"**
   - Enter: `info@dariorganization.com`
   - Fill in your details
   - Click **"Create"**

3. **Check Email:**
   - SendGrid will send verification to `info@dariorganization.com`
   - Click the verification link
   - This improves deliverability

## Step 5: Test (2 minutes)

After Render redeploys:

```bash
POST https://dariappbackend.onrender.com/api/v1/auth/register/request-otp
{
  "email": "test@example.com",
  "phone": "+1234567890"
}
```

**Expected:**
- ✅ Response in 5-10 seconds (not 30+)
- ✅ Logs show: "📧 Attempting to send OTP via SendGrid..."
- ✅ Logs show: "✅ Email sent successfully via SendGrid"
- ✅ Email received in inbox

## Configuration Summary

### On Render (Environment Variables):
```bash
# SendGrid (NEW - REQUIRED)
SENDGRID_API_KEY=SG.your_api_key_here
USE_SENDGRID=true

# Email Settings (EXISTING)
FROM_EMAIL=info@dariorganization.com
OTP_EMAIL_ENABLED=true

# SMTP (OPTIONAL - Fallback for local development)
SMTP_HOST=smtp.zoho.in
SMTP_PORT=587
SMTP_USE_SSL=False
SMTP_USE_TLS=True
SMTP_USERNAME=info@dariorganization.com
SMTP_PASSWORD=2gzU0PPaY10H
```

## How It Works

### Email Sending Flow:
1. **Try SendGrid First:**
   - If `USE_SENDGRID=true` and API key exists
   - Sends via HTTP API
   - No SMTP ports needed ✅

2. **Fallback to SMTP:**
   - If SendGrid fails or not configured
   - Tries SMTP (Zoho)
   - Works locally, blocked on Render ❌

### On Render (Production):
```
Request OTP → Try SendGrid → Success ✅ → Email sent in 5 seconds
```

### Locally (Development):
```
Request OTP → Try SendGrid → (No API key) → Use SMTP → Success ✅
```

## SendGrid Free Tier Limits

| Feature | Free Tier |
|---------|-----------|
| Emails per day | 100 |
| Emails per month | 3,000 |
| Sender verification | Required |
| Email analytics | Yes |
| Templates | Yes |
| Cost | $0 |

**Note:** 100 emails/day is MORE than enough for:
- Testing and development
- Small user base
- OTP codes
- Notifications

## Troubleshooting

### Issue 1: "SendGrid API key not configured"
**Cause:** `SENDGRID_API_KEY` not set on Render  
**Fix:** Add the environment variable and redeploy

### Issue 2: "403 Forbidden" from SendGrid
**Cause:** API key invalid or no permissions  
**Fix:**
- Verify API key is correct
- Recreate API key with "Full Access"
- Check SendGrid account is active

### Issue 3: "Sender verification required"
**Cause:** SendGrid requires sender verification  
**Fix:**
- Go to Sender Authentication
- Verify `info@dariorganization.com`
- Check email for verification link

### Issue 4: Still using SMTP
**Cause:** `USE_SENDGRID` not set to `true`  
**Fix:** Add `USE_SENDGRID=true` to Render

### Issue 5: SendGrid fails, SMTP also fails
**Cause:** Both services having issues  
**Logs:** Will show both attempts  
**Fix:**
- Check SendGrid dashboard for issues
- Verify API key is correct
- Check SendGrid account status

## Monitoring

### Check SendGrid Stats:
1. Go to SendGrid Dashboard
2. Click **"Dashboard"** (left sidebar)
3. See real-time email stats:
   - Emails sent
   - Delivered
   - Bounced
   - Opened (if tracking enabled)

### Check Render Logs:
```bash
# Look for:
✅ Email sent successfully via SendGrid
# Or:
⚠️  SendGrid failed, falling back to SMTP...
```

## Upgrade Options

### If you exceed 100 emails/day:

**SendGrid Essentials:**
- $19.95/month
- 50,000 emails/month
- No daily limit

**SendGrid Pro:**
- $89.95/month
- 100,000 emails/month
- Advanced features

**Or upgrade Render:**
- $7+/month
- SMTP ports unblocked
- Use Zoho SMTP again

## Next Steps

1. ✅ Sign up for SendGrid
2. ✅ Get API key
3. ✅ Add to Render environment variables
4. ✅ Wait for redeploy (~3 minutes)
5. ✅ Test registration endpoint
6. ✅ Verify email received
7. 🎉 Email working!

## Success Criteria

- ✅ Registration completes in 5-10 seconds
- ✅ No "Timeout sending email OTP" errors
- ✅ Logs show "Email sent successfully via SendGrid"
- ✅ OTP emails received in inbox
- ✅ Beautiful formatted HTML emails
- ✅ All endpoints working

---

**Status:** Ready to deploy! Just need SendGrid API key.

**Support:** If you need help, SendGrid has excellent documentation:
https://docs.sendgrid.com/for-developers/sending-email/api-getting-started
