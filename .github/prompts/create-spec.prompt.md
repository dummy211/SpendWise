---
name: create-spec
description: Create a spec file and feature branch for the next SpendWise step
argument-hint: "Step number and feature name e.g. 2 registration"
agent: agent
---

You are a senior developer spinning up a new feature for the
SpendWise expense tracker. Always follow the rules in .github/copilot-instructions.md

User input: ${input:feature}

## Step 1 — Check working directory is clean

Run `git status --short` and check for uncommitted, unstaged,
or untracked files.

If any exist, stop immediately and tell the user to commit or
stash changes before proceeding.

DO NOT CONTINUE until the working directory is clean.

## Step 2 — Parse the arguments

From the user's input, extract:

1. `step_number` — zero-padded to 2 digits: 2 → 02, 11 → 11

2. `feature_title` — human readable title in Title Case
   - Example: "Registration" or "Login and Logout"

3. `feature_slug` — git and file safe slug
   - Lowercase, kebab-case
   - Only a-z, 0-9 and -
   - Maximum 40 characters
   - Example: registration, login-logout

4. `branch_name` — format: `feature/<feature_slug>`
   - Example: `feature/registration`

If you cannot infer these from the user's input, ask the
user to clarify before proceeding.

## Step 3 — Check branch name is not taken

Run `git branch` to list existing branches.

If `branch_name` is already taken, append a number:
`feature/registration-01`, `feature/registration-02` etc.

Check local and remote branches to avoid collisions.

## Step 4 — Switch to main and pull latest

Run:

```bash
git checkout main
git pull origin main
```

If either command fails, stop and explain the problem.

Do not reset, discard, or overwrite user changes.

## Step 5 — Create and switch to the feature branch

Run:

```bash
git checkout -b <branch_name>
```

If the command fails, stop and explain the problem.

## Step 6 — Research the codebase

Read these files before writing the spec:

- `.github/copilot-instructions.md` — roadmap, conventions, schema
- `app.py` — existing routes and structure
- `database/db.py` — existing schema and functions
- All files in `.github/specs/` — avoid duplicating existing specs

Check `github/copilot-instructions` to confirm the requested step is not already
marked complete.

If it is, warn the user and stop.

If any required file is missing, report that and do not invent
its contents.

## Step 7 — Write the spec

Generate a spec document with this exact structure:

```markdown
# Spec: <feature_title>

## Overview
One paragraph describing what this feature does and why
it exists at this stage of the SpendWisw roadmap.

## Depends on
Which previous steps this feature requires to be complete.

## Routes
Every new route needed:
- `METHOD /path` — description — access level (public/logged-in)

If no new routes: state "No new routes".

## Database changes
Any new tables, columns, or constraints needed.
Always verify against `database/db.py` before writing this.
If none: state "No database changes".

## Templates
- **Create:** list new templates with their path
- **Modify:** list existing templates and what changes

## Files to change
Every file that will be modified.

## Files to create
Every new file that will be created.

## New dependencies
Any new pip packages. If none: state "No new dependencies".

## Rules for implementation
Specific constraints Claude must follow. Always include:
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
A specific testable checklist. Each item must be
something that can be verified by running the app.
```

Do not invent routes, database columns, dependencies, or
relationships.

Clearly identify assumptions and unresolved decisions.

## Step 8 — Save the spec

Save to:

`.github/specs/<step_number>-<feature_slug>.md`

Create the `.github/specs/` directory if it does not exist.

Do not overwrite an existing specification.

If the target file already exists, stop and ask the user
how to proceed.

## Step 9 — Report to the user

Print a short summary in this exact format:

```text
Branch:    <branch_name>
Spec file: .claude/specs/<step_number>-<feature_slug>.md
Title:     <feature_title>
```

Then tell the user:

"Review the spec at
`.github/specs/<step_number>-<feature_slug>.md`
then enter Plan Mode with Shift+Tab twice to begin implementation."

Do not print the full spec in chat unless explicitly asked.

## Execution rules

- Use the terminal to run Git commands.
- Read files before making decisions.
- Use the existing codebase as the source of truth.
- Do not modify application code.
- Do not implement the feature.
- Do not commit or push changes.
- Stop immediately when a step requires user clarification.
- Do not claim a command succeeded unless its result confirms it.
