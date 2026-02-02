---
name: stop-local
description: Stop local Genie Lamp Agent development servers (backend and frontend). Use when the user asks to stop local servers, shut down local development, or clean up running processes. Automatically finds and stops servers running on ports 8000 and 3000.
---

# Stop Local Genie Lamp Agent Servers

Stop the locally running Genie Lamp Agent backend and frontend development servers.

## Overview

This skill helps you cleanly stop local development servers when:
- **Switching Tasks**: You're done with local development and want to free up resources
- **Resolving Port Conflicts**: You need to free up ports 8000 or 3000
- **Cleaning Up**: You want to ensure no background processes are running
- **Before Deployment**: Clean shutdown before deploying to Databricks

## What This Skill Does

The stop-local skill performs a clean shutdown:

1. ✅ **Identifies Running Servers**: Checks for processes on ports 8000 (backend) and 3000 (frontend)
2. ✅ **Graceful Shutdown**: Attempts to stop servers gracefully (SIGTERM)
3. ✅ **Forced Cleanup**: Force-kills stubborn processes if needed (SIGKILL)
4. ✅ **Verification**: Confirms ports are freed and processes stopped
5. ✅ **Status Report**: Shows what was stopped and current status

## Usage

**Quick Stop (Recommended):**
```bash
# From project root
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py
```

**With Options:**
```bash
# Stop only backend
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --backend-only

# Stop only frontend
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --frontend-only

# Force kill (skip graceful shutdown)
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --force

# Custom ports
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py \
  --backend-port 8080 \
  --frontend-port 3001
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--backend-port` | Backend server port to stop | `8000` |
| `--frontend-port` | Frontend server port to stop | `3000` |
| `--backend-only` | Stop only backend server | `False` |
| `--frontend-only` | Stop only frontend server | `False` |
| `--force` | Force kill without graceful shutdown | `False` |

## How It Works

### Step 1: Identify Running Processes
The script uses `lsof` to find processes listening on:
- Port 8000 (backend FastAPI/uvicorn)
- Port 3000 (frontend Next.js dev server)

### Step 2: Graceful Shutdown (Default)
Sends SIGTERM signal to processes:
- Allows processes to clean up resources
- Saves any pending work
- Closes connections properly
- Waits up to 5 seconds for shutdown

### Step 3: Forced Cleanup (If Needed)
If processes don't stop gracefully:
- Sends SIGKILL signal (force kill)
- Immediately terminates processes
- Ensures ports are freed

### Step 4: Verification
Confirms:
- All target processes stopped
- Ports are available
- No zombie processes remaining

## Common Scenarios

### Scenario 1: Normal Shutdown
```bash
# Stop both servers gracefully
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py

# Output:
# ✓ Backend stopped (port 8000)
# ✓ Frontend stopped (port 3000)
```

### Scenario 2: Backend Development Only
```bash
# Restart backend but keep frontend running
# First, stop only backend
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --backend-only

# Then start backend
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --backend-only
```

### Scenario 3: Stuck Processes
```bash
# Processes won't stop gracefully
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py --force

# Output:
# ⚠ Force killing backend (port 8000)
# ⚠ Force killing frontend (port 3000)
# ✓ All processes stopped
```

### Scenario 4: Custom Ports
```bash
# Stop servers on non-default ports
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py \
  --backend-port 8080 \
  --frontend-port 3001
```

## Troubleshooting

### Error: "No processes found"
**Meaning**: No servers are running on the specified ports
**Action**: No action needed - servers are already stopped

### Error: "Permission denied"
**Solution**: You may need appropriate permissions to kill processes
```bash
# On macOS/Linux, use sudo if needed (rarely required for your own processes)
sudo .venv/bin/python .claude/skills/stop-local/scripts/stop_local.py
```

### Error: "Process still running after force kill"
**Possible Causes**:
1. Process owned by different user
2. System process protection
3. Process in uninterruptible state

**Solution**:
```bash
# Check process details
lsof -i :8000
ps aux | grep uvicorn

# Kill by process ID directly
kill -9 <PID>
```

### Ports Still in Use After Stopping
**Check for other processes**:
```bash
# Identify what's using the port
lsof -i :8000
lsof -i :3000

# Kill by port
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

## Integration with Deploy-Local

The stop-local skill works seamlessly with deploy-local:

**Typical Development Cycle:**
```bash
# 1. Start development servers
/deploy-local

# 2. Do development work...

# 3. Stop servers when done
/stop-local

# 4. Later, restart servers
/deploy-local --skip-install  # Faster restart
```

**Quick Restart:**
```bash
# Stop and start in one go
/stop-local && /deploy-local --skip-install
```

## When to Use This Skill

**Use stop-local when:**
- ✅ Done with local development for the day
- ✅ Need to free up ports 8000/3000
- ✅ About to deploy to Databricks
- ✅ Switching to different branch/project
- ✅ Experiencing server issues (restart)
- ✅ Running into port conflicts

**Don't use if:**
- ❌ Servers aren't running (no harm, just unnecessary)
- ❌ You want to restart - use deploy-local which handles cleanup

## Safety Notes

- **Graceful by Default**: The script attempts graceful shutdown first
- **Your Processes Only**: Only stops processes you have permission to kill
- **No Data Loss**: Properly running servers should save state before stopping
- **Port Verification**: Confirms ports are freed before completing

## Output Examples

**Successful Stop:**
```
================================================================================
Stopping Local Genie Lamp Agent Servers
================================================================================

ℹ Checking for running servers...

✓ Found backend server on port 8000 (PID: 12345)
✓ Found frontend server on port 3000 (PID: 12346)

ℹ Stopping backend server...
✓ Backend server stopped

ℹ Stopping frontend server...
✓ Frontend server stopped

================================================================================
All Servers Stopped
================================================================================

✓ Backend (port 8000): Stopped
✓ Frontend (port 3000): Stopped
✓ All ports freed
```

**No Servers Running:**
```
================================================================================
Stopping Local Genie Lamp Agent Servers
================================================================================

ℹ Checking for running servers...
ℹ No backend server found on port 8000
ℹ No frontend server found on port 3000

✓ No servers to stop
```

## Related Skills

- **deploy-local**: Start local development servers
- **deploy-app**: Deploy to Databricks Apps (production)

## Support

For issues:
- 🐛 Process won't stop: Try `--force` flag
- 🔧 Port conflicts: Check what else is using ports
- 📖 Documentation: See `README.md` in skill directory

## Summary

**Quick Stop:**
```bash
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py
```

**Via Claude Code:**
```
/stop-local
```

**Verify Stopped:**
```bash
lsof -i :8000  # Should return nothing
lsof -i :3000  # Should return nothing
```
