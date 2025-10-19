# Backend Refactoring Analysis
## DARI V2 - API Specification Alignment

**Date**: October 11, 2025  
**Purpose**: Identify changes needed to align backend with API specification (user-only endpoints)

---

## 🎯 Overview

The backend needs to be refactored to:
1. **Remove ALL admin endpoints** - No admin functionality
2. **Remove admin authentication** - No admin login system
3. **Keep only user-facing endpoints** - Align with API specification
4. **Ensure all endpoints match the specification exactly**

---

## ❌ ENDPOINTS TO REMOVE

### 1. Admin Router (app/api/v1/admin.py)
**Action**: DELETE entire file and remove from main.py

**Endpoints to Remove** (98 admin endpoints):
- `/api/v1/admin/users` - User management
- `/api/v1/admin/users/search` - User search
- `/api/v1/admin/users/{user_id}/details` - User details
- `/api/v1/admin/users/balances/summary` - Balance summary
- `/api/v1/admin/users/{user_id}/activate` - Activate user
- `/api/v1/admin/users/{user_id}/deactivate` - Deactivate user
- `/api/v1/admin/notifications/broadcast` - Broadcast notifications
- `/api/v1/admin/notifications/stats` - Notification stats
- `/api/v1/admin/notifications/history` - Notification history
- `/api/v1/admin/notifications/templates` - Notification templates
- `/api/v1/admin/transactions/monitor` - Transaction monitoring
- `/api/v1/admin/transactions/{transaction_id}/details` - Transaction details
- `/api/v1/admin/transactions/debug` - Debug transactions
- `/api/v1/admin/transactions/all` - All transactions
- `/api/v1/admin/kyc/pending` - Pending KYC
- `/api/v1/admin/kyc/{kyc_id}/approve` - Approve KYC
- `/api/v1/admin/kyc/{kyc_id}/reject` - Reject KYC
- `/api/v1/admin/sub-admins/create` - Create sub-admin
- `/api/v1/admin/sub-admins` - List sub-admins
- `/api/v1/admin/permissions` - List permissions
- `/api/v1/admin/sub-admins/{user_id}` - Update sub-admin
- `/api/v1/admin/sub-admins/{user_id}/status` - Toggle sub-admin status
- `/api/v1/admin/sub-admins/{user_id}` - Delete sub-admin
- `/api/v1/admin/sub-admins/{user_id}/setup-password` - Setup sub-admin password
- `/api/v1/admin/sub-admins/{user_id}/change-password` - Change sub-admin password
- `/api/v1/admin/tasks/create` - Create admin task
- `/api/v1/admin/tasks` - Get admin tasks
- `/api/v1/admin/tasks/{task_id}/complete` - Complete task
- `/api/v1/admin/logs/admin` - Admin logs
- `/api/v1/admin/logs/users` - User activity logs
- `/api/v1/admin/logs/emails` - Email logs
- `/api/v1/admin/stats` - System stats
- `/api/v1/admin/system/health` - System health
- `/api/v1/admin/health/metrics` - Platform health metrics
- `/api/v1/admin/system/maintenance-mode` - Maintenance mode
- `/api/v1/admin/system/metrics` - System metrics
- And many more...

### 2. Admin Authentication Endpoints (app/api/v1/auth.py)
**Action**: REMOVE admin login endpoints

**Endpoints to Remove**:
- `POST /api/v1/auth/admin/login` - Admin login
- Any admin-specific authentication logic

### 3. Admin-Only Endpoints in Other Files
**Action**: REMOVE these endpoints

**In address_resolver.py**:
- `GET /api/v1/address/admin/all` - Get all address resolvers (admin only)

**In users.py**:
- `GET /api/v1/users/stats` - User stats (uses `get_admin_user` dependency)

---

## ✅ ENDPOINTS TO KEEP (Match API Specification)

### 1. Authentication Endpoints (/api/v1/auth)
**Status**: ✅ Already Implemented

- ✅ `POST /api/v1/auth/register/request-otp` - Request registration OTP
- ✅ `POST /api/v1/auth/register/complete` - Complete registration
- ✅ `POST /api/v1/auth/login/request-otp` - Request login OTP
- ✅ `POST /api/v1/auth/login/verify-otp` - Verify login OTP
- ✅ `POST /api/v1/auth/refresh` - Refresh token
- ✅ `GET /api/v1/auth/me` - Get current user
- ✅ `POST /api/v1/auth/logout` - Logout
- ✅ `POST /api/v1/auth/set-pin` - Set PIN
- ✅ `POST /api/v1/auth/verify-pin` - Verify PIN
- ✅ `POST /api/v1/auth/forgot-password/request-otp` - Forgot password OTP
- ✅ `POST /api/v1/auth/forgot-password/reset` - Reset password

**Notes**:
- Remove deprecated endpoints: `/api/v1/auth/register`, `/api/v1/auth/login`
- Remove duplicate forgot-password endpoints (lines 32-47, 101-116)
- Remove universal auth endpoints if not needed
- Remove admin login endpoint

### 2. KYC Endpoints (/api/v1/kyc)
**Status**: ✅ Already Implemented

- ✅ `POST /api/v1/kyc/upload-document` - Upload KYC document
- ✅ `POST /api/v1/kyc/upload-selfie` - Upload selfie
- ✅ `POST /api/v1/kyc/submit` - Submit KYC
- ✅ `GET /api/v1/kyc/status` - Get KYC status
- ✅ `GET /api/v1/kyc/files-status` - Get files status

### 3. Wallet Endpoints (/api/v1/wallets)
**Status**: ✅ Already Implemented

- ✅ `POST /api/v1/wallets/create` - Create wallet
- ✅ `GET /api/v1/wallets/` - Get wallet
- ✅ `GET /api/v1/wallets/balance` - Get balance

### 4. Transaction Endpoints (/api/v1/transactions)
**Status**: ✅ Already Implemented

- ✅ `POST /api/v1/transactions/estimate-gas` - Estimate gas fee
- ✅ `POST /api/v1/transactions/send` - Send transaction
- ✅ `GET /api/v1/transactions/` - Get transaction history
- ✅ `GET /api/v1/transactions/{transaction_id}` - Get transaction details

### 5. Address/Username Endpoints (/api/v1/address)
**Status**: ✅ Already Implemented (needs cleanup)

- ✅ `POST /api/v1/address/create` - Create username
- ✅ `GET /api/v1/address/my-address` - Get my address
- ✅ `PUT /api/v1/address/update` - Update username
- ✅ `POST /api/v1/address/resolve` - Resolve address
- ✅ `GET /api/v1/address/check-username/{username}` - Check username availability
- ✅ `DELETE /api/v1/address/delete` - Delete username

**To Remove**:
- ❌ `GET /api/v1/address/admin/all` - Admin endpoint

### 6. Token Endpoints (/api/v1/tokens)
**Status**: ✅ Already Implemented

- ✅ `GET /api/v1/tokens/` - Get supported tokens
- ✅ `GET /api/v1/tokens/prices` - Get token prices

### 7. Notification Endpoints (/api/v1/notifications)
**Status**: ✅ Already Implemented

- ✅ `GET /api/v1/notifications/` - Get notifications
- ✅ `GET /api/v1/notifications/unread/count` - Get unread count
- ✅ `PATCH /api/v1/notifications/{notification_id}/read` - Mark as read
- ✅ `PATCH /api/v1/notifications/read-all` - Mark all as read
- ✅ `DELETE /api/v1/notifications/{notification_id}` - Delete notification

### 8. User Profile Endpoints (/api/v1/users)
**Status**: ✅ Already Implemented (needs cleanup)

- ✅ `GET /api/v1/users/profile` - Get profile
- ✅ `PUT /api/v1/users/profile` - Update profile
- ✅ `GET /api/v1/users/pin-status` - Get PIN status

**To Remove**:
- ❌ `GET /api/v1/users/stats` - Admin endpoint

---

## 🔧 FILES TO MODIFY

### 1. app/main.py
**Changes**:
- ❌ Remove: `from app.api.v1 import admin`
- ❌ Remove: `app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])`
- ❌ Remove: `from app.core.security import create_initial_admin`
- ❌ Remove: `await create_initial_admin()` from lifespan

### 2. app/api/v1/admin.py
**Action**: DELETE entire file (93,641 bytes)

### 3. app/api/v1/auth.py
**Changes**:
- ❌ Remove: Duplicate forgot-password endpoints (lines 32-47, 101-116)
- ❌ Remove: Deprecated `/register` endpoint (line 237)
- ❌ Remove: Deprecated `/login` endpoint (line 268)
- ❌ Remove: Admin login endpoint `/admin/login` (line 880)
- ❌ Remove: Universal auth endpoints if not needed (lines 686-877)
- ✅ Keep: All user authentication endpoints

### 4. app/api/v1/address_resolver.py
**Changes**:
- ❌ Remove: Admin endpoint `/admin/all` (lines 221-232)
- ❌ Remove: Import `get_admin_user` (line 6)

### 5. app/api/v1/users.py
**Changes**:
- ❌ Remove: `/stats` endpoint (lines 56-63)
- ❌ Remove: Import `get_admin_user` if not used elsewhere

### 6. app/core/security.py
**Changes**:
- ❌ Remove: `create_initial_admin()` function
- ❌ Remove: `get_admin_user()` dependency function
- ❌ Remove: Any admin role checking logic
- ✅ Keep: All user authentication logic

---

## 📊 SUMMARY

### Endpoints Count
- **Total Endpoints in Spec**: 42 user endpoints
- **Current User Endpoints**: 42 ✅
- **Admin Endpoints to Remove**: ~100+ ❌
- **Final Endpoint Count**: 42 user-only endpoints

### Files to Modify
- ✅ Delete: `app/api/v1/admin.py` (entire file)
- ✅ Modify: `app/main.py` (remove admin router)
- ✅ Modify: `app/api/v1/auth.py` (remove admin login, deprecated endpoints)
- ✅ Modify: `app/api/v1/address_resolver.py` (remove admin endpoint)
- ✅ Modify: `app/api/v1/users.py` (remove admin endpoint)
- ✅ Modify: `app/core/security.py` (remove admin functions)

### Database Changes
- No database schema changes needed
- Admin-related tables can remain (for future use or manual admin access)
- All user tables remain unchanged

### Security Changes
- Remove admin authentication middleware
- Remove admin role checking
- Keep all user authentication and authorization

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Remove Admin Router
1. Delete `app/api/v1/admin.py`
2. Remove admin router from `app/main.py`
3. Remove `create_initial_admin()` call

### Phase 2: Clean Auth Endpoints
1. Remove deprecated endpoints in `auth.py`
2. Remove admin login endpoint
3. Remove duplicate forgot-password endpoints
4. Clean up universal auth endpoints

### Phase 3: Clean Other Endpoints
1. Remove admin endpoint from `address_resolver.py`
2. Remove admin endpoint from `users.py`
3. Remove admin dependencies

### Phase 4: Clean Security Module
1. Remove `get_admin_user()` function
2. Remove `create_initial_admin()` function
3. Remove admin role checking logic

### Phase 5: Testing
1. Test all user endpoints
2. Verify no admin endpoints are accessible
3. Verify authentication works correctly
4. Test all CRUD operations

---

## ⚠️ IMPORTANT NOTES

1. **No Admin Access**: After this refactor, there will be NO admin access to the system
2. **KYC Approval**: KYC submissions will need manual database updates or a separate admin tool
3. **User Management**: User management will need to be done directly in the database
4. **Monitoring**: System monitoring will need external tools
5. **Backup**: Ensure database backup before making changes

---

## ✅ VERIFICATION CHECKLIST

After refactoring, verify:
- [ ] No `/api/v1/admin/*` endpoints exist
- [ ] No admin login functionality
- [ ] All 42 user endpoints work correctly
- [ ] Authentication works for users only
- [ ] KYC submission works (approval will be manual)
- [ ] Transactions work correctly
- [ ] Wallet operations work correctly
- [ ] Address resolver works correctly
- [ ] Notifications work correctly
- [ ] Token prices work correctly

---

**End of Analysis**
