# Hook fixture: sample-hook.sh

## Fixture file

`sample-hook.sh` is a self-contained git pre-commit hook. It is the only file
ingested in the AC7 QA session. There is no external companion — all check logic
runs inline.

## What this hook does

`sample-hook.sh` is a git pre-commit hook — a bash script that git invokes
automatically before each `git commit` in the repository. It runs two quality
gates inline:

```bash
python3 -m ruff check . --quiet
python3 -m mypy packages/agentbundle/ --quiet
```

The hook is self-contained: it does not shell out to an external companion
script. This keeps the fixture simple and avoids a missing-companion failure
at landing time.

## Why this requires explicit operator confirm

This is executable code (`#!/usr/bin/env bash`) that runs automatically on
the operator's machine without further prompting on every `git commit` attempt.

The operator must make an informed decision because:

1. **Execution scope** — the hook runs Python tool invocations (`ruff`, `mypy`)
   that affect the local environment and can fail commits.
2. **Abort behavior** — if either tool exits non-zero, the commit is aborted.
   A missing tool or a scope mismatch will block all commits.
3. **Trust boundary** — even a short script runs with the operator's full
   local privileges.

Note: the anti-pattern `anti-patterns.md:38-42` warns against hooks doing
heavy logic directly (mypy, pytest embedded in the hook body). This fixture
deliberately includes inline mypy/ruff to exercise the anti-pattern detection
for completeness; the confirm gate fires on *any* executable code regardless
of whether the hook body is heavy or thin.

## Expected confirm prompt from assimilation skill

When the assimilation skill (`assimilate-primitive`) encounters this file during
Phase 1, it must surface a message similar to:

> This primitive is a bash script — executable code that will run automatically
> on your machine as a git pre-commit hook on every commit attempt.
>
> Raw content is shown above. Please review it before proceeding.
>
> **yes, land this code** / no

The confirm prompt must:
- Identify the file as executable code (not prose).
- Use the contracted phrase: require `yes, land this code` (not just `yes`).
- Ask for an explicit answer before landing.
- Not proceed on ambiguous answers.
