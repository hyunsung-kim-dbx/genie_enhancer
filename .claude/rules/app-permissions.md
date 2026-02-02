# App Deployment Safety Rules

## CRITICAL SAFETY RULE: Never Delete the App

⚠️ **WARNING: Deleting the app causes production outages and loses all granted permissions.**

### Rule Statement

**BE CAREFUL WHEN DEPLOYING THE APP - DO NOT DELETE IT.**

The Genie Enhancement app has been granted permissions through the Databricks UI. If you delete the app, you lose:
- The app's service principal identity
- All UI-granted permissions
- User access to the application
- All app configuration and state

**Key Points:**
- ✅ **Deploying updates is safe** - updates preserve the app and its permissions
- ❌ **Deleting the app is dangerous** - requires re-granting all permissions via UI
- ⚠️ **Be careful with CLI commands** - some commands can accidentally delete the app

### What You MUST NOT Do ❌

1. **NEVER delete the app**
   ```bash
   # ❌ NEVER RUN THIS
   databricks apps delete genie-enhancer
   ```

2. **NEVER trash the app**
   ```bash
   # ❌ NEVER RUN THIS
   databricks apps trash genie-enhancer
   ```

### Safe Operations ✅

1. **✅ Deploy/update the app code** (SAFE)
   ```bash
   databricks bundle deploy
   ```

2. **✅ View app status and logs**
   ```bash
   databricks apps list | grep genie-enhancer
   databricks apps get genie-enhancer
   databricks apps logs genie-enhancer
   ```

### Why This Matters

**The app's identity and permissions enable:**
- ✅ App authentication with Databricks APIs
- ✅ Access to Unity Catalog tables
- ✅ Reading secrets from the genie-enhancement scope
- ✅ Executing validation queries via SQL Warehouse
- ✅ Session persistence (local SQLite)

**If the app is deleted:**
- ❌ App completely stops functioning
- ❌ All users lose access
- ❌ Requires workspace admin to restore or re-deploy
- ❌ May lose app configuration and state

### Recovery from Accidental Deletion

**If the app is accidentally deleted:**

1. **Stop immediately** - don't make additional changes
2. **Check trash** - App might be recoverable
3. **Contact workspace admin immediately**
4. **Document what happened** - capture error messages
5. **Re-deploy if necessary** - Admin will need to re-grant permissions

### Summary

**Golden Rule:** DO NOT DELETE THE APP. Use `databricks bundle deploy` for updates.

**Safe deployment:**
```bash
databricks bundle deploy
```

**Remember:**
- ✅ Updates preserve the app and its permissions
- ❌ Deleting the app loses everything
- ⚠️ Permissions are managed via UI, not CLI
- 📞 When in doubt, ask before running any delete/trash commands
