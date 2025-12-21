# Quick Error Prevention Checklist

**Use this before committing code** - 2-minute safety check

---

## ✅ Pre-Commit Checklist

### 1. Dev Bypass (if using auth)

```bash
# Check if both functions have username & email
grep -A 10 "DISABLE_AUTH_IN_DEV" backend/app/core/security.py | grep -E "username|email"
```

Expected: See "username": and "email": in BOTH `get_current_user` and `require_role`

### 2. Database Services (if added new service)

```python
# Pattern MUST include:
try:
    db_pool = async_db.get_pool()
    return RealService(db_pool=db_pool)
except RuntimeError:
    return MockService()  # ⚠️ REQUIRED for E2E tests
```

### 3. WebSocket (if using WebSocket)

```python
# ✅ CORRECT
if websocket.client_state == WebSocketState.CONNECTED:

# ❌ WRONG
if websocket.application_state == WebSocketState.CONNECTED:
```

### 4. Logging Levels (frontend)

```typescript
// Normal disconnection?
console.warn()   // ✅ Use this

// Unexpected error?
console.error()  // ✅ Use this

// NOT
console.error() for everything  // ❌ Fails E2E tests
```

### 5. Variable Names

```python
# Avoid these variable names:
status  # Shadows fastapi.status
datetime  # Shadows datetime module
json  # Shadows json module
os  # Shadows os module

# Use instead:
rate_status, http_status
dt, timestamp
json_data, payload
operating_system, env
```

---

## 🧪 Quick Test Commands

```bash
# 1. E2E Tests (MUST pass with 0 console errors)
cd web-dashboard && npx playwright test kanban-advanced-features.spec.ts

# 2. Rate-limit endpoint (should return 200, not 500)
curl http://localhost:8081/api/kanban/ai/rate-limit

# 3. Backend health
curl http://localhost:8081/api/health
```

---

## 🚨 Red Flags

If you see these, check ERROR_PREVENTION_GUIDE.md:

| Error | Likely Cause | Fix Location |
|-------|--------------|--------------|
| 403 Forbidden | Dev bypass missing | security.py |
| 500 ValidationError | username/email missing | security.py dev bypass |
| WebSocket send fails | Wrong state attribute | kanban_websocket.py |
| E2E console errors | console.error misuse | Frontend .ts files |
| UnboundLocalError | Variable shadowing | Check variable names |

---

## 📄 Full Guide

See: `docs/guides/ERROR_PREVENTION_GUIDE.md`

---

**Time to check**: ~2 minutes
**Errors prevented**: 6 common issues
**Last updated**: 2025-12-22
