# DARI MVP - Backend API Specification
## Complete API Documentation for Backend Development

**Last Updated**: October 11, 2025  
**API Version**: v1  
**Base URL**: `http://localhost:8000` (Development) | `https://api.dariorganization.com` (Production)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Endpoints by Category](#api-endpoints-by-category)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [WebSocket Events](#websocket-events)
7. [Rate Limiting](#rate-limiting)
8. [Security Requirements](#security-requirements)
9. [Database Schema](#database-schema)
10. [Third-Party Integrations](#third-party-integrations)

---

## 🎯 Overview

### Technology Stack Recommendations

**Backend Framework**: 
- Node.js + Express.js (Recommended)
- Python + FastAPI
- Go + Gin

**Database**:
- PostgreSQL (Primary) - For relational data
- Redis (Cache) - For sessions, OTP, rate limiting
- MongoDB (Optional) - For notifications, logs

**Blockchain**:
- Solana or Polygon for USDC transfers
- Web3.js or Ethers.js for blockchain interaction

**File Storage**:
- AWS S3 / Google Cloud Storage - For KYC documents
- Cloudinary - For image optimization

**Message Queue**:
- RabbitMQ / AWS SQS - For transaction processing
- Bull (Node.js) - For job queues

**Email/SMS**:
- SendGrid / AWS SES - For emails
- Twilio - For SMS OTP

---

## 🔐 Authentication & Authorization

### JWT Token Structure

**Access Token** (Short-lived: 15 minutes):
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "kyc_verified": true,
  "exp": 1697123456
}
```

**Refresh Token** (Long-lived: 7 days):
```json
{
  "user_id": 123,
  "token_version": 1,
  "exp": 1697723456
}
```

### Authentication Flow

1. **Registration** → OTP Verification → Complete Registration → Auto Login
2. **Login** → OTP Verification → Issue Tokens
3. **Token Refresh** → Validate Refresh Token → Issue New Access Token
4. **Logout** → Invalidate Refresh Token

---

## 📡 API Endpoints by Category

## 1️⃣ Authentication Endpoints

### 1.1 Request Registration OTP

**Endpoint**: `POST /api/v1/auth/register/request-otp`

**Purpose**: Request OTP for new user registration

**Request Body**:
```json
{
  "email": "user@example.com",
  "phone": "+911234567890"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "otp_expires_at": "2025-10-11T10:15:00Z",
    "otp_length": 6
  }
}
```

**Validations**:
- Email format validation
- Phone format validation (E.164)
- Check if email/phone already exists
- Rate limit: 3 OTP requests per hour per email/phone

**Business Logic**:
- Generate 6-digit OTP
- Store OTP in Redis with 5-minute expiry
- Send OTP via email AND SMS
- Log OTP request for audit

---

### 1.2 Complete Registration

**Endpoint**: `POST /api/v1/auth/register/complete`

**Purpose**: Complete registration with OTP verification

**Request Body**:
```json
{
  "email": "user@example.com",
  "phone": "+911234567890",
  "password": "SecurePassword123!",
  "otp": "123456",
  "default_currency": "USD",
  "terms_accepted": true
}
```

**Response** (201):
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "phone": "+911234567890",
      "default_currency": "USD",
      "kyc_status": "pending",
      "created_at": "2025-10-11T10:10:00Z"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires_in": 900
    }
  }
}
```

**Validations**:
- OTP must be valid and not expired
- Password strength: min 8 chars, 1 uppercase, 1 number, 1 special char
- Terms must be accepted
- Email/phone uniqueness

**Business Logic**:
- Verify OTP from Redis
- Hash password (bcrypt, 10 rounds)
- Create user record
- Auto-create wallet (blockchain)
- Generate DARI username (e.g., @user123)
- Send welcome email
- Return JWT tokens
- Clear OTP from Redis

---

### 1.3 Request Login OTP

**Endpoint**: `POST /api/v1/auth/login/request-otp`

**Purpose**: Request OTP for login

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "otp_expires_at": "2025-10-11T10:15:00Z",
    "masked_phone": "+91****7890",
    "masked_email": "u***@example.com"
  }
}
```

**Validations**:
- Verify email exists
- Verify password matches (bcrypt compare)
- Check if account is active
- Rate limit: 5 failed attempts → 15-minute lockout

**Business Logic**:
- Validate credentials
- Generate 6-digit OTP
- Store in Redis (5-minute expiry)
- Send OTP to registered email/phone
- Increment failed login counter if password wrong

---

### 1.4 Verify Login OTP

**Endpoint**: `POST /api/v1/auth/login/verify-otp`

**Purpose**: Verify OTP and complete login

**Request Body**:
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 123,
      "email": "user@example.com",
      "phone": "+911234567890",
      "username": "@john_dari",
      "kyc_status": "approved",
      "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "default_currency": "USD"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "expires_in": 900
    }
  }
}
```

**Business Logic**:
- Verify OTP from Redis
- Generate JWT tokens
- Update last_login timestamp
- Clear OTP from Redis
- Create login session
- Log login activity

---

### 1.5 Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Purpose**: Get new access token using refresh token

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900
  }
}
```

**Business Logic**:
- Validate refresh token signature
- Check if token is blacklisted
- Verify user still exists and is active
- Generate new access token
- Optionally rotate refresh token
- Update token version if rotated

---

### 1.6 Get Current User

**Endpoint**: `GET /api/v1/auth/me`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "id": 123,
    "email": "user@example.com",
    "phone": "+911234567890",
    "username": "@john_dari",
    "display_name": "John Doe",
    "kyc_status": "approved",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "default_currency": "USD",
    "pin_set": true,
    "created_at": "2025-10-11T10:10:00Z"
  }
}
```

---

### 1.7 Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Business Logic**:
- Add refresh token to blacklist (Redis)
- Invalidate user session
- Log logout activity

---

### 1.8 Set PIN

**Endpoint**: `POST /api/v1/auth/set-pin`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "pin": "1234"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "PIN set successfully"
}
```

**Validations**:
- PIN must be 4-6 digits
- PIN cannot be sequential (1234, 4321)
- PIN cannot be repeating (1111, 2222)

**Business Logic**:
- Hash PIN (bcrypt)
- Store in user record
- Send confirmation email

---

### 1.9 Verify PIN

**Endpoint**: `POST /api/v1/auth/verify-pin`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "pin": "1234"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "PIN verified",
  "data": {
    "verified": true
  }
}
```

**Business Logic**:
- Compare PIN hash
- Track failed attempts
- Lock account after 3 failed attempts (15 minutes)

---

### 1.10 Forgot Password - Request OTP

**Endpoint**: `POST /api/v1/auth/forgot-password/request-otp`

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Password reset OTP sent",
  "data": {
    "otp_expires_at": "2025-10-11T10:15:00Z"
  }
}
```

---

### 1.11 Forgot Password - Reset

**Endpoint**: `POST /api/v1/auth/forgot-password/reset`

**Request Body**:
```json
{
  "email": "user@example.com",
  "otp": "123456",
  "new_password": "NewSecurePassword123!"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Password reset successful"
}
```

**Business Logic**:
- Verify OTP
- Validate new password strength
- Hash new password
- Update user record
- Invalidate all existing sessions
- Send password changed email

---

## 2️⃣ KYC Endpoints

### 2.1 Upload KYC Document

**Endpoint**: `POST /api/v1/kyc/upload-document`

**Headers**: 
- `Authorization: Bearer {access_token}`
- `Content-Type: multipart/form-data`

**Request Body** (Form Data):
```
file: [File] (image/jpeg, image/png, application/pdf)
document_type: "pan_card" | "aadhar" | "passport" | "driving_license"
```

**Response** (200):
```json
{
  "success": true,
  "message": "Document uploaded successfully",
  "data": {
    "file_id": "kyc_doc_123456",
    "file_url": "https://s3.amazonaws.com/dari-kyc/user123/pan_card_123456.jpg",
    "file_size": 2048576,
    "uploaded_at": "2025-10-11T10:20:00Z"
  }
}
```

**Validations**:
- File size: Max 5MB
- File types: JPEG, PNG, PDF only
- Image resolution: Min 800x600
- User must be authenticated

**Business Logic**:
- Validate file format and size
- Scan for malware
- Compress image if needed
- Upload to S3 with encryption
- Generate unique file ID
- Store metadata in database
- Update KYC status to "documents_uploaded"

---

### 2.2 Upload Selfie

**Endpoint**: `POST /api/v1/kyc/upload-selfie`

**Headers**: 
- `Authorization: Bearer {access_token}`
- `Content-Type: multipart/form-data`

**Request Body** (Form Data):
```
file: [File] (image/jpeg, image/png)
```

**Response** (200):
```json
{
  "success": true,
  "message": "Selfie uploaded successfully",
  "data": {
    "file_id": "kyc_selfie_123456",
    "file_url": "https://s3.amazonaws.com/dari-kyc/user123/selfie_123456.jpg",
    "face_detected": true,
    "uploaded_at": "2025-10-11T10:22:00Z"
  }
}
```

**Business Logic**:
- Validate image contains face (optional: use AWS Rekognition)
- Check for image quality
- Upload to S3 with encryption
- Store metadata
- Compare with document photo (optional AI verification)

---

### 2.3 Submit KYC

**Endpoint**: `POST /api/v1/kyc/submit`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "document_type": "pan_card",
  "document_number": "ABCDE1234F",
  "full_name": "John Doe",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "address": {
    "street": "123 Main Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "country": "India"
  },
  "occupation": "Software Engineer",
  "annual_income_range": "500000-1000000"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "KYC submitted for review",
  "data": {
    "kyc_id": "kyc_123456",
    "status": "under_review",
    "submitted_at": "2025-10-11T10:25:00Z",
    "estimated_review_time": "24-48 hours"
  }
}
```

**Validations**:
- All required fields present
- Document number format validation
- Date of birth: User must be 18+
- Address validation
- Documents must be uploaded first

**Business Logic**:
- Validate all KYC data
- Create KYC submission record
- Update user KYC status to "under_review"
- Trigger KYC verification workflow (manual or automated)
- Send submission confirmation email
- Notify admin for review

---

### 2.4 Get KYC Status

**Endpoint**: `GET /api/v1/kyc/status`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "status": "approved",
    "submitted_at": "2025-10-11T10:25:00Z",
    "reviewed_at": "2025-10-11T12:30:00Z",
    "reviewer_notes": "",
    "rejection_reason": null,
    "documents_uploaded": true,
    "selfie_uploaded": true,
    "details_submitted": true
  }
}
```

**Possible Statuses**:
- `pending` - Not started
- `documents_uploaded` - Documents uploaded, details pending
- `under_review` - Submitted and being reviewed
- `approved` - KYC approved
- `rejected` - KYC rejected (with reason)

---

### 2.5 Get KYC Files Status

**Endpoint**: `GET /api/v1/kyc/files-status`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "document_uploaded": true,
    "document_url": "https://s3.amazonaws.com/dari-kyc/user123/pan_card_123456.jpg",
    "selfie_uploaded": true,
    "selfie_url": "https://s3.amazonaws.com/dari-kyc/user123/selfie_123456.jpg"
  }
}
```

---

## 3️⃣ Wallet Endpoints

### 3.1 Create Wallet

**Endpoint**: `POST /api/v1/wallets/create`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (201):
```json
{
  "success": true,
  "message": "Wallet created successfully",
  "data": {
    "wallet_id": "wallet_123456",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "chain": "polygon",
    "created_at": "2025-10-11T10:30:00Z"
  }
}
```

**Business Logic**:
- Generate new blockchain wallet (Solana/Polygon)
- Store private key in encrypted vault (AWS KMS, HashiCorp Vault)
- Associate wallet with user
- Initialize balance as 0
- Send wallet creation email

---

### 3.2 Get Wallet

**Endpoint**: `GET /api/v1/wallets/`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "wallet_id": "wallet_123456",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "chain": "polygon",
    "balances": {
      "USDC": "1500.50"
    },
    "created_at": "2025-10-11T10:30:00Z"
  }
}
```

---

### 3.3 Get Balance

**Endpoint**: `GET /api/v1/wallets/balance`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "balances": [
      {
        "token": "USDC",
        "balance": "1500.50",
        "usd_value": "1500.50",
        "contract_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
      }
    ],
    "total_usd_value": "1500.50",
    "last_updated": "2025-10-11T10:35:00Z"
  }
}
```

**Business Logic**:
- Query blockchain for real-time balance
- Cache balance in Redis (5-minute TTL)
- Convert to USD using current exchange rates
- Return all token balances

---

## 4️⃣ Transaction Endpoints

### 4.1 Estimate Gas Fee

**Endpoint**: `POST /api/v1/transactions/estimate-gas`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "amount": "100.50",
  "token": "USDC"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "gas_estimate": "0.0015",
    "gas_price_gwei": "25",
    "total_fee_usd": "0.75",
    "estimated_time": "30 seconds"
  }
}
```

**Business Logic**:
- Call blockchain RPC to estimate gas
- Get current gas price
- Calculate total fee in USD
- Return estimate to user

---

### 4.2 Send Transaction

**Endpoint**: `POST /api/v1/transactions/send`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "to_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "to_username": "@jane_dari",
  "amount": "100.50",
  "token": "USDC",
  "pin": "1234",
  "note": "Payment for dinner"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Transaction initiated",
  "data": {
    "transaction_id": 789,
    "tx_hash": "0x1234567890abcdef...",
    "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "to_address": "0x987d35Cc6634C0532925a3b844Bc9e7595f0xyz",
    "amount": "100.50",
    "token": "USDC",
    "fee": "0.75",
    "total": "101.25",
    "status": "pending",
    "created_at": "2025-10-11T10:40:00Z"
  }
}
```

**Validations**:
- PIN verification required
- Check sufficient balance (amount + fee)
- Validate recipient address/username
- KYC must be approved
- Rate limit: 10 transactions per minute

**Business Logic**:
1. Verify user PIN
2. Resolve username to wallet address (if username provided)
3. Check user balance
4. Estimate gas fee
5. Create transaction record (status: pending)
6. Decrypt wallet private key
7. Sign transaction
8. Broadcast to blockchain
9. Update transaction with tx_hash
10. Add to monitoring queue
11. Send confirmation to user
12. Send notification to recipient
13. Return transaction details

**Transaction Processing** (Background Job):
- Monitor transaction status on blockchain
- Update status when confirmed
- Send push notification on confirmation
- Update balances
- Handle failures and retries

---

### 4.3 Get Transaction History

**Endpoint**: `GET /api/v1/transactions/`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `limit` (default: 50, max: 100)
- `offset` (default: 0)
- `type` (optional: "send" | "receive" | "all")
- `status` (optional: "pending" | "confirmed" | "failed")
- `from_date` (optional: ISO 8601 date)
- `to_date` (optional: ISO 8601 date)

**Example**: `GET /api/v1/transactions/?limit=20&offset=0&type=send`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": 789,
        "tx_hash": "0x1234567890abcdef...",
        "type": "send",
        "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "to_address": "0x987d35Cc6634C0532925a3b844Bc9e7595f0xyz",
        "to_username": "@jane_dari",
        "to_display_name": "Jane Doe",
        "amount": "100.50",
        "token": "USDC",
        "fee": "0.75",
        "status": "confirmed",
        "note": "Payment for dinner",
        "created_at": "2025-10-11T10:40:00Z",
        "confirmed_at": "2025-10-11T10:41:00Z"
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

---

### 4.4 Get Transaction Details

**Endpoint**: `GET /api/v1/transactions/{transaction_id}`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "id": 789,
    "tx_hash": "0x1234567890abcdef...",
    "type": "send",
    "from_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "from_username": "@john_dari",
    "to_address": "0x987d35Cc6634C0532925a3b844Bc9e7595f0xyz",
    "to_username": "@jane_dari",
    "to_display_name": "Jane Doe",
    "amount": "100.50",
    "token": "USDC",
    "fee": "0.75",
    "total": "101.25",
    "status": "confirmed",
    "confirmations": 15,
    "note": "Payment for dinner",
    "created_at": "2025-10-11T10:40:00Z",
    "confirmed_at": "2025-10-11T10:41:00Z",
    "blockchain_explorer_url": "https://polygonscan.com/tx/0x1234567890abcdef..."
  }
}
```

---

## 5️⃣ Address/Username Endpoints

### 5.1 Create Username

**Endpoint**: `POST /api/v1/address/create`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "username": "john_dari"
}
```

**Response** (201):
```json
{
  "success": true,
  "message": "Username created successfully",
  "data": {
    "username": "@john_dari",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "created_at": "2025-10-11T10:45:00Z"
  }
}
```

**Validations**:
- Username: 3-20 characters, alphanumeric + underscore
- Username must be unique
- User can only have 1 username

---

### 5.2 Get My Address

**Endpoint**: `GET /api/v1/address/my-address`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "username": "@john_dari",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "qr_code_url": "https://api.dari.com/qr/@john_dari"
  }
}
```

---

### 5.3 Update Username

**Endpoint**: `PUT /api/v1/address/update`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "username": "johndoe_dari"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Username updated successfully",
  "data": {
    "username": "@johndoe_dari"
  }
}
```

---

### 5.4 Resolve Address

**Endpoint**: `POST /api/v1/address/resolve`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "address": "@jane_dari"
}
```

**Response** (200):
```json
{
  "success": true,
  "data": {
    "username": "@jane_dari",
    "display_name": "Jane Doe",
    "wallet_address": "0x987d35Cc6634C0532925a3b844Bc9e7595f0xyz",
    "kyc_verified": true
  }
}
```

**Business Logic**:
- Accept either username or wallet address
- Return associated details
- Hide sensitive info if user is not found

---

### 5.5 Check Username Availability

**Endpoint**: `GET /api/v1/address/check-username/{username}`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "username": "john_dari",
    "available": false,
    "suggestions": ["john_dari2", "john_dari_official", "johnxdari"]
  }
}
```

---

### 5.6 Delete Username

**Endpoint**: `DELETE /api/v1/address/delete`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "message": "Username deleted successfully"
}
```

---

## 6️⃣ Token Endpoints

### 6.1 Get Supported Tokens

**Endpoint**: `GET /api/v1/tokens/`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "tokens": [
      {
        "symbol": "USDC",
        "name": "USD Coin",
        "decimals": 6,
        "contract_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "chain": "polygon",
        "logo_url": "https://assets.dari.com/tokens/usdc.png"
      }
    ]
  }
}
```

---

### 6.2 Get Token Prices

**Endpoint**: `GET /api/v1/tokens/prices`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "prices": {
      "USDC": {
        "USD": 1.00,
        "INR": 83.50,
        "EUR": 0.92,
        "GBP": 0.79
      }
    },
    "last_updated": "2025-10-11T10:50:00Z"
  }
}
```

**Business Logic**:
- Fetch prices from CoinGecko/CoinMarketCap API
- Cache prices in Redis (5-minute TTL)
- Support multiple fiat currencies

---

## 7️⃣ Notification Endpoints

### 7.1 Get Notifications

**Endpoint**: `GET /api/v1/notifications/`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `page` (default: 1)
- `per_page` (default: 20, max: 50)
- `unread_only` (default: false)

**Response** (200):
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": 456,
        "type": "transaction_received",
        "title": "Money Received",
        "message": "You received $100.50 from @jane_dari",
        "data": {
          "transaction_id": 789,
          "amount": "100.50",
          "from_username": "@jane_dari"
        },
        "read": false,
        "created_at": "2025-10-11T10:55:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total": 50,
      "total_pages": 3
    }
  }
}
```

---

### 7.2 Get Unread Count

**Endpoint**: `GET /api/v1/notifications/unread/count`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "unread_count": 5
  }
}
```

---

### 7.3 Mark as Read

**Endpoint**: `PATCH /api/v1/notifications/{notification_id}/read`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

---

### 7.4 Mark All as Read

**Endpoint**: `PATCH /api/v1/notifications/read-all`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "message": "All notifications marked as read"
}
```

---

### 7.5 Delete Notification

**Endpoint**: `DELETE /api/v1/notifications/{notification_id}`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "message": "Notification deleted"
}
```

---

## 8️⃣ User Profile Endpoints

### 8.1 Get Profile

**Endpoint**: `GET /api/v1/users/profile`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "id": 123,
    "email": "user@example.com",
    "phone": "+911234567890",
    "username": "@john_dari",
    "display_name": "John Doe",
    "avatar_url": "https://assets.dari.com/avatars/user123.jpg",
    "default_currency": "USD",
    "kyc_status": "approved",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "created_at": "2025-10-11T10:10:00Z"
  }
}
```

---

### 8.2 Update Profile

**Endpoint**: `PUT /api/v1/users/profile`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "display_name": "John Doe",
  "default_currency": "INR",
  "phone": "+911234567890"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "display_name": "John Doe",
    "default_currency": "INR"
  }
}
```

---

### 8.3 Get PIN Status

**Endpoint**: `GET /api/v1/users/pin-status`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "success": true,
  "data": {
    "pin_set": true
  }
}
```

---

## 📊 Data Models

### User Model
```javascript
{
  id: Integer (Primary Key),
  email: String (Unique, Indexed),
  phone: String (Unique, Indexed),
  password_hash: String,
  username: String (Unique, Indexed, Nullable),
  display_name: String,
  avatar_url: String (Nullable),
  default_currency: String (Default: 'USD'),
  kyc_status: Enum ['pending', 'under_review', 'approved', 'rejected'],
  pin_hash: String (Nullable),
  pin_attempts: Integer (Default: 0),
  pin_locked_until: Timestamp (Nullable),
  wallet_address: String (Unique, Indexed),
  email_verified: Boolean (Default: false),
  phone_verified: Boolean (Default: false),
  is_active: Boolean (Default: true),
  last_login: Timestamp,
  created_at: Timestamp,
  updated_at: Timestamp
}
```

### Wallet Model
```javascript
{
  id: Integer (Primary Key),
  user_id: Integer (Foreign Key → users.id),
  address: String (Unique, Indexed),
  chain: String (Default: 'polygon'),
  encrypted_private_key: String,
  created_at: Timestamp,
  updated_at: Timestamp
}
```

### Transaction Model
```javascript
{
  id: Integer (Primary Key),
  tx_hash: String (Unique, Indexed, Nullable),
  from_user_id: Integer (Foreign Key → users.id),
  to_user_id: Integer (Foreign Key → users.id, Nullable),
  from_address: String,
  to_address: String,
  amount: Decimal(18, 8),
  token: String (Default: 'USDC'),
  fee: Decimal(18, 8),
  status: Enum ['pending', 'confirmed', 'failed', 'cancelled'],
  confirmations: Integer (Default: 0),
  note: Text (Nullable),
  error_message: Text (Nullable),
  created_at: Timestamp,
  confirmed_at: Timestamp (Nullable),
  updated_at: Timestamp
}
```

### KYC Model
```javascript
{
  id: Integer (Primary Key),
  user_id: Integer (Foreign Key → users.id),
  document_type: Enum ['pan_card', 'aadhar', 'passport', 'driving_license'],
  document_number: String,
  document_file_url: String,
  selfie_file_url: String,
  full_name: String,
  date_of_birth: Date,
  gender: Enum ['male', 'female', 'other'],
  address_street: String,
  address_city: String,
  address_state: String,
  address_postal_code: String,
  address_country: String,
  occupation: String,
  annual_income_range: String,
  status: Enum ['pending', 'under_review', 'approved', 'rejected'],
  reviewer_id: Integer (Nullable),
  reviewer_notes: Text (Nullable),
  rejection_reason: Text (Nullable),
  submitted_at: Timestamp,
  reviewed_at: Timestamp (Nullable),
  created_at: Timestamp,
  updated_at: Timestamp
}
```

### Notification Model
```javascript
{
  id: Integer (Primary Key),
  user_id: Integer (Foreign Key → users.id),
  type: Enum ['transaction_sent', 'transaction_received', 'kyc_update', 'login_alert', 'security_alert'],
  title: String,
  message: Text,
  data: JSON,
  read: Boolean (Default: false),
  created_at: Timestamp
}
```

---

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_OTP",
    "message": "The OTP you entered is invalid or expired",
    "details": {
      "field": "otp",
      "attempts_remaining": 2
    }
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH, DELETE |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid auth token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., email exists) |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Maintenance mode |

### Common Error Codes

```javascript
// Authentication
AUTH_INVALID_CREDENTIALS = "Invalid email or password"
AUTH_OTP_EXPIRED = "OTP has expired. Please request a new one"
AUTH_OTP_INVALID = "Invalid OTP"
AUTH_EMAIL_EXISTS = "Email already registered"
AUTH_TOKEN_EXPIRED = "Access token has expired"
AUTH_ACCOUNT_LOCKED = "Account locked due to multiple failed attempts"

// KYC
KYC_ALREADY_SUBMITTED = "KYC already submitted"
KYC_DOCUMENTS_MISSING = "Please upload required documents"
KYC_INVALID_DOCUMENT = "Document type not supported"
KYC_FILE_TOO_LARGE = "File size exceeds 5MB limit"

// Transactions
TRANSACTION_INSUFFICIENT_BALANCE = "Insufficient balance"
TRANSACTION_INVALID_ADDRESS = "Invalid recipient address"
TRANSACTION_INVALID_PIN = "Invalid PIN"
TRANSACTION_LIMIT_EXCEEDED = "Transaction limit exceeded"
TRANSACTION_BLOCKCHAIN_ERROR = "Blockchain transaction failed"

// Wallet
WALLET_ALREADY_EXISTS = "Wallet already created"
WALLET_NOT_FOUND = "Wallet not found"

// Username
USERNAME_TAKEN = "Username already taken"
USERNAME_INVALID_FORMAT = "Username must be 3-20 characters"

// Rate Limiting
RATE_LIMIT_EXCEEDED = "Too many requests. Please try again later"
```

---

## 🔌 WebSocket Events (Real-time Updates)

### Connection
```
wss://api.dari.com/ws?token={access_token}
```

### Events to Emit (Client → Server)

**Subscribe to notifications**:
```json
{
  "event": "subscribe",
  "channel": "notifications"
}
```

**Subscribe to transaction updates**:
```json
{
  "event": "subscribe",
  "channel": "transactions"
}
```

### Events to Listen (Server → Client)

**Transaction status update**:
```json
{
  "event": "transaction_update",
  "data": {
    "transaction_id": 789,
    "status": "confirmed",
    "confirmations": 15
  }
}
```

**New notification**:
```json
{
  "event": "new_notification",
  "data": {
    "id": 456,
    "type": "transaction_received",
    "title": "Money Received",
    "message": "You received $100.50 from @jane_dari"
  }
}
```

**Balance update**:
```json
{
  "event": "balance_update",
  "data": {
    "token": "USDC",
    "balance": "1650.75"
  }
}
```

---

## 🚦 Rate Limiting

### Limits by Endpoint Type

| Endpoint Type | Rate Limit | Window |
|---------------|------------|--------|
| Authentication (Login/Register) | 5 requests | 15 minutes |
| OTP Requests | 3 requests | 1 hour |
| Transactions (Send) | 10 requests | 1 minute |
| Transactions (Query) | 60 requests | 1 minute |
| General API | 100 requests | 1 minute |
| WebSocket Connections | 1 connection | Per user |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1697123456
```

---

## 🔒 Security Requirements

### Must-Have Security Features

1. **HTTPS Only** - All API requests must use TLS 1.2+
2. **JWT Secret Rotation** - Rotate secrets every 90 days
3. **Password Hashing** - bcrypt with 10+ rounds
4. **PIN Hashing** - bcrypt with 12+ rounds
5. **Rate Limiting** - Implement on all endpoints
6. **CORS** - Whitelist only mobile app origins
7. **SQL Injection Protection** - Use parameterized queries
8. **XSS Protection** - Sanitize all user inputs
9. **Private Key Encryption** - Encrypt wallet keys with AES-256
10. **Audit Logging** - Log all sensitive operations
11. **Two-Factor Authentication** - OTP for critical operations
12. **IP Whitelisting** - For admin endpoints
13. **DDoS Protection** - Use Cloudflare or AWS Shield
14. **Security Headers** - Implement HSTS, CSP, etc.

---

## 🗄️ Database Schema (PostgreSQL)

### Users Table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(20) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  username VARCHAR(50) UNIQUE,
  display_name VARCHAR(100),
  avatar_url VARCHAR(500),
  default_currency VARCHAR(3) DEFAULT 'USD',
  kyc_status VARCHAR(20) DEFAULT 'pending',
  pin_hash VARCHAR(255),
  pin_attempts INTEGER DEFAULT 0,
  pin_locked_until TIMESTAMP,
  wallet_address VARCHAR(100) UNIQUE,
  email_verified BOOLEAN DEFAULT false,
  phone_verified BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_wallet_address ON users(wallet_address);
```

### Wallets Table
```sql
CREATE TABLE wallets (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  address VARCHAR(100) UNIQUE NOT NULL,
  chain VARCHAR(50) DEFAULT 'polygon',
  encrypted_private_key TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_wallets_address ON wallets(address);
```

### Transactions Table
```sql
CREATE TABLE transactions (
  id SERIAL PRIMARY KEY,
  tx_hash VARCHAR(100) UNIQUE,
  from_user_id INTEGER REFERENCES users(id),
  to_user_id INTEGER REFERENCES users(id),
  from_address VARCHAR(100) NOT NULL,
  to_address VARCHAR(100) NOT NULL,
  amount DECIMAL(18, 8) NOT NULL,
  token VARCHAR(10) DEFAULT 'USDC',
  fee DECIMAL(18, 8) DEFAULT 0,
  status VARCHAR(20) DEFAULT 'pending',
  confirmations INTEGER DEFAULT 0,
  note TEXT,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  confirmed_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_from_user ON transactions(from_user_id);
CREATE INDEX idx_transactions_to_user ON transactions(to_user_id);
CREATE INDEX idx_transactions_tx_hash ON transactions(tx_hash);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
```

### KYC Table
```sql
CREATE TABLE kyc_submissions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
  document_type VARCHAR(50),
  document_number VARCHAR(100),
  document_file_url VARCHAR(500),
  selfie_file_url VARCHAR(500),
  full_name VARCHAR(255),
  date_of_birth DATE,
  gender VARCHAR(10),
  address_street VARCHAR(255),
  address_city VARCHAR(100),
  address_state VARCHAR(100),
  address_postal_code VARCHAR(20),
  address_country VARCHAR(100),
  occupation VARCHAR(100),
  annual_income_range VARCHAR(50),
  status VARCHAR(20) DEFAULT 'pending',
  reviewer_id INTEGER REFERENCES users(id),
  reviewer_notes TEXT,
  rejection_reason TEXT,
  submitted_at TIMESTAMP,
  reviewed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kyc_user_id ON kyc_submissions(user_id);
CREATE INDEX idx_kyc_status ON kyc_submissions(status);
```

### Notifications Table
```sql
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  data JSONB,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

---

## 🔗 Third-Party Integrations Required

### 1. Blockchain Provider
- **Recommended**: Alchemy, Infura, QuickNode
- **Purpose**: Polygon/Solana RPC endpoints
- **Cost**: Free tier available, ~$50/month for production

### 2. SMS Provider
- **Recommended**: Twilio
- **Purpose**: OTP SMS delivery
- **Cost**: ~$0.0079 per SMS

### 3. Email Provider
- **Recommended**: SendGrid, AWS SES
- **Purpose**: Transactional emails
- **Cost**: Free tier up to 12,000 emails/month

### 4. File Storage
- **Recommended**: AWS S3, Google Cloud Storage
- **Purpose**: KYC document storage
- **Cost**: ~$0.023 per GB

### 5. Price Feed API
- **Recommended**: CoinGecko API, CoinMarketCap API
- **Purpose**: Crypto/fiat exchange rates
- **Cost**: Free tier available

### 6. Push Notifications
- **Recommended**: Firebase Cloud Messaging (FCM)
- **Purpose**: Mobile push notifications
- **Cost**: Free

### 7. Key Management
- **Recommended**: AWS KMS, HashiCorp Vault
- **Purpose**: Encrypt wallet private keys
- **Cost**: ~$1/month per key

### 8. Monitoring & Logging
- **Recommended**: Sentry (errors), Datadog (monitoring)
- **Purpose**: Error tracking, performance monitoring
- **Cost**: Free tier available

---

## 🚀 Development Roadmap

### Phase 1: Core Backend (Week 1-2)
- [ ] Setup project structure (Node.js/Python)
- [ ] Database setup (PostgreSQL + Redis)
- [ ] Authentication endpoints (8 endpoints)
- [ ] User profile endpoints (3 endpoints)
- [ ] JWT implementation
- [ ] Rate limiting
- [ ] Error handling

### Phase 2: Wallet & Blockchain (Week 2-3)
- [ ] Blockchain integration (Polygon)
- [ ] Wallet creation endpoint
- [ ] Balance checking
- [ ] Private key encryption
- [ ] Gas estimation

### Phase 3: Transactions (Week 3-4)
- [ ] Send transaction endpoint
- [ ] Transaction monitoring job
- [ ] Transaction history endpoint
- [ ] Username resolver
- [ ] Address service endpoints

### Phase 4: KYC (Week 4)
- [ ] File upload endpoints
- [ ] KYC submission endpoint
- [ ] Admin review dashboard
- [ ] S3 integration

### Phase 5: Notifications & Real-time (Week 5)
- [ ] Notification endpoints
- [ ] WebSocket server
- [ ] Push notification integration
- [ ] Email templates

### Phase 6: Testing & Optimization (Week 6)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Load testing
- [ ] Security audit
- [ ] Performance optimization

---

## 📝 Environment Variables (.env)

```bash
# Server
NODE_ENV=production
PORT=8000
API_VERSION=v1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dari_db
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_REFRESH_SECRET=your-refresh-token-secret
JWT_EXPIRY=15m
JWT_REFRESH_EXPIRY=7d

# Blockchain
BLOCKCHAIN_NETWORK=polygon
ALCHEMY_API_KEY=your-alchemy-api-key
WALLET_ENCRYPTION_KEY=your-wallet-encryption-key

# AWS
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=dari-kyc-documents
AWS_REGION=us-east-1

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# SendGrid (Email)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@dari.com

# CoinGecko
COINGECKO_API_KEY=your-coingecko-api-key

# Firebase (Push Notifications)
FIREBASE_PROJECT_ID=dari-app
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@dari-app.iam.gserviceaccount.com

# Rate Limiting
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX_REQUESTS=100

# Logging
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=info
```

---

## ✅ API Checklist for Backend Developer

### Authentication
- [ ] POST /api/v1/auth/register/request-otp
- [ ] POST /api/v1/auth/register/complete
- [ ] POST /api/v1/auth/login/request-otp
- [ ] POST /api/v1/auth/login/verify-otp
- [ ] POST /api/v1/auth/refresh
- [ ] GET /api/v1/auth/me
- [ ] POST /api/v1/auth/logout
- [ ] POST /api/v1/auth/set-pin
- [ ] POST /api/v1/auth/verify-pin
- [ ] POST /api/v1/auth/forgot-password/request-otp
- [ ] POST /api/v1/auth/forgot-password/reset

### KYC
- [ ] POST /api/v1/kyc/upload-document
- [ ] POST /api/v1/kyc/upload-selfie
- [ ] POST /api/v1/kyc/submit
- [ ] GET /api/v1/kyc/status
- [ ] GET /api/v1/kyc/files-status

### Wallet
- [ ] POST /api/v1/wallets/create
- [ ] GET /api/v1/wallets/
- [ ] GET /api/v1/wallets/balance

### Transactions
- [ ] POST /api/v1/transactions/estimate-gas
- [ ] POST /api/v1/transactions/send
- [ ] GET /api/v1/transactions/
- [ ] GET /api/v1/transactions/{id}

### Address/Username
- [ ] POST /api/v1/address/create
- [ ] GET /api/v1/address/my-address
- [ ] PUT /api/v1/address/update
- [ ] POST /api/v1/address/resolve
- [ ] GET /api/v1/address/check-username/{username}
- [ ] DELETE /api/v1/address/delete

### Tokens
- [ ] GET /api/v1/tokens/
- [ ] GET /api/v1/tokens/prices

### Notifications
- [ ] GET /api/v1/notifications/
- [ ] GET /api/v1/notifications/unread/count
- [ ] PATCH /api/v1/notifications/{id}/read
- [ ] PATCH /api/v1/notifications/read-all
- [ ] DELETE /api/v1/notifications/{id}

### User
- [ ] GET /api/v1/users/profile
- [ ] PUT /api/v1/users/profile
- [ ] GET /api/v1/users/pin-status

### Infrastructure
- [ ] WebSocket server for real-time updates
- [ ] Background job processor for transactions
- [ ] Redis caching
- [ ] S3 file uploads
- [ ] Email/SMS integration
- [ ] Push notifications
- [ ] Rate limiting
- [ ] Error logging (Sentry)
- [ ] API documentation (Swagger/Postman)

---

## 📚 Additional Resources

- **Polygon Documentation**: https://docs.polygon.technology/
- **Web3.js**: https://web3js.readthedocs.io/
- **JWT Best Practices**: https://tools.ietf.org/html/rfc8725
- **OWASP API Security**: https://owasp.org/www-project-api-security/

---

**Document Version**: 1.0  
**Last Updated**: October 11, 2025  
**Total Endpoints**: 42  
**Estimated Development Time**: 6 weeks

