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
# Running the main application
.venv/bin/python genie.py create --requirements data/demo_requirements.md

# Running validation
.venv/bin/python genie.py validate

# Installing packages
.venv/bin/python -m pip install -r requirements.txt

# Running scripts
.venv/bin/python scripts/auto_deploy.py
.venv/bin/python scripts/validate_setup.py

# Running modules
.venv/bin/python -m pip
```

#### Incorrect Usage ❌

```bash
# DO NOT USE THESE
python genie.py create --requirements data/demo_requirements.md
python3 genie.py validate
pip install -r requirements.txt
python scripts/validate_setup.py
```

### Project-Specific Commands

All project commands must use `.venv/bin/python`:

**Main CLI:**
```bash
# Full pipeline
.venv/bin/python genie.py create --requirements data/demo_requirements.md

# Parse documents
.venv/bin/python genie.py parse --input-dir real_requirements/inputs --output data/parsed.md

# Individual steps
.venv/bin/python genie.py generate --requirements data/parsed.md
.venv/bin/python genie.py validate
.venv/bin/python genie.py deploy
```

**Validation:**
```bash
# Validate configuration
.venv/bin/python genie.py validate

# Verify setup
.venv/bin/python scripts/validate_setup.py
```

**Scripts:**
```bash
# Deployment automation
.venv/bin/python scripts/auto_deploy.py

# Setup validation
.venv/bin/python scripts/validate_setup.py

# Other scripts
.venv/bin/python scripts/fix_instructions.py
.venv/bin/python scripts/analyze_feedback.py
```

### Virtual Environment Location

- **Location**: Project root directory
- **Path**: `.venv/`
- **Python executable**: `.venv/bin/python`
- **Pip**: `.venv/bin/python -m pip` (use this instead of `.venv/bin/pip`)

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
# .venv\Scripts\activate  # Windows

# Install dependencies
.venv/bin/python -m pip install -r requirements.txt

# Verify setup
.venv/bin/python scripts/validate_setup.py
```

### Exception: When NOT to Use .venv

The ONLY exceptions where you can use system Python:

1. **Creating the virtual environment itself**:
   ```bash
   python3 -m venv .venv
   ```

2. **Global tool installations** (not project-specific):
   ```bash
   pip install databricks-cli  # If installing globally
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

### Rule Enforcement

This rule is enforced:
- In documentation (CLAUDE.md)
- In skills (genie-commit, genie-deploy, deploy-app)
- In validation scripts
- In deployment workflows

**When suggesting Python commands to users, ALWAYS use `.venv/bin/python`.**
