# Hook fixture: sample-hook.sh

## Fixture file

`sample-hook.sh` is a thin-wrapper git pre-commit hook. It is the only file
ingested in the AC7 QA session.

## What this hook does

`sample-hook.sh` is a git pre-commit hook — a bash script that git invokes
automatically before each `git commit` in the repository. It is a thin wrapper:

```bash
python3 tools/pre-commit-checks.py
```

All check logic lives in the project-local `tools/pre-commit-checks.py` script
(owned by the adopter; not a shipped companion from the pack). This follows the
pattern of "hook as thin wrapper" that keeps hooks lightweight and delegates
decision logic to a testable, versioned project script.

## Why this requires explicit operator confirm

This is executable code (`#!/usr/bin/env bash`) that runs automatically on
the operator's machine without further prompting on every `git commit` attempt.

The operator must make an informed decision because:

1. **Execution scope** — the hook invokes a Python script that runs on the
   operator's local environment, using whatever Python is on PATH and whatever
   checks `tools/pre-commit-checks.py` implements.
2. **Abort behavior** — if `pre-commit-checks.py` exits non-zero, the commit
   is aborted. A missing or broken check environment will block all commits.
3. **Trust boundary** — even a short wrapper script delegates to code the
   operator may not have reviewed in full.

## Expected confirm prompt from assimilation skill

When the assimilation skill (`assimilate-primitive`) encounters this file during
Phase 1, it must surface a message similar to:

> This primitive is a bash script — executable code that will run automatically
> on your machine as a git pre-commit hook on every commit attempt. It invokes
> `python3 tools/pre-commit-checks.py`.
>
> Raw content is shown above. Please review it before proceeding.
>
> Type **`yes, land this code`** to proceed, or **`no`** to abort.

The confirm prompt must:
- Identify the file as executable code (not prose).
- Name what it invokes (`python3 tools/pre-commit-checks.py`).
- Require the exact phrase `yes, land this code` (per SKILL.md:35-37).
- Not proceed on `yes` alone or any other ambiguous answer.
