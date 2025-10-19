# Render Environment Variables Setup

**Date:** October 19, 2025  
**Status:** ⚠️ Action Required  
**Priority:** Critical

## Current Issue

Email OTP is timing out after 30 seconds:
```
Timeout sending email OTP: timed out
```

This indicates the SMTP server is not reachable or credentials are incorrect.

## Required Environment Variables

You need to add these environment variables in your Render dashboard:

### 1. Navigate to Render Dashboard
1. Go to https://dashboard.render.com
2. Select your service: `dariappbackend`
3. Click on **Environment** tab
4. Add the following variables:

### 2. Database Configuration (Should Already Be Set)
```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

### 3. SMTP/Email Configuration (REQUIRED - Currently Missing or Wrong)

#### Option A: Using Zoho Mail (Recommended)
```bash
SMTP_HOST=smtp.zoho.com
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=your-email@yourdomain.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@dariwallet.com
OTP_EMAIL_ENABLED=true
```

#### Option B: Using Gmail
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
OTP_EMAIL_ENABLED=true
```

**⚠️ Important for Gmail:**
- You MUST use an App Password, not your regular Gmail password
- Generate App Password: https://myaccount.google.com/apppasswords
- Enable 2-factor authentication first

#### Option C: Using SendGrid (Production Recommended)
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@dariwallet.com
OTP_EMAIL_ENABLED=true
```

### 4. Redis Configuration
```bash
REDIS_URL=redis://username:password@host:port
```

### 5. JWT/Security Configuration
```bash
SECRET_KEY=your-super-secret-key-min-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-min-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 6. Blockchain Configuration
```bash
# Ethereum/Polygon RPC
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR-API-KEY
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR-API-KEY

# Contract Addresses
USDT_CONTRACT_ADDRESS=0x...
USDC_CONTRACT_ADDRESS=0x...

# Relayer Configuration
RELAYER_PRIVATE_KEY=0x...
GAS_PRICE_MULTIPLIER=1.2
```

### 7. Twilio (SMS OTP - Optional)
```bash
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
OTP_SMS_ENABLED=true
```

### 8. Application Settings
```bash
ENVIRONMENT=production
DEBUG=false
APP_NAME=DARI Wallet
FRONTEND_URL=https://your-frontend-domain.com
```

## Testing Email Configuration

### Test 1: Check SMTP Credentials Locally

Create a test script `test_smtp.py`:

```python
import smtplib
from email.mime.text import MIMEText

# Replace with your credentials
SMTP_HOST = "smtp.zoho.com"  # or smtp.gmail.com
SMTP_PORT = 465
SMTP_USERNAME = "your-email@domain.com"
SMTP_PASSWORD = "your-password"

try:
    print(f"Connecting to {SMTP_HOST}:{SMTP_PORT}...")
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
    print("✅ Connected!")
    
    print("Logging in...")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("✅ Login successful!")
    
    print("Sending test email...")
    msg = MIMEText("Test email from DARI Wallet Backend")
    msg['Subject'] = "SMTP Test"
    msg['From'] = SMTP_USERNAME
    msg['To'] = SMTP_USERNAME
    
    server.sendmail(SMTP_USERNAME, SMTP_USERNAME, msg.as_string())
    print("✅ Email sent successfully!")
    
    server.quit()
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

Run: `python test_smtp.py`

### Test 2: Check Render Logs

After adding environment variables:

1. Go to Render dashboard → Logs
2. Look for:
   ```
   ✅ Email sent successfully to user@example.com
   ```
3. If you see errors, check:
   - SMTP credentials are correct
   - Port is correct (465 for SSL, 587 for TLS)
   - No firewall blocking Render's IP

## Temporary Workaround: Disable Email OTP

If you want to test other features while fixing email:

1. Add to Render environment variables:
   ```bash
   OTP_EMAIL_ENABLED=false
   OTP_SMS_ENABLED=false
   ```

2. Users will only be able to register/login without OTP verification

**⚠️ Warning:** This is insecure for production!

## Alternative: Use Phone OTP Only

If Twilio is configured:

```bash
OTP_EMAIL_ENABLED=false
OTP_SMS_ENABLED=true
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
```

## Verifying the Fix

### Step 1: Check Environment Variables
```bash
# On Render dashboard, verify all SMTP_* variables are set
```

### Step 2: Trigger Manual Redeploy
1. Go to Render dashboard
2. Click **Manual Deploy** → **Deploy latest commit**
3. Wait for deployment to complete

### Step 3: Test Registration
```bash
curl -X POST https://dariappbackend.onrender.com/api/v1/auth/register/request-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "phone": "+1234567890"
  }'
```

Expected response:
```json
{
  "message": "OTP sent successfully"
}
```

### Step 4: Check Logs
Should see:
```
Email sent successfully to test@example.com
```

Not:
```
Timeout sending email OTP: timed out
```

## Common Issues & Solutions

### Issue 1: "Authentication failed"
**Cause:** Wrong username/password  
**Solution:** 
- For Gmail: Use App Password, not regular password
- For Zoho: Use account password
- Verify credentials are correct

### Issue 2: "Connection refused"
**Cause:** Wrong port or host  
**Solution:**
- Gmail: Use port 587 with TLS
- Zoho: Use port 465 with SSL
- Verify SMTP_HOST is correct

### Issue 3: "Timeout" (Current Issue)
**Cause:** SMTP server unreachable or variables not set  
**Solution:**
- Verify environment variables are set on Render
- Check if Render's IP is blocked by email provider
- Test SMTP credentials locally first

### Issue 4: Render doesn't recognize variables
**Cause:** Didn't redeploy after adding variables  
**Solution:**
- Click "Manual Deploy" after adding variables
- Variables only apply on next deployment

## Security Best Practices

### 1. Never Commit Credentials
```bash
# ❌ DON'T DO THIS
SMTP_PASSWORD=my-password-123

# ✅ DO THIS
# Set in Render dashboard only
```

### 2. Use App Passwords
- Gmail: Generate app-specific password
- Zoho: Can use account password (less secure)
- SendGrid: Use API key

### 3. Restrict Permissions
- Email account should only have "Send Email" permission
- Use separate email account for transactional emails
- Monitor for suspicious activity

## Production Recommendations

For production deployment, use a dedicated email service:

1. **SendGrid** (Recommended)
   - Free tier: 100 emails/day
   - Better deliverability
   - Detailed analytics

2. **Amazon SES**
   - Very cheap ($0.10 per 1000 emails)
   - High deliverability
   - Requires AWS setup

3. **Mailgun**
   - Free tier: 5000 emails/month
   - Easy setup
   - Good documentation

## Next Steps

1. ✅ Check if SMTP variables are set on Render
2. ⏳ Add missing SMTP environment variables
3. ⏳ Test SMTP credentials locally (optional)
4. ⏳ Trigger manual redeploy on Render
5. ⏳ Test registration endpoint again
6. ⏳ Verify email is received

## Status Checklist

- [ ] SMTP_HOST set on Render
- [ ] SMTP_PORT set on Render
- [ ] SMTP_USERNAME set on Render
- [ ] SMTP_PASSWORD set on Render
- [ ] FROM_EMAIL set on Render
- [ ] SMTP credentials tested locally
- [ ] Manual redeploy triggered
- [ ] Registration endpoint tested
- [ ] Email received successfully

---

**Current Status:** Email timeout indicates SMTP configuration is missing or incorrect on Render. Add the environment variables above and redeploy.
