# Bug Fix: SQLAlchemy DetachedInstanceError

**Date:** 2025-11-18
**Status:** ✅ Fixed
**Severity:** Critical (blocked application login)

## Problem

When trying to log in to the application, users encountered a crash with this error:

```
sqlalchemy.orm.exc.DetachedInstanceError: Instance <User at 0x...> is not bound to a Session;
attribute refresh operation cannot proceed
```

**Stack Trace:**
```
File "app/gui/dashboard_widget.py", line 236, in load_user_data
    self.user_label.setText(f"User: {user.username}")
                                     ^^^^^^^^^^^^^
```

## Root Cause

**SQLAlchemy Session Management Issue**

The `authenticate()` method in `app/core/auth.py` was:
1. Opening a database session
2. Querying the User object
3. **Closing the session** in the `finally` block
4. Returning the User object to the GUI

When the database session closes, the User object becomes **"detached"** - it's no longer bound to any SQLAlchemy session. Later, when the GUI tried to access `user.username` or `user.id`, SQLAlchemy attempted to lazy-load these attributes from the database, but **couldn't** because there was no active session.

### Code Before Fix

```python
def authenticate(self, username: str, password: str) -> Optional[User]:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and self.verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            db.commit()
            return user  # ⚠️ User object still attached to session
        return None
    finally:
        db.close()  # ⚠️ Session closed, User becomes detached!
```

When the GUI later accessed `user.username`, the object was already detached.

## Solution

**Eager Loading of Required Attributes**

Before closing the database session, we now explicitly access all attributes that will be needed by the GUI. This forces SQLAlchemy to load them into memory **while the session is still active**.

### Code After Fix

```python
def authenticate(self, username: str, password: str) -> Optional[User]:
    logger.info(f"Authentication attempt for username: {username}")
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.username == username).first()

        if user and self.verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            db.commit()

            # ✅ Eagerly load attributes needed by GUI before session closes
            # This prevents DetachedInstanceError when accessing attributes later
            _ = user.id
            _ = user.username
            _ = user.created_at
            _ = user.last_login

            logger.info(f"Authentication successful for user: {username} (id={user.id})")
            return user

        logger.warning(f"Authentication failed for username: {username}")
        return None

    finally:
        db.close()
```

**What This Does:**
- Accessing `user.id`, `user.username`, etc. forces SQLAlchemy to load these columns
- Once loaded, they're cached in the object's `__dict__`
- After the session closes, these cached values remain accessible
- No lazy-loading is needed when the GUI accesses them later

## Attributes Verified

Scanned the entire `app/gui/` directory for User object attribute access:

| File | Line | Attribute | Status |
|------|------|-----------|--------|
| `dashboard_widget.py` | 236 | `user.username` | ✅ Fixed |
| `dashboard_widget.py` | 250 | `user.id` | ✅ Fixed |
| `workflow_widget.py` | 209 | `user.id` | ✅ Fixed |
| `report_widget.py` | 68 | `user.id` | ✅ Fixed |

All required attributes are now eagerly loaded.

## Additional Improvements

### 1. Added Logging
Enhanced auth module with comprehensive logging:
- Registration attempts (success/failure)
- Authentication attempts (success/failure)
- User IDs for successful logins

**Example log output:**
```
2025-11-18 14:30:12 | INFO | app.core.auth | Authentication attempt for username: admin
2025-11-18 14:30:12 | INFO | app.core.auth | Authentication successful for user: admin (id=1)
```

### 2. Documented the Fix
- Added detailed comments in the code explaining the eager loading
- Created this bug fix documentation for future reference

## Alternative Solutions Considered

### Option A: Keep Session Open (Rejected)
- Keep the database session alive for the entire user session
- **Problem:** Resource leaks, connection pool exhaustion, concurrent access issues

### Option B: Use `expunge()` and `make_transient()` (Rejected)
- Explicitly detach the object and make it transient
- **Problem:** More complex, still requires loading attributes anyway

### Option C: Return a DTO/Dictionary (Rejected)
- Create a separate data class or dict with just the needed data
- **Problem:** Changes many method signatures, more refactoring

### Option D: Eager Loading ✅ **Selected**
- Simple, minimal code changes
- Clear intent with comments
- No architectural changes needed

## Testing

After the fix:
1. ✅ User registration works
2. ✅ User login works
3. ✅ Dashboard loads with `user.username` displayed
4. ✅ Workflows can be started (uses `user.id`)
5. ✅ Reports page loads (uses `user.id`)

## Prevention

**For Future Development:**

When returning SQLAlchemy model objects from functions that close the session:

1. **Document which attributes will be accessed**
2. **Eagerly load those attributes before closing the session**
3. **Add logging to track session lifecycle**
4. **Consider using DTOs for cross-layer data transfer**

**Code Pattern:**
```python
def query_object_and_close_session():
    db = SessionLocal()
    try:
        obj = db.query(Model).first()

        # Eagerly load needed attributes
        _ = obj.required_field_1
        _ = obj.required_field_2

        return obj
    finally:
        db.close()
```

## Related Documentation

- SQLAlchemy Sessions: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- DetachedInstanceError: https://docs.sqlalchemy.org/en/20/errors.html#error-bhk3
- Eager Loading: https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html

## Files Modified

- `app/core/auth.py` - Fixed `authenticate()` method, added logging
- `docs/BUGFIX_DETACHED_USER.md` - This documentation

---

**Lesson Learned:** Always consider SQLAlchemy session lifecycle when passing model objects between layers. Eager loading is a simple solution for single-object scenarios.
