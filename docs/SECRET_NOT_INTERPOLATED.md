# Secret Not Being Interpolated - Diagnostic Guide

## The Problem

Your environment shows:
```
"DATABRICKS_TOKEN={{secrets/genie-enhancement/service-token}}"  ← Still a template!
```

This means the Databricks Apps runtime is **NOT interpolating the secret**. It should look like:
```
"DATABRICKS_TOKEN=dapi1234567890abcdef..."  ← Actual token value
```

## Why This Happens

The template `{{secrets/scope-name/key-name}}` is not being replaced with the actual secret value because:

### 1. **Secret Doesn't Exist**

The secret `service-token` doesn't exist in scope `genie-enhancement`.

**Check:**
```bash
# List secrets in the scope
databricks secrets list --scope genie-enhancement

# Expected output:
# Key             Last Updated
# service-token   2024-01-15
```

**Fix:**
```bash
# Create the secret
databricks secrets put-secret genie-enhancement service-token

# When prompted, paste your PAT (personal access token)
# Or use string value:
databricks secrets put-secret genie-enhancement service-token --string-value "dapi..."
```

### 2. **Secret Scope Doesn't Exist**

The scope `genie-enhancement` doesn't exist.

**Check:**
```bash
# List all scopes
databricks secrets list-scopes

# Expected output should include:
# Scope               Backend  Principal
# genie-enhancement   DATABRICKS
```

**Fix:**
```bash
# Create the scope
databricks secrets create-scope genie-enhancement

# Then add the secret
databricks secrets put-secret genie-enhancement service-token
```

### 3. **App Doesn't Have Permission to Read Secret**

The app service principal doesn't have READ permission on the secret scope.

**Check:**
```bash
# Check scope permissions
databricks secrets list-acls --scope genie-enhancement

# Expected output should include:
# Principal                        Permission
# <app-service-principal>          READ
```

**Fix:**

**Option A: Grant permission via CLI (if supported):**
```bash
# Grant READ permission to app service principal
databricks secrets put-acl --scope genie-enhancement \
  --principal <app-service-principal-id> \
  --permission READ
```

**Option B: Use DATABRICKS-backed scope (recommended):**
- DATABRICKS-backed scopes inherit workspace permissions
- The app automatically has access
- No explicit ACL needed

```bash
# Recreate scope as DATABRICKS-backed
databricks secrets delete-scope genie-enhancement
databricks secrets create-scope genie-enhancement --initial-manage-principal users
databricks secrets put-secret genie-enhancement service-token
```

### 4. **Wrong Secret Path in app.yaml**

The secret path in `app.yaml` doesn't match the actual secret location.

**Check app.yaml:**
```yaml
env:
  - name: DATABRICKS_TOKEN
    value: "{{secrets/genie-enhancement/service-token}}"
            #        ^^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^
            #        scope name            key name
```

**Fix:**
- Ensure scope name matches: `genie-enhancement` (not `genie-enhancer`, not `genie_enhancement`)
- Ensure key name matches: `service-token` (not `service_token`, not `servicetoken`)
- Secrets are case-sensitive!

## Diagnostic Steps

### Step 1: Check if secret exists

```bash
databricks secrets list --scope genie-enhancement
```

**Expected:** You see `service-token` in the list

**If not found:**
```bash
databricks secrets put-secret genie-enhancement service-token
# Paste your PAT when prompted
```

### Step 2: Check if scope exists

```bash
databricks secrets list-scopes
```

**Expected:** You see `genie-enhancement` in the list

**If not found:**
```bash
databricks secrets create-scope genie-enhancement
databricks secrets put-secret genie-enhancement service-token
```

### Step 3: Verify app.yaml configuration

Check that `app.yaml` has:
```yaml
env:
  - name: DATABRICKS_TOKEN
    value: "{{secrets/genie-enhancement/service-token}}"
```

**Common mistakes:**
- ❌ `{{secrets/genie-enhancer/service-token}}` (wrong scope name)
- ❌ `{{secrets/genie-enhancement/service_token}}` (underscore instead of dash)
- ❌ `{{secret/genie-enhancement/service-token}}` (typo: "secret" not "secrets")

### Step 4: Redeploy the app

After fixing secrets:
```bash
cd /Users/hyunsung.kim/genie_enhancer
databricks bundle deploy
```

### Step 5: Check environment after deployment

```bash
# Check app logs
databricks apps logs genie-enhancer | head -20

# Or check environment via API
curl https://genie-enhancer-<workspace-id>.aws.databricksapps.com/api/workspace/config
```

**Expected response:**
```json
{
  "host": "https://krafton-sandbox.cloud.databricks.com",
  "token": "dapi...",  ← Actual token (will be masked)
  "_debug": {
    "token_is_template": false,
    "token_hint": "Token successfully loaded"
  }
}
```

**If still template:**
```json
{
  "host": "https://krafton-sandbox.cloud.databricks.com",
  "token": "",
  "_debug": {
    "token_is_template": true,
    "token_hint": "Check 'databricks secrets list --scope genie-enhancement'"
  }
}
```

## Quick Fix Commands

**Complete setup from scratch:**
```bash
# 1. Create secret scope
databricks secrets create-scope genie-enhancement

# 2. Add your PAT to the scope
databricks secrets put-secret genie-enhancement service-token
# Paste your PAT when prompted

# 3. Verify secret was added
databricks secrets list --scope genie-enhancement

# 4. Redeploy app
cd /Users/hyunsung.kim/genie_enhancer
databricks bundle deploy

# 5. Check environment
databricks apps logs genie-enhancer | grep DATABRICKS_TOKEN

# 6. Test the app
curl https://genie-enhancer-7474647945795688.aws.databricksapps.com/api/workspace/config
```

## Common Issues

### Issue: "Secret not found" when creating secret

**Cause:** Scope doesn't exist

**Solution:**
```bash
databricks secrets create-scope genie-enhancement
databricks secrets put-secret genie-enhancement service-token
```

### Issue: "Permission denied" when reading secret

**Cause:** App doesn't have READ permission

**Solution:** Use DATABRICKS-backed scope (default) which inherits permissions:
```bash
databricks secrets delete-scope genie-enhancement
databricks secrets create-scope genie-enhancement --initial-manage-principal users
databricks secrets put-secret genie-enhancement service-token
```

### Issue: Secret exists but still shows as template

**Cause:** Wrong secret path or typo

**Solution:** Double-check app.yaml matches exactly:
- Scope name: `genie-enhancement` (with dash)
- Key name: `service-token` (with dash)
- Case-sensitive!

### Issue: App was deployed before secret was created

**Cause:** Databricks Apps interpolates secrets at deployment time

**Solution:** Redeploy after creating secret:
```bash
databricks bundle deploy
```

## Verification

After fixing, verify the secret is properly loaded:

**1. Check environment response:**
```bash
curl https://genie-enhancer-7474647945795688.aws.databricksapps.com/api/workspace/config
```

**2. Check app can list warehouses:**
```bash
curl -X POST https://genie-enhancer-7474647945795688.aws.databricksapps.com/api/workspace/warehouses \
  -H "Content-Type: application/json" \
  -d '{"host": "https://krafton-sandbox.cloud.databricks.com", "token": "YOUR_PAT"}'
```

**3. Check logs for errors:**
```bash
databricks apps logs genie-enhancer | grep -i "token\|secret\|auth"
```

## Summary

**The secret template is not being interpolated because:**
1. ❌ Secret doesn't exist in the scope
2. ❌ Secret scope doesn't exist
3. ❌ App doesn't have permission to read secret
4. ❌ Secret path in app.yaml is incorrect

**Fix by:**
1. ✅ Create the secret scope
2. ✅ Add your PAT to the scope
3. ✅ Verify app.yaml has correct path
4. ✅ Redeploy the app
5. ✅ Test the config endpoint

**Once fixed, the app will:**
- ✅ Auto-populate host field
- ✅ Auto-populate token field
- ✅ Allow operations without manual credential entry
