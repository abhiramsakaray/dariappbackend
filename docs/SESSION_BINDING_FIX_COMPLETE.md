# Session Binding Fix - Complete

## Overview
Fixed DetachedInstanceError issues across the codebase caused by accessing SQLAlchemy model attributes on objects not bound to an active database session.

## Root Cause
When User objects are created from JWT tokens in the `get_current_user` dependency, they are detached from any database session. Accessing lazy-loaded attributes on these detached objects causes `DetachedInstanceError`.

## Solution Pattern

### The Fix
Always refresh the user from the database before accessing any attributes:

```python
@router.post("/some-endpoint")
async def endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)  # ← Add database session
):
    # Refresh user from database
    from app.crud import user as user_crud
    refreshed_user = await user_crud.get_user_by_id(db, current_user.id)
    
    if not refreshed_user:
        raise HTTPException(404, detail="User not found")
    
    # Now safe to access attributes
    if not refreshed_user.pin_hash:  # ← Use refreshed_user
        raise HTTPException(400, detail="PIN not set")
    
    # ... rest of logic
```

## Fixed Endpoints

### 1. `get_current_active_user` Dependency (security.py)
- **Location**: `app/core/security.py` lines 203-242
- **Issue**: Accessing `current_user.is_active` on detached object
- **Fix**: Added `db` parameter, refresh user before accessing attributes
- **Impact**: All endpoints using `Depends(get_current_active_user)` are now safe

### 2. `verify_pin_endpoint` (auth.py)
- **Location**: `app/api/v1/auth.py` lines 433-460
- **Issue**: Accessing `current_user.pin_hash` on detached object
- **Fix**: Added `db` parameter, refresh user before accessing `pin_hash`
- **Impact**: PIN verification now works without errors

## Safe Endpoints

These endpoints use `get_current_active_user` which already handles session binding:
- `GET /api/v1/users/profile` - Uses refreshed user from dependency
- `PUT /api/v1/users/profile` - Uses refreshed user from dependency
- `GET /api/v1/users/pin-status` - Uses refreshed user from dependency

## Eager Loading Improvements

### User CRUD (user.py)
Added eager loading of relationships to prevent lazy load errors:

```python
async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.address_resolver))  # ← Eager load
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

**Benefits:**
- Prevents MissingGreenlet errors
- Loads address_resolver in single query
- Enables access to `user.address_resolver.full_address` (DARI addresses)

## Best Practices

### When to Use Each Dependency

1. **Use `get_current_active_user`** (preferred):
   - For most endpoints
   - Automatically refreshes user
   - Checks if user is active
   - Handles session binding
   ```python
   current_user: User = Depends(get_current_active_user)
   # No need to add db or refresh - already done
   ```

2. **Use `get_current_user`** (only when necessary):
   - When you need to allow inactive users
   - When you're manually handling the user check
   - **Always add db parameter and refresh**
   ```python
   current_user: User = Depends(get_current_user),
   db: AsyncSession = Depends(get_db)
   # Must refresh user manually
   ```

### Developer Guidelines

1. **Always prefer `get_current_active_user`** - it handles session binding automatically
2. **If using `get_current_user`** - always add `db` parameter and refresh
3. **Never access user attributes directly** on detached objects
4. **Use eager loading** for relationships (selectinload)
5. **Test after changes** - check for DetachedInstanceError in logs

## Error Signatures

### DetachedInstanceError
```
sqlalchemy.orm.exc.DetachedInstanceError: Instance <User at 0x...> is not bound to a Session
```
**Solution**: Add db parameter and refresh user

### MissingGreenlet
```
greenlet_spawn has not been called; can't call await_only() here
```
**Solution**: Add eager loading with selectinload()

## Testing

### Verify Fix
1. Call endpoint that was failing
2. Check logs for no DetachedInstanceError
3. Verify response is successful

### Example: PIN Verification
```bash
# Should now work without errors
curl -X POST https://api.dari.com/api/v1/auth/verify-pin \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pin": "1234"}'
```

Expected response:
```json
{
  "success": true,
  "message": "PIN verified",
  "data": {
    "verified": true
  }
}
```

## Related Issues Fixed

1. ✅ Transaction privacy display (DARI addresses)
2. ✅ Relayer transaction filtering
3. ✅ Connection pool disposal on startup
4. ✅ Eager loading of address_resolver
5. ✅ Session binding in auth endpoints

## Files Modified

- `app/core/security.py` - get_current_active_user dependency
- `app/api/v1/auth.py` - verify_pin_endpoint
- `app/crud/user.py` - Added eager loading
- `app/api/v1/transactions.py` - Privacy features

## Next Steps

1. Monitor error logs for any remaining DetachedInstanceError issues
2. Test all auth endpoints from mobile app
3. Verify transaction privacy display shows DARI addresses
4. Document this pattern in developer onboarding guide

## Conclusion

The session binding issues have been systematically resolved by:
1. Refreshing user objects from database before accessing attributes
2. Adding eager loading to prevent lazy load errors
3. Using `get_current_active_user` dependency by default
4. Following consistent pattern across all endpoints

This ensures reliable database access and prevents detached instance errors.
