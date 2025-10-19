# Relayer Status Endpoint

**Date:** October 13, 2025  
**Feature:** Relayer wallet monitoring for gasless transactions  
**Endpoint:** `GET /api/v1/transactions/relayer/status`  
**Status:** ✅ IMPLEMENTED

---

## 📋 Overview

This endpoint provides real-time monitoring of the relayer wallet used for sponsoring gasless transactions. It helps administrators track the relayer's MATIC balance and plan refills before running out.

---

## 🔗 Endpoint Details

### Request

```http
GET /api/v1/transactions/relayer/status
Authorization: Bearer <access_token>
```

**Authentication:** Required (any authenticated user)

**Parameters:** None

### Response (Success)

```json
{
  "enabled": true,
  "relayer_address": "0x3e1ac401EB1d85D8D9d337F838E514eCE552313C",
  "matic_balance": 0.168115445295371264,
  "matic_balance_formatted": "0.168115 MATIC",
  "estimated_transactions_remaining": 37,
  "average_gas_cost_matic": 0.0045,
  "average_gas_cost_formatted": "0.0045 MATIC",
  "status": "funded",
  "status_message": "✅ Relayer is well funded",
  "recommendations": [],
  "network": "Polygon Amoy Testnet",
  "timestamp": 1697232000.123
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Whether gasless transactions are enabled |
| `relayer_address` | string | The relayer wallet address |
| `matic_balance` | number | Current MATIC balance (decimal) |
| `matic_balance_formatted` | string | Human-readable balance with units |
| `estimated_transactions_remaining` | integer | Number of transactions that can be sponsored |
| `average_gas_cost_matic` | number | Average gas cost per transaction |
| `average_gas_cost_formatted` | string | Human-readable gas cost |
| `status` | string | `funded`, `low`, `critical`, or `empty` |
| `status_message` | string | Human-readable status description |
| `recommendations` | array | List of recommended actions |
| `network` | string | Blockchain network being used |
| `timestamp` | number | Unix timestamp of the check |

---

## 🚦 Status Levels

### 1. **Funded** (✅ Green)
- **Balance:** ≥ 0.1 MATIC
- **Transactions:** 22+ remaining
- **Action:** None required
- **Message:** "✅ Relayer is well funded"

### 2. **Low** (⚠️ Yellow)
- **Balance:** 0.05 - 0.1 MATIC
- **Transactions:** 11-22 remaining
- **Action:** Plan to refill soon
- **Message:** "⚠️ Relayer balance is low"
- **Recommendations:**
  - "Consider refilling the relayer wallet soon"
  - "Current balance can sponsor ~X more transactions"

### 3. **Critical** (🔴 Orange)
- **Balance:** 0.01 - 0.05 MATIC
- **Transactions:** 2-11 remaining
- **Action:** Refill immediately
- **Message:** "🔴 Relayer balance is critically low"
- **Recommendations:**
  - "⚠️ URGENT: Refill the relayer wallet immediately"
  - "Only X transactions remaining"
  - "Gasless transactions will fail when balance reaches 0"

### 4. **Empty** (❌ Red)
- **Balance:** < 0.01 MATIC
- **Transactions:** 0-2 remaining
- **Action:** Refill NOW - service failing
- **Message:** "❌ Relayer wallet is empty or nearly empty"
- **Recommendations:**
  - "🚨 CRITICAL: Refill the relayer wallet NOW"
  - "Gasless transactions are failing or will fail soon"
  - "Users cannot send transactions without MATIC"

---

## 📊 Gas Cost Calculation

### Formula
```
Estimated TX Remaining = MATIC Balance / Average Gas Cost
```

### Gas Breakdown (Per Transaction)
```
1. MATIC Transfer to User:
   - Gas Used: ~21,000 gas
   - Gas Price: ~50 Gwei (0.00000005 MATIC)
   - Cost: ~0.00105 MATIC

2. Token Transfer by User:
   - Gas Used: ~65,000 gas
   - Gas Price: ~50 Gwei (0.00000005 MATIC)
   - Cost: ~0.00325 MATIC

3. Total Cost per Gasless TX:
   - Combined: ~86,000 gas
   - Total: ~0.0043 MATIC
   - Conservative Estimate: 0.0045 MATIC
```

### Current Costs (Polygon Amoy Testnet)
- **Gas Price:** 50 Gwei average
- **MATIC Transfer:** ~0.00105 MATIC
- **Token Transfer:** ~0.00325 MATIC
- **Total per TX:** ~0.0045 MATIC
- **1 MATIC sponsors:** ~222 transactions

---

## 🧪 Testing

### Test 1: Check Relayer Status
```bash
curl -X GET "http://localhost:8000/api/v1/transactions/relayer/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "enabled": true,
  "relayer_address": "0x3e1a...",
  "matic_balance": 0.168,
  "status": "funded",
  "estimated_transactions_remaining": 37
}
```

### Test 2: When Gasless Disabled
```bash
# Set ENABLE_GASLESS=false in .env
curl -X GET "http://localhost:8000/api/v1/transactions/relayer/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response:**
```json
{
  "enabled": false,
  "status": "disabled",
  "message": "Gasless transactions are disabled"
}
```

### Test 3: Monitor Over Time
```python
import requests
import time

def check_relayer():
    response = requests.get(
        "http://localhost:8000/api/v1/transactions/relayer/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()
    print(f"Balance: {data['matic_balance']} MATIC")
    print(f"Status: {data['status']}")
    print(f"TX Remaining: {data['estimated_transactions_remaining']}")

# Check every 5 minutes
while True:
    check_relayer()
    time.sleep(300)
```

---

## 🔔 Monitoring & Alerts

### Recommended Monitoring Setup

1. **Check Frequency:**
   - Production: Every 5 minutes
   - Development: Every hour

2. **Alert Thresholds:**
   - **Low (0.05 MATIC):** Email notification
   - **Critical (0.01 MATIC):** SMS/Slack alert
   - **Empty (0 MATIC):** Immediate escalation

3. **Grafana Dashboard:**
   ```promql
   # Example Prometheus metrics
   relayer_matic_balance
   relayer_transactions_remaining
   relayer_status_level
   ```

### Sample Alert Script
```python
import requests
import os

def check_and_alert():
    response = requests.get(
        f"{os.getenv('API_URL')}/api/v1/transactions/relayer/status",
        headers={"Authorization": f"Bearer {os.getenv('ADMIN_TOKEN')}"}
    )
    
    data = response.json()
    status = data.get('status')
    
    if status == 'critical':
        send_email_alert(data)
        send_slack_alert(data)
    elif status == 'empty':
        send_sms_alert(data)
        send_slack_alert(data, urgent=True)
    elif status == 'low':
        send_email_alert(data)
    
    return data

# Run in cron job: */5 * * * * python check_relayer.py
```

---

## 💰 Refill Process

### When to Refill
- **Recommended:** When balance < 0.1 MATIC
- **Urgent:** When balance < 0.05 MATIC
- **Critical:** When balance < 0.01 MATIC

### How to Refill

1. **Get Relayer Address:**
   ```bash
   curl http://localhost:8000/api/v1/transactions/relayer/status
   # Note the "relayer_address" field
   ```

2. **Send MATIC (Testnet):**
   - Use Polygon Amoy Faucet: https://faucet.polygon.technology/
   - Or transfer from another wallet

3. **Send MATIC (Mainnet):**
   - Use MetaMask or any wallet
   - Send to relayer address
   - Recommended amount: 1-5 MATIC

4. **Verify Refill:**
   ```bash
   curl http://localhost:8000/api/v1/transactions/relayer/status
   # Check "matic_balance" and "status" fields
   ```

### Refill Costs (Mainnet Estimates)
- **1 MATIC:** ~$0.90 USD → ~222 transactions
- **5 MATIC:** ~$4.50 USD → ~1,111 transactions
- **10 MATIC:** ~$9.00 USD → ~2,222 transactions

---

## 🔒 Security Considerations

### Access Control
- ✅ Endpoint requires authentication
- ✅ Any authenticated user can check status
- ⚠️ Consider restricting to admin users only

### Sensitive Information
- ✅ Relayer address is public (on blockchain)
- ✅ Balance is public (on blockchain)
- ✅ No private keys exposed
- ✅ No sensitive configuration exposed

### Rate Limiting
```python
# Add rate limiting for non-admin users
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/relayer/status")
@limiter.limit("10/minute")  # 10 requests per minute
async def get_relayer_status(...):
    ...
```

---

## 📱 Frontend Integration

### React/React Native Example
```typescript
interface RelayerStatus {
  enabled: boolean;
  relayer_address: string;
  matic_balance: number;
  matic_balance_formatted: string;
  estimated_transactions_remaining: number;
  status: 'funded' | 'low' | 'critical' | 'empty';
  status_message: string;
  recommendations: string[];
}

async function getRelayerStatus(): Promise<RelayerStatus> {
  const response = await fetch(
    `${API_URL}/api/v1/transactions/relayer/status`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  return response.json();
}

// Usage in component
function RelayerStatusCard() {
  const [status, setStatus] = useState<RelayerStatus | null>(null);
  
  useEffect(() => {
    getRelayerStatus().then(setStatus);
    
    // Poll every 5 minutes
    const interval = setInterval(() => {
      getRelayerStatus().then(setStatus);
    }, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  if (!status?.enabled) return null;
  
  return (
    <div className={`status-card status-${status.status}`}>
      <h3>Relayer Status</h3>
      <p>{status.status_message}</p>
      <p>Balance: {status.matic_balance_formatted}</p>
      <p>TX Remaining: {status.estimated_transactions_remaining}</p>
      {status.recommendations.length > 0 && (
        <ul>
          {status.recommendations.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

## 🐛 Troubleshooting

### Issue: "Relayer address not configured"
**Solution:** Set `RELAYER_ADDRESS` in `.env` file

### Issue: "Gasless transactions are disabled"
**Solution:** Set `ENABLE_GASLESS=true` in `.env` file

### Issue: Balance shows 0 but wallet has MATIC
**Solution:** 
- Check RPC connection to Polygon network
- Verify correct network (testnet vs mainnet)
- Check relayer address is correct

### Issue: Estimated transactions don't match reality
**Solution:**
- Gas prices fluctuate - estimates are conservative
- Actual cost may vary ±20% based on network congestion
- Update `avg_gas_cost` in code if consistently off

---

## 📝 Related Files

- **Endpoint:** `app/api/v1/transactions.py` - Lines 771-792
- **Service:** `app/services/blockchain_service.py` - Lines 1320-1440
- **Test Script:** `test_relayer.py` - Standalone diagnostics
- **Documentation:** `docs/GASLESS_TRANSACTIONS.md` - Gasless system overview

---

## ✅ Verification Checklist

- [x] Endpoint created and documented
- [x] Service function implemented
- [x] Status levels defined (funded/low/critical/empty)
- [x] Gas cost calculations accurate
- [x] Recommendations logic working
- [x] Error handling implemented
- [x] Authentication required
- [x] Response format documented
- [x] Testing instructions provided
- [x] Monitoring recommendations included
- [x] Frontend integration example provided
- [x] Syntax validated (compilation successful)

---

**Status:** 🟢 Production Ready

Monitor your relayer wallet status in real-time! 📊
