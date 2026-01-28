# IntlError Fix Complete - C-K Theory Page

**Date**: 2026-01-07
**Issue**: IntlError on C-K Theory page due to JSON placeholder
**Status**: ✅ **RESOLVED**

---

## Issue Report

**Console Error**:
```
INVALID_MESSAGE: MALFORMED_ARGUMENT ({"budget": "2 weeks", "team_size": 2})
app/ck-theory/page.tsx (256:34)
```

**Error Type**: `IntlError` - i18n message formatting error

**Affected Pages**:
1. ✅ GI Formula page (fixed in previous session)
2. ✅ C-K Theory page (fixed in this session)

---

## Root Cause

**Problem**: i18n messages using JSON objects as placeholders

```json
// BEFORE (BUGGY):
{
  "constraintsPlaceholder": "{\"budget\": \"2 weeks\", \"team_size\": 2}"
}
```

**Why It Fails**: next-intl cannot parse JSON objects embedded in strings as placeholders.

---

## Solution

**Changed JSON placeholder to plain text**:

### Korean (ko.json)
```json
// AFTER (FIXED):
{
  "constraintsPlaceholder": "예시: budget: 2주, team_size: 2, security: high"
}
```

### English (en.json)
```json
// AFTER (FIXED):
{
  "constraintsPlaceholder": "Example: budget: 2 weeks, team_size: 2, security: high"
}
```

---

## Files Modified

1. ✅ `web-dashboard/messages/ko.json` (line 284)
2. ✅ `web-dashboard/messages/en.json` (line 284)

**Changes**:
- Removed escaped JSON format: `{\"budget\": ...}`
- Replaced with plain text: `예시: budget: 2주, ...`
- Added additional example field: `security: high`

---

## Verification Steps

1. **Navigate to C-K Theory page**: http://localhost:3000/ck-theory
2. **Check console**: No IntlError should appear
3. **Verify placeholder text**:
   - Korean: "예시: budget: 2주, team_size: 2, security: high"
   - English: "Example: budget: 2 weeks, team_size: 2, security: high"

---

## Prevention

**Rule**: Never use JSON objects in i18n message placeholders

**Good Examples** ✅:
```json
{
  "placeholder": "Example: key1: value1, key2: value2"
}
```

**Bad Examples** ❌:
```json
{
  "placeholder": "{\"key1\": \"value1\", \"key2\": \"value2\"}"
}
```

---

## Related Fixes

### Session 1 (Previous)
- **File**: GI Formula page
- **Message Key**: `latencyPlaceholder`
- **Before**: `{\"current_latency\": \"200ms\", \"target_latency\": \"100ms\"}`
- **After**: `예: current_latency: 200ms, target_latency: 100ms`

### Session 2 (Current)
- **File**: C-K Theory page
- **Message Key**: `constraintsPlaceholder`
- **Before**: `{\"budget\": \"2주\", \"team_size\": 2}`
- **After**: `예시: budget: 2주, team_size: 2, security: high`

---

## Impact

**Before Fix**:
- ❌ Console errors on C-K Theory page
- ❌ Placeholder not rendering correctly
- ❌ User sees error overlay

**After Fix**:
- ✅ No console errors
- ✅ Placeholder renders as plain text
- ✅ Clean user experience

---

## All IntlError Issues (Complete Status)

| Page | Message Key | Status | Session |
|------|-------------|--------|---------|
| GI Formula | `latencyPlaceholder` | ✅ Fixed | Previous |
| C-K Theory | `constraintsPlaceholder` | ✅ Fixed | Current |
| Other pages | N/A | ✅ Verified (no JSON placeholders) | Current |

**Total IntlErrors Fixed**: 2
**Total Pages Affected**: 2
**Total Messages Modified**: 4 (2 keys × 2 languages)

---

## Summary

| Item | Status |
|------|--------|
| **Issue Identified** | ✅ Complete |
| **Root Cause Found** | ✅ Complete (JSON placeholders) |
| **Fix Applied** | ✅ Complete (2 files) |
| **Verification** | ✅ Complete (no more JSON placeholders) |
| **Prevention Rule** | ✅ Documented |

**Resolution**: All IntlErrors caused by JSON placeholders have been eliminated.

---

**Last Updated**: 2026-01-07 04:05:00 KST
**Status**: ✅ **RESOLVED** - All IntlError issues fixed
**Next Action**: Proceed with User Testing (no blocking errors remaining)
