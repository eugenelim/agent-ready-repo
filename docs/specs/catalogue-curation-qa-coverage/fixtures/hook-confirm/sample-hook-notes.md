# Hook fixture: sample-hook.sh

## Fixture file

`sample-hook.sh` is a self-contained git pre-commit hook. It is the only file
ingested in the AC7 QA session.

## What this hook does

`sample-hook.sh` is a git pre-commit hook — a bash script that git invokes
automatically before each `git commit`. It checks for staged `.env` files and
aborts the commit if any are detected:

```bash
if git diff --cached --name-only | grep -q '\.env$'; then
  echo "Error: .env file staged — refusing commit." >&2
  exit 1
fi
```

The hook is self-contained — no external companion is required. It can be
safely landed without depending on any other projected artifact.

## Why this requires explicit operator confirm

This is executable code (`#!/usr/bin/env bash`) that runs automatically on
the operator's machine without further prompting on every `git commit` attempt.

The operator must make an informed decision because:

1. **Execution scope** — the hook runs on the operator's local environment
   using whatever `git` is on PATH. A misconfigured or unexpected environment
   could cause false positives.
2. **Abort behavior** — if the hook exits non-zero, the commit is aborted.
   Any staging of a `.env` file (including accidentally named files) blocks
   the commit.
3. **Trust boundary** — even a short script delegates execution to the
   operator's shell environment.

## Expected confirm prompt from assimilation skill

When the assimilation skill (`assimilate-primitive`) encounters this file during
Phase 1, it must surface a message similar to:

> This primitive is a bash script — executable code that will run automatically
> on your machine as a git pre-commit hook on every commit attempt. It blocks
> commits when a `.env` file is staged.
>
> Raw content is shown above. Please review it before proceeding.
>
> Type **`yes, land this code`** to proceed, or **`no`** to abort.

The confirm prompt must:
- Identify the file as executable code (not prose).
- Describe what it does (blocks staged `.env` files).
- Require the exact phrase `yes, land this code` (per SKILL.md:35-37).
- Not proceed on `yes` alone or any other ambiguous answer.
