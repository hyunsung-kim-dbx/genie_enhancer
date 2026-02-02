---
name: project-commit
description: Create git commits for the Genie Lamp Agent project with automated testing, validation, and conventional commit messages. Use when the user asks to commit changes, create a commit, or save work to git. Includes pre-commit testing workflow, virtual environment handling, and project-specific commit message patterns (feat/fix/refactor/docs/test).
---

# Project Commit

Automate git commits for the Genie Lamp Agent project with proper testing, validation, and conventional commit messages.

## Commit Workflow

Follow this workflow when the user requests a commit:

### 1. Check Branch and Create Feature Branch

**Always check the current branch before committing:**

```bash
git branch --show-current
```

**If on `main` or `master` branch:**
1. Ask the user if they want to create a feature branch
2. Suggest a branch name based on the commit type and description:
   - Format: `<type>/<short-description>`
   - Examples:
     - `feat/pre-commit-hook`
     - `fix/table-validation`
     - `refactor/parsing-module`
     - `docs/update-readme`

3. Create and switch to the feature branch:
```bash
git checkout -b feat/your-feature-name
```

**If already on a feature branch:** Proceed with the commit workflow.

**Note:** This prevents accidentally committing directly to main/master and follows Git best practices.

### 2. Pre-commit Status Check

**Note:** The pre-commit hook validates that tests were run recently (< 120 min).
If the hook fails, run `scripts/run_smoke.sh` first.

Run these commands in parallel to understand the current state:

```bash
git status
git diff --staged
git diff
```

Analyze what files have changed and their purpose in the project.

### 3. Determine Commit Type

Based on the changed files, classify the commit:

- **feat:** New features or functionality
  - New pipeline components
  - New CLI commands
  - New API integrations
  - Enhanced generation capabilities

- **fix:** Bug fixes
  - Fixing validation logic
  - Correcting parsing errors
  - API compatibility fixes
  - Error handling improvements

- **refactor:** Code restructuring without changing functionality
  - Reorganizing modules
  - Renaming files or functions
  - Simplifying logic
  - Removing deprecated code

- **docs:** Documentation changes only
  - README updates
  - CLAUDE.md modifications
  - Comment improvements
  - Architecture documentation

- **test:** Adding or updating tests
  - New test cases
  - Test refactoring
  - Test data updates

- **chore:** Maintenance tasks
  - Dependency updates
  - Configuration changes
  - Build script updates

### 4. Craft Commit Message

Format: `<type>: <description>`

**Description guidelines:**
- Start with a capital letter
- Use imperative mood ("Add" not "Added" or "Adds")
- Be specific and concise (50-72 characters)
- Focus on WHAT and WHY, not HOW
- Reference key components or files changed

**Examples from this project:**
```
feat: Add SQL validation and instruction quality scoring to generation pipeline
feat: Add markdown formatting support for Genie space instructions
fix: Display benchmark questions in output and ensure API compatibility
refactor: Unify CLI with genie.py and modular pipeline architecture
docs: Enhance README with GitHub integration and fix broken references
test: Add integration tests for table validator
```

### 5. Stage and Commit

Stage specific files (avoid `git add -A` to prevent accidentally committing sensitive files):

```bash
# Stage specific files
git add src/pipeline/generator.py
git add tests/test_generation.py
# ... other files

# Create commit with Co-Authored-By trailer
git commit -m "$(cat <<'EOF'
feat: Add your description here

Detailed explanation if needed (optional).
- Bullet points for multiple changes
- Or additional context

Co-Authored-By: Claude (databricks-claude-sonnet-4-5) <noreply@anthropic.com>
EOF
)"
```

### 6. Verify Commit

After committing, verify success:

```bash
git status
git log -1 --pretty=format:"%h - %s%n%b"
```

## Project-Specific Validations

### Virtual Environment Check

Always use `.venv/bin/python` instead of `python` or `python3`. This is enforced by the project's cursor rules.

### Test Coverage

The project has comprehensive tests in `tests/`:
- `test_generation.py` - End-to-end config generation
- `test_table_validator.py` - Unity Catalog validation
- `test_requirements_converter.py` - PDF/markdown parsing
- `test_pdf_image_parsing.py` - Vision model parsing
- `test_endpoint.py` - Databricks endpoint connectivity
- `test_join_specs.py` - Join specification handling

### Sensitive Files to Avoid

Never commit:
- `.env` files (contains DATABRICKS_HOST and DATABRICKS_TOKEN)
- `output/` directory (contains generated configs)
- `__pycache__/` directories
- `.pytest_cache/` directories
- Personal access tokens or credentials

## Quick Reference

### Common Scenarios

**Scenario 1: Committing from main branch**
```bash
# Check current branch
git branch --show-current
# Output: main

# Create feature branch before committing
git checkout -b feat/retry-logic

# Then proceed with commit
Type: feat
Message: "feat: Add retry logic for LLM API calls"
```

**Scenario 2: Feature addition on feature branch**
```bash
# Already on feature branch, proceed with commit
Type: feat
Message: "feat: Add retry logic for LLM API calls"
```

**Scenario 3: Bug fix**
```bash
# User fixed table validation error handling
Type: fix
Message: "fix: Handle missing schema gracefully in table validator"
```

**Scenario 4: Refactoring**
```bash
# User reorganized the parsing module
Type: refactor
Message: "refactor: Split PDF parser into separate page processors"
```

## Error Handling

### Pre-commit Hook Failures

If git hooks fail:
1. Show the error to the user
2. Fix the issue if possible
3. Create a NEW commit (never use --amend unless explicitly requested)

### Merge Conflicts

If there are merge conflicts:
1. Alert the user immediately
2. Do NOT attempt to commit
3. Guide them to resolve conflicts first

### Empty Commits

If there are no changes to commit:
1. Inform the user
2. Show current git status
3. Ask if they meant to stage files first

## References

See `references/commit-best-practices.md` for additional guidance on:
- Writing effective commit messages
- Handling complex multi-file changes
- Commit message conventions
- Git workflow best practices
