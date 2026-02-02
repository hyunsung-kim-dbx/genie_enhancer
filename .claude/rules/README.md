# Claude Code Rules

This directory contains project-specific rules that Claude Code must follow when working with this codebase.

## Active Rules

- **python-venv.md**: Python virtual environment usage (CRITICAL - always use `.venv/bin/python`)
- **app-permissions.md**: Databricks App deployment and permissions safety

## How Rules Work

Rules in this directory override Claude Code's default behavior and enforce project-specific standards. Claude Code automatically reads these rules before suggesting changes or running commands.

## When to Create New Rules

Create a new rule file when:
- A pattern needs to be enforced consistently across all sessions
- Default behavior could cause issues in this project
- Team conventions differ from general best practices
- Security or compliance requirements exist

## Rule File Format

Rules should be clear, concise markdown files that:
- Start with a clear title
- Explain WHY the rule exists
- Provide concrete examples (DO and DON'T)
- Include exceptions if any
