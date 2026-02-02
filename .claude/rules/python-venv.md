# Python Virtual Environment Rules

## Virtual Environment Usage

**CRITICAL RULE: Always use the project root `.venv` for Python commands.**

### Required Python Execution Pattern

When executing Python commands, you MUST use:
```bash
.venv/bin/python
```

**NEVER use:**
- `python` (system Python)
- `python3` (system Python 3)
- `py` (Windows launcher)
- Any other Python interpreter

### Examples

#### Correct Usage ✅

```bash
# Running the CLI
.venv/bin/python enhancer.py score --host ... --space-id ...

# Running backend
.venv/bin/python -m uvicorn backend.main:app

# Installing packages
.venv/bin/python -m pip install -r requirements.txt

# Running tests
.venv/bin/python -m pytest
```

#### Incorrect Usage ❌

```bash
# DO NOT USE THESE
python enhancer.py score
python3 -m uvicorn backend.main:app
pip install -r requirements.txt
```

### Why This Matters

1. **Dependency Isolation**: Ensures correct package versions are used
2. **Reproducibility**: All team members use the same environment
3. **No System Conflicts**: Avoids conflicts with system Python packages
4. **Project Standards**: Enforced by project configuration
5. **Testing Reliability**: Tests run with the correct dependencies

### Environment Setup

If the virtual environment doesn't exist or needs to be recreated:

```bash
# Create virtual environment (if needed)
python3 -m venv .venv

# Activate (for interactive use only)
source .venv/bin/activate  # macOS/Linux

# Install dependencies
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r backend/requirements.txt
```

### Exception: When NOT to Use .venv

The ONLY exception where you can use system Python:

1. **Creating the virtual environment itself**:
   ```bash
   python3 -m venv .venv
   ```

For all other Python operations, use `.venv/bin/python`.

### Verification

To verify you're using the correct Python:

```bash
# Check Python path
.venv/bin/python -c "import sys; print(sys.executable)"
# Should output: /path/to/project/.venv/bin/python

# Check installed packages
.venv/bin/python -m pip list
```

**When suggesting Python commands to users, ALWAYS use `.venv/bin/python`.**
