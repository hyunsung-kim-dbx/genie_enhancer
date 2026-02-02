# App Deployment Safety Rules

## CRITICAL SAFETY RULE: Never Delete the App

⚠️ **WARNING: Deleting the app causes production outages and loses all granted permissions.**

### Rule Statement

**BE CAREFUL WHEN DEPLOYING THE APP - DO NOT DELETE IT.**

The Genie Lamp Agent app has been granted permissions through the Databricks UI. If you delete the app, you lose:
- The app's service principal identity
- All UI-granted permissions
- User access to the application
- All app configuration and state

**Key Points:**
- ✅ **Deploying updates is safe** - updates preserve the app and its permissions
- ❌ **Deleting the app is dangerous** - requires re-granting all permissions via UI
- ⚠️ **Be careful with CLI commands** - some commands can accidentally delete the app

### Permissions Are Managed via UI

**Important:** Permissions are granted through the Databricks UI, not via CLI or scripts.
- You cannot accidentally revoke permissions through CLI operations
- The main risk is accidentally deleting the app itself
- Focus on being careful during deployment operations

### What You MUST NOT Do ❌

**Focus on app deployment safety - don't delete the app:**

1. **NEVER delete the app**
   ```bash
   # ❌ NEVER RUN THIS - destroys the app and loses all permissions
   databricks apps delete genie-lamp-agent
   ```

2. **NEVER trash the app**
   ```bash
   # ❌ NEVER RUN THIS - moves app to trash, users lose access
   databricks apps trash genie-lamp-agent
   ```

3. **Be careful with deployment commands**
   ```bash
   # ❌ AVOID these commands - they might have delete/trash options
   databricks apps [command] genie-lamp-agent

   # Always double-check what the command does before running
   ```


### Safe Operations ✅

**These operations are completely safe:**

1. **✅ Deploy/update the app code** (SAFE - this is what you should use)
   ```bash
   # This is the correct way to update the app
   # It preserves the app identity and all permissions
   python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
     --target dev \
     --profile DEFAULT \
     --source-code-path /Workspace/Users/<user>/.bundle/genie-lamp-agent/dev/files \
     --working-dir app \
     --update
   ```

2. **✅ View app status and logs**
   ```bash
   # Check app status
   databricks apps list | grep genie-lamp-agent

   # View app details
   databricks apps get genie-lamp-agent

   # Check app logs
   databricks apps logs genie-lamp-agent
   ```

3. **✅ View permissions (read-only)**
   ```bash
   databricks permissions get apps/genie-lamp-agent
   ```

4. **✅ Check Unity Catalog access**
   ```sql
   SHOW GRANTS ON CATALOG sandbox;
   SHOW GRANTS ON SCHEMA sandbox.agent_poc;
   ```

### Why This Matters

**The app's identity and permissions enable:**
- ✅ App authentication with Databricks APIs
- ✅ Access to Unity Catalog tables for validation
- ✅ Reading secrets from the genie-lamp scope (service-token, sql-warehouse-http-path)
- ✅ Executing validation queries via SQL Warehouse
- ✅ Creating and deploying Genie spaces
- ✅ Processing user-uploaded requirements (local storage)
- ✅ Session persistence (local SQLite)

**If the app or its permissions are deleted:**
- ❌ App completely stops functioning
- ❌ All users lose access to the application
- ❌ Cannot generate or deploy Genie spaces
- ❌ Authentication fails for all operations
- ❌ Data access is blocked
- ❌ Requires workspace admin to restore or re-deploy
- ❌ All active user sessions terminate
- ❌ May lose app configuration and state

### Recovery from Accidental Deletion

**If the app is accidentally deleted:**

1. **Stop immediately** - don't make additional changes
2. **Check trash** - App might be in trash and recoverable
   ```bash
   databricks apps list --filter "trashed=true"
   ```
3. **Contact workspace admin immediately** - Time-sensitive for recovery
4. **Document what happened** - Capture:
   - When the app was deleted
   - What command was run
   - Error messages and logs
   - Last known working state
5. **Re-deploy if necessary** - If app cannot be restored:
   - Use the deploy-app skill to re-deploy
   - Workspace admin will need to re-grant permissions
   - Secrets scope must be verified/recreated
   - Unity Catalog grants must be re-applied

**If permissions are accidentally revoked:**

1. **Stop immediately** - don't make additional changes
2. **Document what was revoked** - capture error messages and logs
3. **Contact workspace admin** - permissions require admin privileges to restore
4. **Do not attempt to recreate** - let admin handle it to avoid further issues
5. **Verify app functionality** after restoration

### Before Making Permission Changes

**ALWAYS ask yourself:**

1. ❓ Do I have explicit approval to change permissions?
2. ❓ Have I documented the current state?
3. ❓ Do I have a rollback plan?
4. ❓ Have I tested in dev environment first?
5. ❓ Is there a valid business reason for this change?

**If the answer to ANY of these is "No", DO NOT PROCEED.**

### Approval Process

To modify app permissions:

1. **Document the request**:
   - What permissions need to change?
   - Why is the change needed?
   - What is the impact if not done?

2. **Get approval**:
   - Workspace administrator
   - Project owner
   - Security team (if applicable)

3. **Test in dev first**:
   - Make changes in dev environment
   - Verify app functionality
   - Document the procedure

4. **Apply to prod**:
   - Follow tested procedure
   - Document changes made
   - Verify app functionality

### Common Scenarios

#### ✅ Scenario 1: Deploying app updates
**Question:** I need to update the app with new code. What should I do?
**Answer:** Use the deploy-app skill with `--update` flag. This is safe and preserves all permissions.

#### ✅ Scenario 2: Checking app status
**Question:** How do I check if the app is running?
**Answer:** Use `databricks apps get genie-lamp-agent` or `databricks apps list`. Read-only operations are always safe.

#### ⚠️ Scenario 3: Initial deployment
**Question:** Can I use `--initial` flag for deployment?
**Answer:** ONLY if the app doesn't exist yet. If the app already exists, use `--update` instead. Using `--initial` on an existing app might cause issues.

#### ❌ Scenario 4: Troubleshooting deployment issues
**Question:** Deployment failed. Should I delete the app and try again?
**Answer:** NO! Never delete the app. Debug the issue first. Check logs, bundle configuration, and source code path. If stuck, ask for help.

#### ⚠️ Scenario 5: Adding new permissions
**Question:** The app needs access to a new catalog. What should I do?
**Answer:** Contact the workspace admin. Permissions are granted through the UI, not via CLI.

### Monitoring and Validation

**Regular checks (safe to run):**

```bash
# Verify service principal exists
databricks service-principals list | grep -i "genie-lamp"

# Check secrets scope
databricks secrets list-scopes | grep genie-lamp

# Verify app status
databricks apps list | grep genie-lamp-agent
```

**Include in deployment checklist:**
- ✅ Service principal exists and is active
- ✅ Secrets scope genie-lamp is accessible
- ✅ Unity Catalog grants are in place
- ✅ App can authenticate successfully

### Emergency Contact

If you accidentally delete or modify permissions:

1. **Stop all operations immediately**
2. **Contact:** Workspace Administrator
3. **Provide:**
   - What was deleted/modified
   - When it happened
   - Error messages received
   - Steps taken before the issue

### Summary

**Golden Rule:** DO NOT DELETE THE APP. Use `--update` for deployments.

**Safe deployment command:**
```bash
python .claude/skills/deploy-app/scripts/deploy_app.py genie-lamp-agent \
  --target dev --profile DEFAULT \
  --source-code-path <path> \
  --working-dir app \
  --update
```

**Remember:**
- ✅ Updates preserve the app and its permissions
- ❌ Deleting the app loses everything (identity, permissions, configuration)
- ⚠️ Permissions are managed via UI, not CLI
- 📞 When in doubt, ask before running any delete/trash commands

This rule exists to prevent accidentally destroying the app during deployment operations.
