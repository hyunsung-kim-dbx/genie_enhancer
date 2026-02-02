# Authentication Architecture

## Overview

The Genie Enhancement System uses a **dual-auth pattern**: user credentials for Genie operations and service principal for backend infrastructure.

## Why This Matters

**Genie Spaces are USER-scoped resources.**

- When a user creates/clones/updates a Genie space, they need **their own permissions** on that space
- Service principals **cannot act on behalf of users** for Genie operations
- Using the service principal's token for Genie operations will fail with permission errors

## Authentication Flow

```
┌──────────┐                 ┌─────────────┐                 ┌──────────────┐
│          │  User Token     │             │  User Token     │              │
│ Frontend │ ─────────────> │   Backend   │ ─────────────> │  Genie API   │
│   (UI)   │  (Host + PAT)  │  (FastAPI)  │ (On behalf of) │  (Spaces)    │
│          │                 │             │      user)      │              │
└──────────┘                 └─────────────┘                 └──────────────┘
                                     │
                                     │ Service Principal Token
                                     │ (For infrastructure)
                                     ▼
                             ┌──────────────┐
                             │              │
                             │  SQL Queries │
                             │  (Validation)│
                             │              │
                             └──────────────┘
```

## Implementation

### 1. User Credentials (Frontend → Backend → Genie)

**Frontend (UI):**
- User enters host and personal access token
- Credentials sent in API requests via `workspace_config`

**Backend (API):**
```python
class WorkspaceConfig(BaseModel):
    host: str
    token: str          # USER'S token
    warehouse_id: str
    space_id: str
```

**Backend (Task Functions):**
```python
def run_score_job(session_id, space_id, host, token, ...):
    # Use USER's credentials for Genie operations
    genie_client = GenieConversationalClient(host, token, space_id)
    space_api = SpaceUpdater(host, token)
    llm_client = DatabricksLLMClient(host, token, endpoint)
```

**Result:** Operations succeed because they use the user's permissions.

### 2. Service Principal (Backend Infrastructure)

**Purpose:** Backend operations that don't require user context:
- SQL validation queries
- Backend infrastructure
- Secrets access

**Configuration (app.yaml):**
```yaml
env:
  - name: DATABRICKS_TOKEN
    value: "{{secrets/genie-enhancement/service-token}}"
  - name: DATABRICKS_HTTP_PATH
    value: "{{secrets/genie-enhancement/sql-warehouse-http-path}}"
```

**Usage (if needed):**
```python
import os
service_token = os.getenv("DATABRICKS_TOKEN")  # For SQL validation only
```

## Critical: Avoiding OAuth Conflicts

The Databricks SDK can pick up OAuth credentials from environment variables, causing "multiple auth methods" errors.

**Solution:** Explicitly disable OAuth when using PAT auth:

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.config import Config

# CORRECT: Explicitly disable OAuth
config = Config(
    host=host,
    token=credentials.token,  # User's PAT
    client_id=None,           # Disable OAuth
    client_secret=None,
)
client = WorkspaceClient(config=config)

# WRONG: SDK might pick up OAuth from env
client = WorkspaceClient(host=host, token=credentials.token)
```

## API Client Pattern

All API clients accept credentials as parameters:

**Genie Conversational Client:**
```python
client = GenieConversationalClient(host, token, space_id)
```

**Space API Client:**
```python
space_api = SpaceUpdater(host, token)
```

**LLM Client:**
```python
llm_client = DatabricksLLMClient(host, token, endpoint_name)
```

**SQL Executor:**
```python
sql_executor = SQLExecutor(host, token, warehouse_id)
```

## Secrets Configuration

**Secrets Scope:** `genie-enhancement`

**Required Secrets:**
```bash
# Service principal token (for backend infrastructure only)
databricks secrets put-secret genie-enhancement service-token

# SQL warehouse path (for SQL validation queries)
databricks secrets put-secret genie-enhancement sql-warehouse-http-path
```

**NOT in secrets:**
- ❌ User tokens (provided by frontend)
- ❌ Workspace host (provided by frontend)
- ❌ Space IDs (provided by frontend)

## App Permissions

**App service principal needs:**
- ✅ Read access to Unity Catalog (for SQL validation)
- ✅ Access to secrets scope (`genie-enhancement`)
- ❌ NO Genie space permissions needed!

**Why:** Operations use user's credentials, so they inherit user's permissions.

## Common Issues and Solutions

### Issue 1: "Permission denied" on Genie operations
**Cause:** Using service principal token instead of user token
**Solution:** Ensure user credentials are passed from frontend through to API clients

### Issue 2: "Multiple auth methods" error
**Cause:** SDK picking up OAuth credentials from environment
**Solution:** Use `Config(client_id=None, client_secret=None)`

### Issue 3: Operations work locally but fail in app
**Cause:** App environment variables overriding user credentials
**Solution:** Ensure API clients use parameters, not `os.getenv()`

## Testing Authentication

**1. Test with user credentials:**
```python
# Should succeed if user has permissions
genie_client = GenieConversationalClient(
    host="https://your-workspace.cloud.databricks.com",
    token="<user-pat>",
    space_id="<space-id>"
)
result = genie_client.ask("What are the top 10 sales?")
```

**2. Test service principal (should FAIL for Genie):**
```python
# Should FAIL with permission error
genie_client = GenieConversationalClient(
    host="https://your-workspace.cloud.databricks.com",
    token=os.getenv("DATABRICKS_TOKEN"),  # Service principal token
    space_id="<space-id>"
)
result = genie_client.ask("What are the top 10 sales?")
# Error: Permission denied
```

## Summary

| Operation | Uses | Token From |
|-----------|------|------------|
| Genie Space Operations | User Credentials | Frontend → Backend parameter |
| LLM Inference | User Credentials | Frontend → Backend parameter |
| SQL Validation | Service Principal | Environment variable (optional) |
| Secrets Access | App Service Principal | Databricks Apps runtime |

**Golden Rule:**
- 🟢 Genie operations → Use user credentials
- 🔵 Backend infrastructure → Use service principal (if needed)
- ⚠️ Never use service principal for Genie operations
