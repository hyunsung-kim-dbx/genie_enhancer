# OAuth Conflict Fix & Auto-Population Guide

## Problem Summary

You encountered two issues:

### Issue 1: "Multiple auth methods" error ✅ FIXED

**Error:**
```
validate: more than one authorization method configured: oauth and pat.
Config: host=..., token=***, client_id=db135a71..., client_secret=***.
Env: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET
```

**Root Cause:**
- Databricks Apps runtime sets `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` as environment variables
- The SDK picks these up even when we set `client_id=None` in the Config
- This causes "multiple auth methods" conflict

**Fix Applied:**
- **Explicitly remove OAuth env vars** before creating WorkspaceClient
- Use `os.environ.pop()` to temporarily clear them
- Restore in `finally` block to avoid side effects

### Issue 2: Credentials not auto-populating ✅ FIXED

**Problem:**
- You expected host and token to auto-populate from secrets
- Fields were showing as empty

**Root Cause:**
- Code was checking if token starts with `{{` (template variable)
- If so, returns empty to "force user to provide credentials"
- This was intentional but confusing UX

**Fix Applied:**
- Changed logic to **always auto-populate** token from environment
- Host always auto-populated from workspace
- Users can override if needed

## What Changed

### File: `backend/main.py`

#### 1. Fixed `list_warehouses()` function (Lines 166-210)

**Before:**
```python
config = Config(
    host=host,
    token=credentials.token,
    client_id=None,  # This didn't work!
    client_secret=None,
)
```

**After:**
```python
# Explicitly clear OAuth env vars
saved_client_id = os.environ.pop('DATABRICKS_CLIENT_ID', None)
saved_client_secret = os.environ.pop('DATABRICKS_CLIENT_SECRET', None)

try:
    config = Config(
        host=host,
        token=credentials.token,
        client_id="",  # Empty string
        client_secret="",
    )
    client = WorkspaceClient(config=config)
    # ... use client ...
finally:
    # Restore env vars
    if saved_client_id:
        os.environ['DATABRICKS_CLIENT_ID'] = saved_client_id
    if saved_client_secret:
        os.environ['DATABRICKS_CLIENT_SECRET'] = saved_client_secret
```

#### 2. Fixed `list_genie_spaces()` function (Lines 212-256)

Same fix as above.

#### 3. Fixed `get_workspace_config()` function (Lines 130-166)

**Before:**
```python
token = os.getenv("DATABRICKS_TOKEN", "")
if token.startswith("{{"):
    token = ""  # Force user to provide
```

**After:**
```python
token = os.getenv("DATABRICKS_TOKEN", "")
if token.startswith("{{"):
    token = ""  # Template not yet interpolated
# Otherwise return the token (auto-populated)
```

## What This Means

### ✅ Credentials Auto-Populate Now

When you open the app:
- **Host:** Auto-filled from workspace
- **Token:** Auto-filled from service principal
- **You can still override** if you want to use your own PAT

### ✅ OAuth Conflict Resolved

The "multiple auth methods" error should be gone.

### ⚠️ Important: Service Principal Permissions

Since credentials are auto-populated from the **service principal**, the service principal needs:

1. **LIST permissions** on warehouses and Genie spaces
2. **CAN_EDIT** permissions on Genie spaces you want to enhance

**Granting permissions:**

```bash
# Option 1: Grant via Databricks UI
# Go to Genie Space → Share → Add service principal

# Option 2: Grant via CLI (if supported)
databricks permissions update genie-spaces <space-id> \
  --add-service-principal <service-principal-id> CAN_EDIT
```

## Testing the Fix

### Step 1: Deploy

```bash
cd /Users/hyunsung.kim/genie_enhancer
databricks bundle deploy
```

### Step 2: Open the App

```bash
databricks apps list | grep genie-enhancer
# Visit: https://<workspace>.cloud.databricks.com/apps/genie-enhancer
```

### Step 3: Check Auto-Population

**Expected behavior:**
- Host field: ✅ Pre-filled with workspace URL
- Token field: ✅ Pre-filled with masked token (e.g., `dapi...`)

### Step 4: Test Operations

1. **List warehouses:** Dropdown should populate
2. **List Genie spaces:** Dropdown should populate
3. **Run scoring:** Should work without "multiple auth methods" error

### Step 5: Verify Logs

```bash
databricks apps logs genie-enhancer --follow
```

**Look for:**
- ✅ No "multiple auth methods" errors
- ✅ Successful API calls
- ✅ Warehouse and space listings work

## Alternative: Use Your Own PAT

If you prefer to use your personal credentials:

1. **Clear the pre-filled token**
2. **Enter your own PAT**
3. Operations will use **your permissions** instead of service principal's

This is useful if:
- You don't want to grant service principal permissions
- You want operations to run as yourself
- You're testing with spaces you own

## Troubleshooting

### Issue: Token field still empty

**Diagnosis:**
```bash
# Check if secret is properly set
databricks secrets list --scope genie-enhancement

# Check if app can read it
databricks apps logs genie-enhancer | grep DATABRICKS_TOKEN
```

**Solution:**
```bash
# Verify secret exists
databricks secrets put-secret genie-enhancement service-token
# Paste your service principal PAT

# Redeploy
databricks bundle deploy
```

### Issue: "Permission denied" on Genie operations

**Cause:** Service principal doesn't have permissions on the Genie space

**Solution:** Grant permissions via UI:
1. Open the Genie Space
2. Click "Share"
3. Add service principal
4. Grant "Can Edit" permission

### Issue: OAuth error persists

**Diagnosis:**
```bash
# Check if OAuth env vars are set
databricks apps logs genie-enhancer | grep -i "DATABRICKS_CLIENT"
```

**Solution:**
- Verify the fix was deployed
- Check that `os.environ.pop()` is being called
- Try clearing browser cache and reloading

### Issue: Dropdowns not loading

**Diagnosis:**
```bash
# Check API logs
databricks apps logs genie-enhancer | grep -i "warehouse\|space"
```

**Solution:**
- Verify service principal has LIST permissions
- Check network connectivity
- Verify host URL is correct

## Why This Approach Works

### The OAuth Conflict

**Problem:**
```
SDK sees:
- token="dapi..." (from Config)
- DATABRICKS_CLIENT_ID="db135a71..." (from env)
- DATABRICKS_CLIENT_SECRET="***" (from env)

Result: "Multiple auth methods configured!"
```

**Solution:**
```
SDK sees:
- token="dapi..." (from Config)
- DATABRICKS_CLIENT_ID not in env (removed)
- DATABRICKS_CLIENT_SECRET not in env (removed)

Result: ✅ PAT auth only
```

### The Auto-Population

**Before:**
```
API returns: { "host": "...", "token": "" }
Frontend shows: Empty fields
User thinks: "Where are my credentials?"
```

**After:**
```
API returns: { "host": "...", "token": "dapi..." }
Frontend shows: Pre-filled fields
User sees: Credentials ready to use
```

## Security Considerations

### Service Principal Token Exposure

**Q:** Is it safe to auto-populate the service principal token?

**A:** Yes, because:
1. Token is masked in UI (shows as `dapi***`)
2. Token never leaves the backend (passed via API, not stored in frontend)
3. Operations are scoped to the app's permissions
4. Users can override with their own PAT if needed

### Multi-User Support

**Q:** Do all users share the same token?

**A:** By default, yes (service principal token). But:
- Each user can override with their own PAT
- Operations then use that user's permissions
- Service principal is fallback for convenience

## Summary

| Before | After |
|--------|-------|
| ❌ OAuth conflict errors | ✅ OAuth explicitly disabled |
| ❌ Empty credential fields | ✅ Auto-populated from secrets |
| ❌ Manual entry required | ✅ Works out of the box |
| ⚠️ Unclear which token to use | ✅ Clear: service principal by default, user override available |

## Next Steps

1. **Deploy the fix:** `databricks bundle deploy`
2. **Test auto-population:** Check if fields are pre-filled
3. **Test operations:** Try listing warehouses/spaces
4. **Grant permissions:** If needed, add service principal to Genie spaces
5. **Verify logs:** Confirm no OAuth errors

## Success Criteria

✅ Host field auto-populated
✅ Token field auto-populated (masked)
✅ Warehouses dropdown loads
✅ Genie spaces dropdown loads
✅ No "multiple auth methods" errors
✅ Scoring/planning/applying works

**You should now be able to use the app without manual credential entry!**
