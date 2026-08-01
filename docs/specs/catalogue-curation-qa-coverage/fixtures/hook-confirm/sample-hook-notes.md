# Hook fixture: sample-hook.sh

## Fixture bundle

This fixture bundle contains two files ingested together:
- `sample-hook.sh` — the pre-commit hook (thin wrapper calling the companion at its
  projected path: `python .agentbundle/bin/pre-commit-checks.py`).
- `scripts/pre-commit-checks.py` — the companion script source (stub, exits 0).
  During landing, it is placed at `packs/core/.apm/adapter-root-bins/pre-commit-checks.py`
  and projected to `.agentbundle/bin/pre-commit-checks.py` at repo scope by `build-self`.
  The hook body calls it at that projected path.

## What this hook does

`sample-hook.sh` is a git pre-commit hook — a bash script that git invokes
automatically before each `git commit` in the repository. It is a thin wrapper:

```bash
python .agentbundle/bin/pre-commit-checks.py
```

All check logic (formatting, lint, type-checking, tests) lives in
`scripts/pre-commit-checks.py`. The hook body itself is minimal, following the
pattern of "hook as thin wrapper over a deterministic script" that keeps hooks
lightweight and testable independently of git's event system.

## Why this requires explicit operator confirm

This is executable code (`#!/usr/bin/env bash`) that runs automatically on
the operator's machine without further prompting on every `git commit` attempt.

The operator must make an informed decision because:

1. **Execution scope** — the hook calls a Python script that runs on the
   operator's local environment, using whatever Python is on PATH and whatever
   packages are installed locally.
2. **Abort behavior** — if `pre-commit-checks.py` exits non-zero, the commit
   is aborted. A broken check environment will block all commits.
3. **Trust boundary** — even a short wrapper script delegates to Python code
   the operator may not have inspected. The same trust surface applies.

Note: the anti-pattern `anti-patterns.md:38-42` warns against hooks doing
heavy logic directly (mypy, pytest embedded in the hook body). This fixture
correctly avoids that: the hook body is a thin wrapper, delegating to a script.
The confirm gate fires on *any* executable code, not just heavy-logic hooks.

## Expected confirm prompt from assimilation skill

When the assimilation skill (assimilate-primitive) encounters this file during
Phase 1, it must surface a message similar to:

> This primitive is a bash script — executable code that will run automatically
> on your machine as a git pre-commit hook on every commit attempt. It invokes
> `python .agentbundle/bin/pre-commit-checks.py`.
>
> Raw content is shown above. Please review it before proceeding.
>
> Do you want to land this hook? (yes / no)

The confirm prompt must:
- Identify the file as executable code (not prose).
- Name what it executes (`python .agentbundle/bin/pre-commit-checks.py`).
- Ask for an explicit "yes" before landing.
- Not proceed on ambiguous answers.
