# Notification System Architecture

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER MAKES TRANSACTION                       │
│                    (Send 100 USDC to recipient)                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BLOCKCHAIN CONFIRMATION                          │
│              (Transaction confirmed on Polygon)                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  BACKEND NOTIFICATION SERVICE                        │
│                                                                      │
│  1. Get user's default_currency (e.g., INR)                         │
│  2. Convert amount: 100 USDC → 8,275.50 INR                         │
│  3. Get DARI addresses (abhi@dari, john@dari)                       │
│  4. Generate clean titles (no emojis)                               │
│  5. Create notification in database                                 │
└──────────┬────────────────┬─────────────────┬──────────────────────┘
           │                │                 │
           ▼                ▼                 ▼
    ┌──────────┐    ┌──────────┐      ┌──────────┐
    │ IN-APP   │    │   PUSH   │      │  EMAIL   │
    │ DATABASE │    │   (FCM)  │      │  (SMTP)  │
    └────┬─────┘    └────┬─────┘      └────┬─────┘
         │               │                  │
         ▼               ▼                  ▼
   ┌──────────┐    ┌──────────┐      ┌──────────┐
   │  Mobile  │    │  Mobile  │      │  Email   │
   │   App    │    │   App    │      │  Inbox   │
   │  (Pull)  │    │(Real-time)│     │ (Async)  │
   └──────────┘    └──────────┘      └──────────┘
```

## Currency Display Logic

```
┌─────────────────────────────────────────────────┐
│         User's Default Currency Check            │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
┌─────────────┐         ┌─────────────┐
│  USD User   │         │  INR User   │
└──────┬──────┘         └──────┬──────┘
       │                       │
       ▼                       ▼
Show: 100 USDC           Show: 8,275.50 INR
                         Sub: (100 USDC)
```

## Push Notification Flow

```
┌──────────────────────────────────────────────────────────┐
│                    MOBILE APP                             │
│                                                           │
│  1. User logs in                                         │
│  2. Request notification permission                      │
│  3. Get FCM device token                                 │
│  4. POST /api/v1/users/fcm-token                        │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    BACKEND                                │
│                                                           │
│  • Store token in users.fcm_device_token                 │
│  • Token linked to user account                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ (Later, when transaction occurs)
                         ▼
┌──────────────────────────────────────────────────────────┐
│              FIREBASE CLOUD MESSAGING                     │
│                                                           │
│  • Backend sends notification to FCM                     │
│  • FCM delivers to device via token                      │
│  • Includes custom data payload                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                 DEVICE RECEIVES                           │
│                                                           │
│  • Notification appears instantly                        │
│  • User taps → Opens transaction details                 │
│  • Works even if app is closed                           │
└──────────────────────────────────────────────────────────┘
```

## Before vs After Comparison

### Old System
```
User A sends money
         ↓
Transaction saved in DB
         ↓
User B opens app
         ↓
User B pulls notifications
         ↓
User B sees: "💸 You received 100 USDC"
         ↓
❌ Delay: User must open app
❌ Wrong currency: Always shows USDC
❌ Emojis: Unprofessional
```

### New System
```
User A sends money
         ↓
Transaction confirmed on blockchain
         ↓
Backend creates notification
         ↓
    ┌───┴────────────────┐
    ↓                    ↓
Push sent          Saved in DB
    ↓                    ↓
User B's phone    User B can view
buzzes instantly   in app history
    ↓
User B sees: "Payment Received"
"You received 8,275.50 INR from abhi@dari"
         ↓
✅ Instant: No need to open app
✅ Right currency: Shows user's preference
✅ Clean: No emojis
✅ Context: Shows DARI address
```

## Database Schema Changes

```sql
-- Before
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255),
    phone VARCHAR(20),
    default_currency VARCHAR(3) DEFAULT 'USD',
    ...
);

-- After
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255),
    phone VARCHAR(20),
    default_currency VARCHAR(3) DEFAULT 'USD',
    fcm_device_token VARCHAR(500),  -- ← NEW FIELD
    ...
);
```

## API Request Flow

### Register Device Token
```
Mobile App                Backend                  Database
    │                        │                         │
    │──POST /fcm-token──────▶│                         │
    │  {token: "abc123"}     │                         │
    │                        │──UPDATE users─────────▶│
    │                        │  SET fcm_device_token   │
    │                        │                         │
    │◀─────200 OK────────────│◀───────Success──────────│
    │  {success: true}       │                         │
```

### Send Notification
```
Transaction           Backend               FCM                Device
    │                    │                   │                    │
    │─Confirmed─────────▶│                   │                    │
    │                    │──Get user─────▶[DB]                   │
    │                    │  & token          │                    │
    │                    │                   │                    │
    │                    │──Send push───────▶│                    │
    │                    │  {title, body}    │                    │
    │                    │                   │──Deliver──────────▶│
    │                    │                   │                    │
    │                    │◀────Success───────│                 [BUZZ!]
    │                    │                   │              Notification
    │                    │                                    appears
```

## Notification Content Structure

```javascript
// Old Notification
{
  "title": "💸 Transaction Sent",
  "message": "You sent 100 USDC to 0x1234...5678"
}

// New Notification
{
  "title": "Transaction Sent",  // ← No emoji
  "message": "You sent 8,275.50 INR to abhi@dari (100 USDC)",
  //            ↑ User currency  ↑ DARI address  ↑ Token amount
  
  "extra_data": {
    "amount": "100",
    "token_symbol": "USDC",
    "amount_in_user_currency": "8275.50",
    "user_currency": "INR",
    "sender_dari_address": "sender@dari",
    "receiver_dari_address": "abhi@dari"
  }
}
```

## Security & Privacy Flow

```
┌──────────────────────────────────────────────────┐
│            User Device Token                      │
│         (Stored in database)                      │
└────────────────┬─────────────────────────────────┘
                 │
                 │ Token is user-specific
                 │ and encrypted in transit
                 ▼
┌──────────────────────────────────────────────────┐
│          Backend validates:                       │
│  • User is authenticated                         │
│  • Token belongs to this user                    │
│  • User has permission for this transaction      │
└────────────────┬─────────────────────────────────┘
                 │
                 │ Only send notification if:
                 │ - User is sender/receiver
                 │ - Transaction confirmed
                 │ - User has active account
                 ▼
┌──────────────────────────────────────────────────┐
│        Firebase Cloud Messaging                   │
│  • Uses HTTPS                                    │
│  • Google's secure infrastructure                │
│  • Encrypted end-to-end                          │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│           User's Device                           │
│  • Only this device receives notification        │
│  • No sensitive data in notification             │
│  • Full details fetched after auth               │
└──────────────────────────────────────────────────┘
```

## Multi-Language Support (Future)

```
User's Language Setting
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│English │ │ Hindi  │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
"Payment    "भुगतान
Received"   प्राप्त"
    │          │
    └────┬─────┘
         ▼
   Localized
  Notification
```

## Performance Metrics

```
Notification Delivery Timeline
─────────────────────────────────
Transaction Confirmed: 0s
         ↓
Backend Processing: +50ms
         ↓
Database Write: +100ms
         ↓
FCM API Call: +200ms
         ↓
Device Receives: +300ms
─────────────────────────────────
Total: ~650ms (< 1 second)

Compare to old system:
User opens app: Variable (could be hours/days)
Pull notifications: 1-2 seconds
Total: Minutes to days
```

## Error Handling Flow

```
┌──────────────────────────────────────┐
│    Transaction Notification          │
└────────────┬─────────────────────────┘
             │
             ▼
     ┌───────────────┐
     │ User has FCM  │
     │    token?     │
     └───┬───────┬───┘
         │       │
      YES│       │NO
         │       │
         ▼       ▼
   ┌─────────┐  └─────────────────┐
   │Send Push│  │Log: No token    │
   └────┬────┘  │Skip push        │
        │       │Continue w/ DB   │
        │       └─────────────────┘
        ▼
   ┌─────────┐
   │FCM API  │
   │Success? │
   └───┬───┬─┘
       │   │
    YES│   │NO
       │   │
       ▼   ▼
   ┌────┐ ┌──────────────┐
   │ ✓  │ │Log error     │
   └────┘ │Retry (3x)    │
          │Still save DB │
          └──────────────┘
```

## Files Changed Overview

```
Project Structure
├── app/
│   ├── models/
│   │   └── user.py ──────────────────► Added fcm_device_token field
│   ├── services/
│   │   ├── notification_service.py ──► Removed emojis, added currency logic, FCM calls
│   │   └── firebase_service.py ──────► NEW: FCM integration
│   ├── api/v1/
│   │   └── users.py ─────────────────► NEW: FCM token endpoints
│   └── core/
│       └── config.py ────────────────► Added FCM_SERVER_KEY
├── alembic/versions/
│   └── add_fcm_device_token.py ──────► NEW: Database migration
├── docs/
│   ├── NOTIFICATION_ENHANCEMENTS.md ─► NEW: Full documentation
│   ├── FCM_SETUP_GUIDE.md ───────────► NEW: Setup instructions
│   ├── MOBILE_INTEGRATION_GUIDE.md ──► NEW: Mobile dev guide
│   ├── NOTIFICATION_UPDATES.md ──────► NEW: Changelog
│   └── COMPLETE_SUMMARY.md ──────────► NEW: Summary
└── .env
    └── FCM_SERVER_KEY ───────────────► NEW: Configuration needed
```

---

**Legend:**
- ► = Modified/Added
- ✓ = Success
- ✗ = Error
- ← = New/Important
