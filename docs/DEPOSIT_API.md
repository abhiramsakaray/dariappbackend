# USDC Deposit API Documentation

## Overview

The Deposit API allows users to deposit USDC into their DARI wallet through a relayer-based system. Users can deposit from any exchange or wallet by scanning a QR code.

## How It Works

### Deposit Flow

```
1. User → Request Deposit
   ↓
2. Backend → Generate QR Code (Relayer Address + Amount)
   ↓
3. User → Scan QR in Exchange/Wallet App
   ↓
4. User → Send USDC to Relayer Address
   ↓
5. Backend → Monitor Relayer Wallet (Every 30s)
   ↓
6. Backend → Detect Incoming USDC
   ↓
7. Backend → Transfer USDC to User's Wallet
   ↓
8. User → Receives USDC in DARI Wallet
```

### Key Features

- **10-Minute Timeout**: Deposit requests expire after 10 minutes
- **Automatic Processing**: Background service monitors and processes deposits
- **Status Tracking**: Real-time status updates
- **Secure**: Uses relayer wallet as intermediary
- **Exchange-Friendly**: Works with any wallet/exchange that supports Polygon USDC

## API Endpoints

### 1. Create Deposit Request

**POST** `/api/v1/deposits/create`

Creates a new deposit request and returns QR code data.

**Request Body:**
```json
{
  "amount": 100
}
```

**Response:**
```json
{
  "deposit_id": "DEP-20251012120000-A1B2C3D4",
  "relayer_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "amount": "100",
  "token": "USDC",
  "status": "pending",
  "expires_at": "2025-10-12T12:10:00Z",
  "qr_data": {
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "amount": "100",
    "token": "USDC",
    "network": "Polygon",
    "deposit_id": "DEP-20251012120000-A1B2C3D4",
    "chain_id": 137
  },
  "time_remaining_seconds": 600
}
```

**QR Code Data:**
- `address`: Relayer wallet address (where to send USDC)
- `amount`: Amount to deposit
- `token`: USDC
- `network`: Polygon
- `chain_id`: 137 (Polygon Mainnet)
- `deposit_id`: Unique identifier for tracking

### 2. Check Deposit Status

**GET** `/api/v1/deposits/{deposit_id}`

Check the status of a deposit request.

**Response:**
```json
{
  "deposit_id": "DEP-20251012120000-A1B2C3D4",
  "status": "completed",
  "amount": "100",
  "received_amount": "100",
  "transferred_amount": "100",
  "deposit_tx_hash": "0xabc...123",
  "transfer_tx_hash": "0xdef...456",
  "created_at": "2025-10-12T12:00:00Z",
  "expires_at": "2025-10-12T12:10:00Z",
  "received_at": "2025-10-12T12:02:30Z",
  "completed_at": "2025-10-12T12:03:00Z",
  "time_remaining_seconds": null,
  "error_message": null
}
```

**Status Values:**
- `pending`: Waiting for user to send USDC to relayer
- `received`: Relayer received USDC, processing transfer
- `processing`: Transferring USDC to user wallet
- `completed`: USDC successfully transferred to user
- `expired`: 10-minute timeout expired without receiving funds
- `failed`: Transfer failed (check `error_message`)

### 3. List User Deposits

**GET** `/api/v1/deposits/`

Get list of all deposit requests for the authenticated user.

**Query Parameters:**
- `limit` (optional, default=10): Number of results
- `offset` (optional, default=0): Pagination offset

**Response:**
```json
{
  "deposits": [
    {
      "deposit_id": "DEP-20251012120000-A1B2C3D4",
      "status": "completed",
      "amount": "100",
      ...
    }
  ],
  "total_count": 5
}
```

## Frontend Integration

### Step 1: Create Deposit Request

```javascript
const response = await fetch('/api/v1/deposits/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ amount: 100 })
});

const data = await response.json();
```

### Step 2: Generate QR Code

```javascript
// Use qr_data from response
const qrData = JSON.stringify(data.qr_data);

// Generate QR code using a library like qrcode.react
<QRCode value={qrData} size={256} />
```

### Step 3: Display Instructions

```javascript
<div>
  <h3>Deposit USDC</h3>
  <p>Scan this QR code in your exchange or wallet app</p>
  <QRCode value={qrData} />
  
  <div>
    <p>Or send manually:</p>
    <p>Address: {data.relayer_address}</p>
    <p>Amount: {data.amount} USDC</p>
    <p>Network: Polygon</p>
  </div>
  
  <p>Time remaining: {Math.floor(data.time_remaining_seconds / 60)}:{data.time_remaining_seconds % 60}</p>
</div>
```

### Step 4: Poll for Status

```javascript
const pollInterval = setInterval(async () => {
  const status = await fetch(`/api/v1/deposits/${depositId}`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  
  const statusData = await status.json();
  
  if (statusData.status === 'completed') {
    // Show success message
    clearInterval(pollInterval);
  } else if (statusData.status === 'expired' || statusData.status === 'failed') {
    // Show error message
    clearInterval(pollInterval);
  }
}, 5000); // Poll every 5 seconds
```

## Background Processing

### Deposit Monitor Service

The backend runs a background service that:

1. **Monitors Pending Deposits** (every 30 seconds)
   - Checks relayer wallet for incoming USDC transactions
   - Marks deposits as "received" when funds arrive

2. **Processes Received Deposits**
   - Transfers USDC from relayer to user wallet
   - Updates status to "completed"
   - Records transaction hashes

3. **Expires Old Deposits**
   - Marks deposits as "expired" after 10 minutes
   - Prevents stale requests from processing

### Celery Task

```python
# Auto-scheduled task runs every 30 seconds
@celery_app.task(name="monitor_deposits")
def monitor_deposits_task():
    asyncio.run(deposit_monitor_service.monitor_deposits())
```

## Database Schema

### deposit_requests Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | User who created request |
| user_wallet_address | String(42) | User's wallet address |
| deposit_id | String(50) | Unique deposit identifier |
| amount | Numeric | Expected USDC amount |
| token | String(10) | Token symbol (USDC) |
| relayer_address | String(42) | Relayer wallet address |
| status | Enum | Current status |
| deposit_tx_hash | String(66) | User → Relayer tx hash |
| transfer_tx_hash | String(66) | Relayer → User tx hash |
| received_amount | Numeric | Actual amount received |
| transferred_amount | Numeric | Amount sent to user |
| qr_data | Text | JSON QR code data |
| created_at | DateTime | Request creation time |
| expires_at | DateTime | Expiration time (created + 10min) |
| received_at | DateTime | When funds were received |
| completed_at | DateTime | When transfer completed |
| error_message | Text | Error details if failed |
| retry_count | Integer | Number of retry attempts |

## Security Considerations

1. **Relayer Private Key**: Store securely in environment variables
2. **User Verification**: Deposits only processed for authenticated users
3. **Amount Validation**: Verify received amount matches expected amount
4. **Timeout**: 10-minute expiration prevents indefinite pending states
5. **Error Handling**: Failed transfers are logged and can be retried

## Production Recommendations

### 1. Implement Proper Transaction Tracking

The current implementation checks balance changes. For production, implement Web3 event filtering:

```python
# Monitor Transfer events on USDC contract
transfer_filter = usdc_contract.events.Transfer.create_filter(
    from_block='latest',
    argument_filters={'to': relayer_address}
)

for event in transfer_filter.get_all_entries():
    # Process deposit based on event data
    process_deposit_event(event)
```

### 2. Add Transaction Confirmation

Wait for sufficient block confirmations before processing:

```python
# Wait for 12 confirmations (~30 seconds on Polygon)
current_block = w3.eth.block_number
if current_block - tx_block_number >= 12:
    # Process deposit
```

### 3. Implement Retry Logic

Add retry mechanism for failed transfers:

```python
max_retries = 3
if deposit.retry_count < max_retries:
    # Retry transfer
else:
    # Mark as permanently failed, notify admin
```

### 4. Add Notifications

Notify users of deposit status changes:

```python
# On completed
await notification_service.send_notification(
    user_id=deposit.user_id,
    title="Deposit Completed",
    message=f"{deposit.amount} USDC deposited to your wallet"
)
```

### 5. Monitor Relayer Balance

Alert when relayer balance is low:

```python
min_balance = 1000  # Minimum USDC
if relayer_balance < min_balance:
    # Alert admin to refill relayer
```

## Testing

### Manual Testing Steps

1. **Create Deposit**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/deposits/create \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"amount": 100}'
   ```

2. **Send USDC to Relayer** (using MetaMask or exchange)

3. **Check Status**:
   ```bash
   curl http://localhost:8000/api/v1/deposits/DEP-xxx \
     -H "Authorization: Bearer <token>"
   ```

4. **Verify in Wallet**:
   ```bash
   curl http://localhost:8000/api/v1/wallets/balance \
     -H "Authorization: Bearer <token>"
   ```

## Troubleshooting

### Deposit Stuck in "pending"

- Check relayer wallet balance on PolygonScan
- Verify transaction was sent to correct address
- Check if deposit expired (10 minutes)

### Deposit Failed

- Check `error_message` in status response
- Verify relayer has sufficient MATIC for gas
- Check relayer private key is correct

### Transfer Not Completing

- Verify deposit monitor service is running
- Check Celery worker logs
- Ensure database migrations are applied

## Environment Variables

```env
# Relayer Configuration (from .env)
RELAYER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
RELAYER_PRIVATE_KEY=0x...
ENABLE_GASLESS=true

# Polygon Configuration
POLYGON_RPC_URL=https://polygon-rpc.com
USDC_CONTRACT_ADDRESS=0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
```
