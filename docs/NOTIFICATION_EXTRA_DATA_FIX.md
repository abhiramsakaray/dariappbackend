# Notification Extra Data Fix

## Issue
The notifications endpoint was returning 500 errors with a Pydantic validation error:

```
ValidationError: 1 validation error for NotificationResponse
extra_data
  Input should be a valid dictionary [type=dict_type, input_value='{"transaction_hash": "",...', input_type=str]
```

## Root Cause

**Database Storage vs. API Response Mismatch:**

1. **In Database**: `extra_data` is stored as `Text` column (JSON string)
   ```python
   # app/models/notification.py
   extra_data = Column(Text, nullable=True)  # JSON string
   ```

2. **In Pydantic Schema**: `extra_data` expects a Python dict
   ```python
   # app/schemas/notification.py
   extra_data: Optional[Dict[str, Any]] = None
   ```

3. **The Problem**: When fetching from database, we were passing the JSON string directly to Pydantic:
   ```python
   NotificationResponse(
       ...
       extra_data=notification.extra_data,  # ← This is a JSON string!
       ...
   )
   ```

## Solution

Added a helper function to parse the JSON string before creating the Pydantic response:

```python
def parse_extra_data(extra_data):
    """Parse extra_data from JSON string to dict"""
    if extra_data is None:
        return None
    if isinstance(extra_data, dict):
        return extra_data
    if isinstance(extra_data, str):
        try:
            return json.loads(extra_data)
        except (json.JSONDecodeError, ValueError):
            return None
    return None
```

## Fixed Endpoints

### 1. GET /api/v1/notifications/
**Before:**
```python
NotificationResponse(
    ...
    extra_data=notification.extra_data,  # JSON string - causes error
    ...
)
```

**After:**
```python
NotificationResponse(
    ...
    extra_data=parse_extra_data(notification.extra_data),  # Parsed dict
    ...
)
```

### 2. PATCH /api/v1/notifications/{notification_id}/read
**Before:**
```python
return NotificationResponse(
    ...
    extra_data=notification.extra_data,  # JSON string - causes error
    ...
)
```

**After:**
```python
return NotificationResponse(
    ...
    extra_data=parse_extra_data(notification.extra_data),  # Parsed dict
    ...
)
```

## Data Flow

### Creating Notifications (Already Correct)
```python
# CRUD layer converts dict → JSON string for storage
extra_data_json = None
if notification_data.extra_data:
    extra_data_json = json.dumps(notification_data.extra_data)

db_notification = Notification(
    ...
    extra_data=extra_data_json,  # Stored as JSON string
    ...
)
```

### Retrieving Notifications (Now Fixed)
```python
# API layer converts JSON string → dict for response
NotificationResponse(
    ...
    extra_data=parse_extra_data(notification.extra_data),  # Parsed back to dict
    ...
)
```

## Files Modified

- `app/api/v1/notifications.py`:
  - Added `import json`
  - Added `parse_extra_data()` helper function
  - Updated GET `/` endpoint to parse extra_data
  - Updated PATCH `/{notification_id}/read` endpoint to parse extra_data

## Testing

### Verify Fix
```bash
# Get notifications - should now return 200 with parsed extra_data
curl -X GET "https://api.dari.com/api/v1/notifications/?page=1&per_page=50" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "notifications": [
    {
      "id": 1,
      "type": "transaction_received",
      "extra_data": {
        "transaction_hash": "0x...",
        "amount": "100.00",
        "timestamp": "2025-10-14T18:21:25.693538+00:00"
      }
    }
  ],
  "total_count": 1,
  "page": 1,
  "per_page": 50
}
```

### Mark as Read
```bash
curl -X PATCH "https://api.dari.com/api/v1/notifications/1/read" \
  -H "Authorization: Bearer $TOKEN"
```

Expected: 200 OK with parsed extra_data as dict

## Prevention

### Guidelines for JSON Column Handling

When working with JSON columns stored as TEXT:

1. **Storage (CRUD layer)**: Convert dict → JSON string
   ```python
   extra_data_json = json.dumps(data_dict) if data_dict else None
   ```

2. **Retrieval (API layer)**: Convert JSON string → dict
   ```python
   extra_data = json.loads(json_string) if json_string else None
   ```

3. **Pydantic Models**: Always use `Dict[str, Any]` type
   ```python
   extra_data: Optional[Dict[str, Any]] = None
   ```

4. **Database Models**: Use `Text` or `JSON` column type
   ```python
   extra_data = Column(Text, nullable=True)
   # or
   extra_data = Column(JSON, nullable=True)  # PostgreSQL JSON type
   ```

### Alternative Solutions

**Option 1: Use PostgreSQL JSON Column Type**
```python
# In model
from sqlalchemy.dialects.postgresql import JSON
extra_data = Column(JSON, nullable=True)
```
- Pros: SQLAlchemy automatically handles JSON serialization
- Cons: Database-specific (PostgreSQL)

**Option 2: Custom Pydantic Validator**
```python
from pydantic import field_validator
import json

class NotificationResponse(BaseModel):
    extra_data: Optional[Dict[str, Any]] = None
    
    @field_validator('extra_data', mode='before')
    @classmethod
    def parse_extra_data(cls, v):
        if isinstance(v, str):
            return json.loads(v) if v else None
        return v
```
- Pros: Validation happens at schema level
- Cons: Less explicit, harder to debug

**Current Solution (Helper Function)**
- ✅ Explicit and easy to understand
- ✅ Database-agnostic
- ✅ Easy to debug
- ✅ Reusable across endpoints

## Related Issues

This fix complements other session binding fixes:
- ✅ Session binding in auth endpoints
- ✅ Transaction privacy display
- ✅ Notification extra_data parsing
- ✅ Eager loading of relationships

## Conclusion

The notification endpoints now correctly parse JSON strings from the database into Python dictionaries before passing them to Pydantic models. This ensures compatibility between database storage format (TEXT/JSON string) and API response format (dict).
