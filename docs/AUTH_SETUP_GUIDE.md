# Authentication Setup Guide

## What Changed

✅ **Good news:** Your code was already 95% correct! I made 2 small fixes:

1. **backend/main.py**: Added explicit OAuth disabling in `list_genie_spaces` function
2. **app.yaml**: Added comments clarifying that service principal token is NOT for Genie operations

## What You Need To Do

### Step 1: Verify Secrets Configuration

Check that your secrets scope has the required secrets:

```bash
# List secrets in the scope
databricks secrets list --scope genie-enhancement
```

**Expected secrets:**
- `service-token`: Service principal PAT (for SQL validation)
- `sql-warehouse-http-path`: SQL Warehouse HTTP path

**If missing, create them:**

```bash
# Create the scope (if doesn't exist)
databricks secrets create-scope genie-enhancement

# Add service principal token
databricks secrets put-secret genie-enhancement service-token
# Paste your service principal PAT when prompted

# Add SQL warehouse path
databricks secrets put-secret genie-enhancement sql-warehouse-http-path
# Paste path like: /sql/1.0/warehouses/<warehouse-id>
```

### Step 2: Deploy the Updated App

```bash
# Navigate to project root
cd /Users/hyunsung.kim/genie_enhancer

# Build frontend (if not already built)
cd frontend && npm run build && cd ..

# Deploy the app
databricks bundle deploy
```

### Step 3: Test the Authentication Flow

#### 3.1 Access the App

```bash
# Get the app URL
databricks apps list | grep genie-enhancer
```

Access the app at: `https://<your-workspace>.cloud.databricks.com/apps/genie-enhancer`

#### 3.2 Test User Credentials Flow

1. **Open the app in your browser**
2. **Enter your credentials in the UI:**
   - **Host**: `https://<your-workspace>.cloud.databricks.com`
   - **Token**: Your **personal** access token (NOT the service principal token)
   - **Warehouse ID**: Select a warehouse from the dropdown
   - **Space ID**: Select a Genie space from the dropdown

3. **Test operations:**
   - Try scoring benchmarks
   - Try generating enhancement plans
   - Check that operations succeed

#### 3.3 Verify Logs

```bash
# Check app logs for authentication errors
databricks apps logs genie-enhancer --follow
```

**Look for:**
- ✅ No "multiple auth methods" errors
- ✅ No "permission denied" on Genie operations
- ✅ Successful API calls

### Step 4: Troubleshooting

#### Issue: "Permission denied" on Genie operations

**Diagnosis:**
```bash
# Check if app is using correct credentials
databricks apps logs genie-enhancer | grep -i "permission\|denied\|unauthorized"
```

**Solution:**
- Ensure you're entering YOUR personal access token in the UI
- Do NOT use the service principal token
- Verify your token has access to the Genie space

#### Issue: "Multiple auth methods" error

**Diagnosis:**
```bash
# Check logs for auth method conflicts
databricks apps logs genie-enhancer | grep -i "multiple auth"
```

**Solution:**
- This should be fixed by the code changes
- If still occurring, check for environment variables setting OAuth credentials

#### Issue: Dropdowns not loading (warehouses/spaces)

**Diagnosis:**
```bash
# Check API endpoint logs
databricks apps logs genie-enhancer | grep -i "warehouse\|space"
```

**Solution:**
- Verify your token has LIST permissions on warehouses and spaces
- Check that host URL is correct (should include `https://`)

### Step 5: Verify Authentication Pattern

**Run this test to confirm the pattern is working:**

```python
# Test script: test_auth_pattern.py
import requests

# Replace with your app URL
APP_URL = "https://<workspace>.cloud.databricks.com/apps/genie-enhancer"
USER_TOKEN = "<your-personal-token>"
WORKSPACE_HOST = "https://<workspace>.cloud.databricks.com"

# Test 1: List warehouses (should succeed)
response = requests.post(
    f"{APP_URL}/api/workspace/warehouses",
    json={
        "host": WORKSPACE_HOST,
        "token": USER_TOKEN
    }
)
print("Warehouses:", response.json())

# Test 2: List Genie spaces (should succeed)
response = requests.post(
    f"{APP_URL}/api/workspace/spaces",
    json={
        "host": WORKSPACE_HOST,
        "token": USER_TOKEN
    }
)
print("Spaces:", response.json())
```

**Expected output:**
```json
{
  "warehouses": [
    {"id": "...", "name": "...", "state": "RUNNING"}
  ]
}

{
  "spaces": [
    {"id": "...", "name": "...", "description": "..."}
  ]
}
```

## Understanding the Auth Flow

### What Happens Now (CORRECT)

```
1. User enters credentials in UI
   ├─ Host: https://your-workspace.cloud.databricks.com
   ├─ Token: User's personal access token
   ├─ Warehouse: User-selected warehouse
   └─ Space: User-selected Genie space

2. Frontend sends credentials to backend
   POST /api/jobs/score
   {
     "workspace_config": {
       "host": "...",
       "token": "<user-token>",  ← User's credentials
       "warehouse_id": "...",
       "space_id": "..."
     }
   }

3. Backend uses user credentials for Genie
   genie_client = GenieConversationalClient(
       host=workspace_config.host,
       token=workspace_config.token  ← User's token
   )

4. Operations succeed with user's permissions ✅
```

### What NOT To Do (WRONG)

```
❌ Backend reads token from environment
   token = os.getenv("DATABRICKS_TOKEN")  # Service principal token
   genie_client = GenieConversationalClient(host, token, space_id)
   # FAILS: Service principal doesn't have user's permissions

❌ Frontend sends empty credentials
   POST /api/jobs/score
   {
     "workspace_config": {
       "host": "",
       "token": "",  ← Empty!
     }
   }
   # FAILS: Backend has no credentials to use

❌ Use service principal token in UI
   Token: dapi...  ← Service principal token
   # FAILS: Service principal can't access user's Genie spaces
```

## App Permissions Summary

**What the app service principal needs:**
- ✅ Read access to Unity Catalog (for SQL validation)
- ✅ Access to `genie-enhancement` secrets scope
- ✅ Basic workspace access

**What the app service principal does NOT need:**
- ❌ Permissions on Genie spaces
- ❌ CAN_MANAGE on user's resources
- ❌ Any user-level permissions

**Why:** All Genie operations use the user's credentials, not the app's credentials.

## Quick Reference

| Component | Auth Type | Token Source |
|-----------|-----------|--------------|
| Frontend | User credentials | User input |
| Backend API | User credentials (passed through) | API request parameters |
| Genie API calls | User credentials | Passed from backend |
| LLM inference | User credentials | Passed from backend |
| SQL validation | Service principal | Environment variable (optional) |

## Success Criteria

✅ User can list warehouses and Genie spaces
✅ User can score benchmarks without permission errors
✅ No "multiple auth methods" errors in logs
✅ Operations complete successfully with user's permissions
✅ App works for multiple users (each with their own permissions)

## Next Steps

1. Deploy the updated app
2. Test with your personal credentials
3. Verify operations succeed
4. Test with another user to confirm multi-user support

## Need Help?

If you encounter issues:

1. **Check logs:** `databricks apps logs genie-enhancer --follow`
2. **Verify secrets:** `databricks secrets list --scope genie-enhancement`
3. **Test credentials:** Use the test script above
4. **Review documentation:** See `/docs/AUTHENTICATION.md` for detailed architecture

## Summary

**The fix was simple:** Your code was already passing user credentials correctly. I just added explicit OAuth disabling to prevent SDK conflicts. The key insight is that **Genie operations must use the user's token**, not the service principal's token.

**Test it now:** Deploy and try the workflow with your personal credentials!
