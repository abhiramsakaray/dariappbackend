# DARI Backend Refactoring Plan
**Date**: October 11, 2025  
**Objective**: Align current backend with BACKEND_API_SPECIFICATION.md and remove all admin functionality

---

## 📊 Current vs. Specification Analysis

### ✅ Endpoints That Match Specification (No Changes Needed)

#### Authentication Endpoints
1. ✅ `POST /api/v1/auth/register/request-otp` - Already implemented
2. ✅ `POST /api/v1/auth/register/complete` - Already implemented
3. ✅ `POST /api/v1/auth/login/request-otp` - Already implemented
4. ✅ `POST /api/v1/auth/login/verify-otp` - Already implemented
5. ✅ `POST /api/v1/auth/refresh` - Already implemented
6. ✅ `GET /api/v1/auth/me` - Already implemented
7. ✅ `POST /api/v1/auth/logout` - Already implemented
8. ✅ `POST /api/v1/auth/set-pin` - Already implemented
9. ✅ `POST /api/v1/auth/verify-pin` - Already implemented
10. ✅ `POST /api/v1/auth/forgot-password/request-otp` - Already implemented
11. ✅ `POST /api/v1/auth/forgot-password/reset` - Already implemented

#### KYC Endpoints
1. ✅ `POST /api/v1/kyc/upload-document` - Already implemented
2. ✅ `POST /api/v1/kyc/upload-selfie` - Already implemented
3. ✅ `POST /api/v1/kyc/submit` - Already implemented
4. ✅ `GET /api/v1/kyc/status` - Already implemented
5. ✅ `GET /api/v1/kyc/files-status` - Already implemented

#### Wallet Endpoints
1. ✅ `POST /api/v1/wallets/create` - Already implemented
2. ✅ `GET /api/v1/wallets/` - Already implemented
3. ✅ `GET /api/v1/wallets/balance` - Already implemented

#### Transaction Endpoints
1. ✅ `POST /api/v1/transactions/estimate-gas` - Already implemented
2. ✅ `POST /api/v1/transactions/send` - Already implemented
3. ✅ `GET /api/v1/transactions/` - Already implemented
4. ✅ `GET /api/v1/transactions/{transaction_id}` - Already implemented

#### Address/Username Endpoints
1. ✅ `POST /api/v1/address/create` - Already implemented
2. ✅ `GET /api/v1/address/my-address` - Already implemented
3. ✅ `PUT /api/v1/address/update` - Already implemented
4. ✅ `POST /api/v1/address/resolve` - Already implemented
5. ✅ `GET /api/v1/address/check-username/{username}` - Already implemented
6. ✅ `DELETE /api/v1/address/delete` - Already implemented

#### Token Endpoints
1. ✅ `GET /api/v1/tokens/` - Already implemented
2. ✅ `GET /api/v1/tokens/prices` - Already implemented

#### Notification Endpoints
1. ✅ `GET /api/v1/notifications/` - Already implemented
2. ✅ `GET /api/v1/notifications/unread/count` - Already implemented
3. ✅ `PATCH /api/v1/notifications/{notification_id}/read` - Already implemented
4. ✅ `PATCH /api/v1/notifications/read-all` - Already implemented
5. ✅ `DELETE /api/v1/notifications/{notification_id}` - Already implemented

#### User Profile Endpoints
1. ✅ `GET /api/v1/users/profile` - Already implemented
2. ✅ `PUT /api/v1/users/profile` - Already implemented
3. ✅ `GET /api/v1/users/pin-status` - Already implemented

---

## ❌ Endpoints/Features to REMOVE (Admin & Deprecated)

### Authentication (app/api/v1/auth.py)
1. ❌ `POST /api/v1/auth/register` (deprecated) - Line 237
2. ❌ `POST /api/v1/auth/login` (deprecated) - Line 268
3. ❌ `POST /api/v1/auth/request-otp` (deprecated) - Line 635
4. ❌ `POST /api/v1/auth/verify-otp` (deprecated) - Line 655
5. ❌ `POST /api/v1/auth/change-password` (not in spec) - Line 568
6. ❌ `POST /api/v1/auth/universal/login/request-otp` (redundant) - Line 686
7. ❌ `POST /api/v1/auth/universal/login/verify-otp` (redundant) - Line 739
8. ❌ `POST /api/v1/auth/universal/forgot-password/request-otp` (redundant) - Line 804
9. ❌ `POST /api/v1/auth/universal/forgot-password/reset` (redundant) - Line 830
10. ❌ `POST /api/v1/auth/admin/login` (ADMIN) - Line 880

### Address Resolver (app/api/v1/address_resolver.py)
1. ❌ `GET /api/v1/address/admin/all` (ADMIN) - Line 222

### Users (app/api/v1/users.py)
1. ❌ `GET /api/v1/users/stats` (not in spec) - Line 56

### Notifications (app/api/v1/notifications.py)
1. ❌ `GET /api/v1/notifications/{notification_id}` (not in spec) - Line 159

---

## 🗑️ Files to DELETE

### Models
1. ❌ `app/models/admin_log.py` - Admin logging model
2. ❌ `app/models/admin_monitoring.py` - Admin monitoring model
3. ❌ `app/models/admin_task.py` - Admin task model
4. ❌ `app/models/permission.py` - Admin permissions model
5. ❌ `app/models/login_log.py` - Logging model (if admin-only)

### CRUD Operations
1. ❌ `app/crud/admin.py` - Admin CRUD operations

### Migrations (if admin-related)
1. Check `alembic/versions/admin_management_v1.py`
2. Check `app/models/__init__.py` for admin imports

---

## 🔧 Files to MODIFY

### 1. app/main.py
- Remove admin router imports (if any)
- Keep only user-facing routers

### 2. app/api/v1/auth.py
- Remove deprecated endpoints (lines 237, 268, 635, 655, 568)
- Remove universal endpoints (lines 686, 739, 804, 830)
- Remove admin login endpoint (line 880)
- Keep only specification-compliant endpoints

### 3. app/api/v1/address_resolver.py
- Remove admin endpoint (line 222)

### 4. app/api/v1/users.py
- Remove stats endpoint (line 56)

### 5. app/api/v1/notifications.py
- Remove get single notification endpoint (line 159)

### 6. app/core/security.py
- Remove admin-related functions (e.g., require_admin, is_admin)
- Keep user authentication functions

### 7. app/models/__init__.py
- Remove admin model imports

### 8. app/crud/__init__.py
- Remove admin CRUD imports

---

## 📋 Implementation Steps

### Phase 1: Remove Admin Models & CRUD ✅
1. Delete `app/models/admin_log.py`
2. Delete `app/models/admin_monitoring.py`
3. Delete `app/models/admin_task.py`
4. Delete `app/models/permission.py`
5. Delete `app/crud/admin.py`
6. Update `app/models/__init__.py`
7. Update `app/crud/__init__.py`

### Phase 2: Clean Authentication Endpoints
1. Remove deprecated `/register` endpoint
2. Remove deprecated `/login` endpoint
3. Remove deprecated `/request-otp` endpoint
4. Remove deprecated `/verify-otp` endpoint
5. Remove `/change-password` endpoint
6. Remove all `/universal/*` endpoints
7. Remove `/admin/login` endpoint
8. Clean up related imports and functions

### Phase 3: Clean Other Endpoints
1. Remove `/address/admin/all` endpoint
2. Remove `/users/stats` endpoint
3. Remove `/notifications/{notification_id}` GET endpoint

### Phase 4: Clean Core & Security
1. Remove admin-related functions from `app/core/security.py`
2. Remove admin-related middleware
3. Update `app/main.py` if needed

### Phase 5: Update Schemas & Validation
1. Ensure response formats match specification
2. Update error codes to match specification
3. Verify all validations match spec requirements

### Phase 6: Testing & Documentation
1. Test all remaining endpoints
2. Verify no admin endpoints accessible
3. Update API documentation
4. Update progress.md

---

## 🎯 Final Endpoint Count

### Specification Requirements: 42 endpoints
### Current Implementation: ~55 endpoints
### After Cleanup: 42 endpoints

**Endpoints to Remove**: 13
**Endpoints to Keep**: 42

---

## ⚠️ Important Notes

1. **Preserve User Functionality**: All user-facing features must remain intact
2. **No Breaking Changes**: Existing mobile app should continue working
3. **Clean Migration**: Consider database migrations for admin table removal
4. **Security**: Ensure no backdoor admin access remains
5. **Testing**: Thoroughly test after each phase

---

## 📝 Response Format Alignment

Current response format mostly matches specification. Key points:
- ✅ Success responses use `{"success": true, "data": {...}}`
- ✅ Error responses use `{"success": false, "error": {...}}`
- ✅ HTTP status codes align with specification
- ⚠️ May need to adjust some response field names for exact match

---

## 🔒 Security Considerations

1. Remove all admin authentication logic
2. Remove admin role checks
3. Remove admin permissions system
4. Keep user PIN verification
5. Keep OTP system
6. Keep JWT token system
7. Ensure rate limiting remains on all endpoints

---

**Status**: Ready for implementation  
**Estimated Time**: 4-6 hours  
**Risk Level**: Medium (requires careful testing)
