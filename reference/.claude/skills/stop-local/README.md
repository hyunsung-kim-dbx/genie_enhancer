# stop-local Skill

Stop local Genie Lamp Agent development servers (backend and frontend).

## Overview

The `stop-local` skill provides a clean way to stop locally running development servers. It:
- Identifies processes by port number (8000 for backend, 3000 for frontend)
- Attempts graceful shutdown first (SIGTERM)
- Force-kills if needed (SIGKILL)
- Verifies ports are freed
- Provides clear status feedback

## When to Use

Use this skill when you want to:
- Stop local development servers when done
- Free up ports 8000 or 3000
- Clean up before switching tasks
- Resolve port conflicts
- Restart servers (stop then start)

## Quick Start

**From Claude Code:**
```
/stop-local
```

**From Command Line:**
```bash
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py
```

## Options

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

## What It Does

1. **Identify Processes**: Uses `lsof` to find processes on target ports
2. **Graceful Shutdown**: Sends SIGTERM and waits up to 5 seconds
3. **Force Cleanup**: Sends SIGKILL if graceful shutdown fails
4. **Verification**: Confirms ports are free
5. **Status Report**: Shows what was stopped and current status

## Exit Codes

- **0**: All servers stopped successfully
- **1**: Some servers failed to stop or ports still in use

## Integration with deploy-local

**Typical workflow:**
```bash
# Start servers
/deploy-local

# ... do development work ...

# Stop servers
/stop-local

# Restart servers
/deploy-local --skip-install
```

**Quick restart:**
```bash
# Stop and start in one go
.venv/bin/python .claude/skills/stop-local/scripts/stop_local.py && \
.venv/bin/python .claude/skills/deploy-local/scripts/deploy_local.py --skip-install
```

## Troubleshooting

**No processes found:**
- Servers are already stopped (no action needed)

**Permission denied:**
- Process may be owned by different user
- Try with sudo (rarely needed for your own processes)

**Process still running after force kill:**
- Check process details: `lsof -i :8000`
- Kill by PID: `kill -9 <PID>`

**Ports still in use:**
```bash
# Manual cleanup
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

## Example Output

**Successful stop:**
```
================================================================================
Stopping Local Genie Lamp Agent Servers
================================================================================

ℹ Checking for backend server on port 8000...
✓ Found backend server (PID: 12345)
ℹ Stopping backend server (PID: 12345)...
✓ Backend server stopped (PID: 12345)

ℹ Checking for frontend server on port 3000...
✓ Found frontend server (PID: 12346)
ℹ Stopping frontend server (PID: 12346)...
✓ Frontend server stopped (PID: 12346)

================================================================================
Verification
================================================================================

✓ Backend port 8000 is free
✓ Frontend port 3000 is free

================================================================================
Summary
================================================================================

✓ All servers stopped successfully
  • Backend (port 8000): Stopped
  • Frontend (port 3000): Stopped
```

**No servers running:**
```
================================================================================
Stopping Local Genie Lamp Agent Servers
================================================================================

ℹ Checking for backend server on port 8000...
ℹ No backend server found on port 8000
ℹ Checking for frontend server on port 3000...
ℹ No frontend server found on port 3000

================================================================================
Summary
================================================================================

✓ All servers stopped successfully
```

## Files

- `skill.md`: Skill description and complete documentation
- `scripts/stop_local.py`: Main script to stop servers
- `README.md`: This file

## Related Skills

- **deploy-local**: Start local development servers
- **deploy-app**: Deploy to Databricks Apps (production)

## Support

For issues or questions:
- Check that you're running from the project root
- Verify you have permission to stop the processes
- Try `--force` flag if graceful shutdown fails
- See `skill.md` for detailed troubleshooting
