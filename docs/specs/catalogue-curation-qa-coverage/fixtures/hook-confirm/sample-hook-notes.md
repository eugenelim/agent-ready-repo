# Hook fixture: sample-hook.py

## Fixture file

`sample-hook.py` is a self-contained Python git pre-commit hook. It is the
only file ingested in the AC7 QA session.

## What this hook does

`sample-hook.py` is a git pre-commit hook — a Python script that git invokes
automatically before each `git commit`. It checks for staged `.env` files and
aborts the commit if any are detected:

```python
result = subprocess.run(
    ["git", "diff", "--cached", "--name-only"],
    capture_output=True, text=True, check=True,
)
staged = result.stdout.splitlines()
if any(f == ".env" or f.endswith("/.env") for f in staged):
    print("Error: .env file staged — refusing commit.", file=sys.stderr)
    sys.exit(1)
```

The hook is self-contained — no external companion is required. It can be
safely landed without depending on any other projected artifact. The
`sys.stdout.reconfigure` / `sys.stderr.reconfigure` guard immediately after
`import sys` is required by `packs/AGENTS.md:117-125` for any `.apm/` Python
script that prints to stdout or stderr — it is already present in the fixture. Using Python
(not bash) satisfies the repo policy that new additions to `tools/` must be
pure-stdlib Python (`AGENTS.md:238-241`); `build-self` projects the hook to
`tools/hooks/pre-commit.py`.

## Why this requires explicit operator confirm

This is executable code (`#!/usr/bin/env python3`) that runs automatically on
the operator's machine without further prompting on every `git commit` attempt.

The operator must make an informed decision because:

1. **Execution scope** — the hook runs `git diff --cached` on the operator's
   local environment. A misconfigured git environment could cause unexpected
   behavior.
2. **Abort behavior** — if the hook exits non-zero, the commit is aborted.
   Any staging of a `.env` file (including accidentally named files) blocks
   the commit.
3. **Trust boundary** — even a short script runs in the operator's Python
   environment; the subprocess call invokes the local git binary.

## Expected confirm prompt from assimilation skill

When the assimilation skill (`assimilate-primitive`) encounters this file during
Phase 1, it must surface a message similar to:

> This primitive is a Python script — executable code that, if installed as a
> git hook, will run automatically on your machine on every commit attempt.
> It blocks commits when a `.env` file is staged.
>
> Raw content is shown above. Please review it before proceeding.
>
> Type **`yes, land this code`** to proceed, or **`no`** to abort.

The confirm prompt must:
- Identify the file as executable code (not prose).
- Describe what it does (blocks staged `.env` files).
- Require the exact phrase `yes, land this code` (per SKILL.md:35-37).
- Not proceed on `yes` alone or any other ambiguous answer.
