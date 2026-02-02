# Commit Best Practices for Genie Lamp Agent

## Conventional Commit Format

### Structure

```
<type>: <subject>

[optional body]

[optional footer]
```

### Type Definitions

- **feat**: A new feature for users
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Formatting, missing semicolons, etc (no code change)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or refactoring tests
- **chore**: Changes to build process or auxiliary tools

### Subject Line Rules

1. Use imperative mood ("Add" not "Added")
2. Don't capitalize first letter after colon... wait, this project DOES capitalize
3. No period at the end
4. Keep under 72 characters
5. Be specific about what changed

### Body Guidelines (Optional)

- Wrap at 72 characters
- Explain WHAT and WHY, not HOW
- Use bullet points for multiple items
- Reference issue numbers if applicable

## Project-Specific Patterns

### Commit Message Examples by Module

**Pipeline changes (src/pipeline/):**
```
feat: Add retry mechanism to LLM generator with exponential backoff
fix: Handle empty requirements gracefully in parser
refactor: Extract validation logic into separate validator class
```

**LLM Integration (src/llm/):**
```
feat: Add support for streaming responses in Databricks LLM client
fix: Correct timeout handling in structured output generation
```

**Validation (src/utils/):**
```
feat: Add interactive replacement for missing catalogs in validator
fix: Prevent duplicate catalog checks in table validation
```

**Testing (tests/):**
```
test: Add edge case tests for benchmark extraction
test: Mock Databricks API calls in integration tests
```

**Documentation:**
```
docs: Update CLAUDE.md with new skill creation workflow
docs: Add troubleshooting section to README
```

### Multi-file Changes

When committing changes across multiple files, group by logical change:

**Good approach:**
```bash
# Commit 1: Feature implementation
git add src/pipeline/generator.py src/models.py
git commit -m "feat: Add reasoning support to generation pipeline"

# Commit 2: Tests for the feature
git add tests/test_generation.py
git commit -m "test: Add tests for reasoning generation"

# Commit 3: Documentation
git add CLAUDE.md README.md
git commit -m "docs: Document reasoning generation feature"
```

**Avoid:** Bundling unrelated changes in one commit

## Testing Strategy

### Pre-commit Testing

Always run the full test suite:

```bash
.venv/bin/python -m pytest tests/ -v
```

### Test-driven Commits

For new features:
1. Write failing tests first
2. Commit tests: `test: Add tests for new feature X`
3. Implement feature
4. Commit implementation: `feat: Add feature X`

### Handling Test Failures

If tests fail:
- **Option 1:** Fix tests before committing (preferred)
- **Option 2:** Commit with WIP marker: `feat: Add feature X (WIP, tests failing)`
- **Never:** Commit broken code without noting it

## Git Workflow

### Branch Strategy

Main branch: `main`

For features:
```bash
git checkout -b feature/reasoning-support
# Make changes
git commit -m "feat: Add reasoning support"
git push origin feature/reasoning-support
# Create PR
```

### Staging Files

**Prefer explicit staging:**
```bash
git add src/pipeline/generator.py
git add tests/test_generation.py
```

**Avoid catch-all commands:**
```bash
# DON'T: Can accidentally include .env or other sensitive files
git add -A
git add .
```

### Commit Verification

After each commit:
```bash
git status  # Should show "nothing to commit"
git log -1  # Review the commit
git show    # See the actual changes
```

## Special Cases

### Emergency Fixes

For critical bugs in production:
```bash
git checkout -b hotfix/critical-validation-bug
# Fix the bug
git commit -m "fix: Prevent null pointer in table validator (critical)"
```

### Dependency Updates

```bash
git add requirements.txt
git commit -m "chore: Update pdfplumber to 0.10.3 for security fix"
```

### Configuration Changes

```bash
git add .cursor/rules/python-standards.mdc
git commit -m "chore: Update Python standards to require .venv usage"
```

### Reverting Changes

If a commit needs to be undone:
```bash
git revert <commit-hash>
# Creates new commit that undoes the changes
```

## Common Mistakes to Avoid

1. **Vague messages:** "Update files" → "feat: Add SQL validation to generator"
2. **Too broad:** Mixing features and fixes → Split into separate commits
3. **Missing context:** "Fix bug" → "fix: Handle None values in table schema validation"
4. **Wrong type:** Using "fix" for new features
5. **Committing secrets:** Always check for .env, tokens, credentials
6. **Skipping tests:** Always run tests before committing
7. **Using wrong Python:** Use `.venv/bin/python`, not global `python`

## Co-Authored-By Attribution

Always include when Claude assists:

```
feat: Add new feature

Implementation details here.

Co-Authored-By: Claude (databricks-claude-sonnet-4-5) <noreply@anthropic.com>
```

## Interactive Commit Messages

For complex commits, use a detailed format:

```
feat: Add interactive catalog replacement to validator

When table validation fails with missing catalogs, the system now:
- Identifies all missing catalog.schema combinations
- Prompts user for correct names
- Updates all references across the config
- Re-validates automatically

This reduces manual fixing time from ~10 minutes to ~30 seconds.

Implements: #123
Related: #456

Co-Authored-By: Claude (databricks-claude-sonnet-4-5) <noreply@anthropic.com>
```

## Quick Decision Tree

```
Changed code behavior?
├─ Adds new capability → feat:
├─ Fixes existing issue → fix:
├─ Improves performance → perf:
└─ Restructures code → refactor:

Changed tests only? → test:
Changed docs only? → docs:
Changed config/deps? → chore:
```
