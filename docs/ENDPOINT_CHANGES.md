# Quick Reference: Endpoint Changes

## Removed Endpoints (Do Not Use)

### Authentication - Deprecated/Removed
❌ `POST /api/v1/auth/register` → Use `/register/request-otp` + `/register/complete`  
❌ `POST /api/v1/auth/login` → Use `/login/request-otp` + `/login/verify-otp`  
❌ `POST /api/v1/auth/request-otp` → Use specific endpoints  
❌ `POST /api/v1/auth/verify-otp` → Use specific endpoints  
❌ `POST /api/v1/auth/change-password` → Use `/forgot-password/reset`  
❌ `POST /api/v1/auth/universal/login/request-otp` → Use `/login/request-otp`  
❌ `POST /api/v1/auth/universal/login/verify-otp` → Use `/login/verify-otp`  
❌ `POST /api/v1/auth/universal/forgot-password/request-otp` → Use `/forgot-password/request-otp`  
❌ `POST /api/v1/auth/universal/forgot-password/reset` → Use `/forgot-password/reset`  
❌ `POST /api/v1/auth/admin/login` → Removed (admin access)

### Other - Removed
❌ `GET /api/v1/address/admin/all` → Removed (admin access)  
❌ `GET /api/v1/users/stats` → Removed (admin access)  
❌ `GET /api/v1/notifications/{notification_id}` → Use list endpoint

---

## Current Endpoints (Use These)

### Authentication (11 endpoints)
✅ `POST /api/v1/auth/register/request-otp` - Request OTP for registration  
✅ `POST /api/v1/auth/register/complete` - Complete registration with OTP  
✅ `POST /api/v1/auth/login/request-otp` - Request OTP for login  
✅ `POST /api/v1/auth/login/verify-otp` - Complete login with OTP  
✅ `POST /api/v1/auth/refresh` - Refresh access token  
✅ `GET /api/v1/auth/me` - Get current user info  
✅ `POST /api/v1/auth/logout` - Logout user  
✅ `POST /api/v1/auth/set-pin` - Set/update PIN  
✅ `POST /api/v1/auth/verify-pin` - Verify PIN  
✅ `POST /api/v1/auth/forgot-password/request-otp` - Request password reset OTP  
✅ `POST /api/v1/auth/forgot-password/reset` - Reset password with OTP

### KYC (5 endpoints)
✅ `POST /api/v1/kyc/upload-document` - Upload ID document  
✅ `POST /api/v1/kyc/upload-selfie` - Upload selfie  
✅ `POST /api/v1/kyc/submit` - Submit KYC for review  
✅ `GET /api/v1/kyc/status` - Get KYC status  
✅ `GET /api/v1/kyc/files-status` - Get uploaded files status

### Wallet (3 endpoints)
✅ `POST /api/v1/wallets/create` - Create new wallet  
✅ `GET /api/v1/wallets/` - Get wallet info  
✅ `GET /api/v1/wallets/balance` - Get wallet balance

### Transactions (4 endpoints)
✅ `POST /api/v1/transactions/estimate-gas` - Estimate transaction fee  
✅ `POST /api/v1/transactions/send` - Send transaction  
✅ `GET /api/v1/transactions/` - Get transaction history  
✅ `GET /api/v1/transactions/{id}` - Get transaction details

### Address/Username (6 endpoints)
✅ `POST /api/v1/address/create` - Create username  
✅ `GET /api/v1/address/my-address` - Get my username/address  
✅ `PUT /api/v1/address/update` - Update username  
✅ `POST /api/v1/address/resolve` - Resolve address/username  
✅ `GET /api/v1/address/check-username/{username}` - Check availability  
✅ `DELETE /api/v1/address/delete` - Delete username

### Tokens (2 endpoints)
✅ `GET /api/v1/tokens/` - Get supported tokens  
✅ `GET /api/v1/tokens/prices` - Get token prices

### Notifications (5 endpoints)
✅ `GET /api/v1/notifications/` - Get all notifications  
✅ `GET /api/v1/notifications/unread/count` - Get unread count  
✅ `PATCH /api/v1/notifications/{id}/read` - Mark as read  
✅ `PATCH /api/v1/notifications/read-all` - Mark all as read  
✅ `DELETE /api/v1/notifications/{id}` - Delete notification

### User Profile (3 endpoints)
✅ `GET /api/v1/users/profile` - Get user profile  
✅ `PUT /api/v1/users/profile` - Update profile  
✅ `GET /api/v1/users/pin-status` - Check if PIN is set

---

## Response Format Changes

### Before (Inconsistent)
```json
{
  "access_token": "...",
  "user": { ... }
}
```

### After (Consistent - Matches Spec)
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": { ... },
    "tokens": {
      "access_token": "...",
      "refresh_token": "...",
      "expires_in": 900
    }
  }
}
```

---

## Migration Guide for Frontend/Mobile

### Registration Flow
**Old**:
```
POST /auth/register
```

**New**:
```
1. POST /auth/register/request-otp
2. POST /auth/register/complete
```

### Login Flow
**Old**:
```
POST /auth/login
```

**New**:
```
1. POST /auth/login/request-otp
2. POST /auth/login/verify-otp
```

### Password Reset
**Old**:
```
POST /auth/change-password
```

**New**:
```
1. POST /auth/forgot-password/request-otp
2. POST /auth/forgot-password/reset
```

---

## Key Improvements

1. **Consistent Responses**: All endpoints return `{success, message, data}` format
2. **Better Security**: All sensitive operations require OTP
3. **Cleaner API**: No deprecated or redundant endpoints
4. **Specification Compliant**: 100% matches BACKEND_API_SPECIFICATION.md
5. **No Admin Access**: All admin endpoints removed

---

**Last Updated**: October 11, 2025  
**Total Endpoints**: 42
