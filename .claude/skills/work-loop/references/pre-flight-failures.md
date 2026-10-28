# Pre-existing failure capture

> **Loaded when:** a gate fails on a file not in the diff — the "Pre-existing
> failure triage" paragraph in `work-loop` SKILL.md step 3 (GATES) tells you to
> load this reference for the full schema and heuristics.
> **What this is:** the complete doctrine behind that paragraph — file schema,
> detection methods, known-skip heuristic, "made it worse" test, deduplication,
> and examples.

## Detection: is the failure pre-existing?

**Primary heuristic.** A gate failure is pre-existing when the failing file is
not in the current diff. Run `git diff --name-only HEAD` (or check the set of
files you edited) and compare. If the failing file isn't there, it's almost
certainly pre-existing — proceed to capture.

**Confirmation (when the primary is ambiguous).** Use when the failing file IS
in the diff but the failure looks unrelated to your change:

- **worktree-check**: `git worktree add --detach ../pre-flight-check HEAD`, run
  `<gate command>` inside that directory, then
  `git worktree remove ../pre-flight-check`. If the failure reproduces without
  your uncommitted changes, it predates your work. A fresh worktree has no
  installed dependencies — for a gate that needs them, commit your work in
  progress and re-run the gate against the parent commit instead.
  **Not `git stash`:** `refs/stash` is not a per-worktree ref, so every linked
  worktree of the repository shares one stash stack — a stash pushed here can
  be popped from another one, and a gate that aborts between push and pop
  leaves your work sitting on it.
- **HEAD-compare**: `git show HEAD:<failing-file>` — scan for a broken
  implementation, a wrong fixture, or a missing stub that was already broken at
  HEAD before you touched anything.

When the primary heuristic is unambiguous (the failing file is clearly not in
the diff), skip confirmation — the worktree-check is an extra step, not the rule.

## Captured-item file

A pre-existing failure is a defect captured in its own file. Nothing is added to
`workspace.toml`.

```markdown
# Pre-existing test validate empty

- **Status:** Open
- **Kind:** defect

## Summary

test_validate_empty_input in tests/test_validator.py fails at HEAD: the conftest
fixture is broken and the test fails on import before the assertion fires.
Fix: repair the fixture setup in conftest.py. Captured 2026-07-22. Unblocks
when someone picks up the test-health cleanup.
```

**File name**: `docs/product/captured/pre-existing-<short-name>.md`. The name
always starts with `pre-existing-` so this class of item is greppable (`ls
docs/product/captured/pre-existing-*`). Use the failing test or lint rule name as
the short-name, lowercase, hyphenated, and trimmed to 30 characters.

**Preamble**: `Status: Open` and `Kind: defect`, each once. Add a `Detail:` line
when a note owns more context.

**Summary section**: cold-start-sufficient. A reader coming back after months
should understand what failed, why it wasn't fixed at discovery time, what
condition would unblock addressing it, and the ISO 8601 date (for example
`2026-07-22`) the failure was first captured. A months-old date is a staleness
signal for the next agent who picks it up.

**Closing**: when the failure is fixed, set `Status: Closed` and add a
`Resolution:` line (`fixed`, `declined`, or `superseded`) in the same file.

## Known-skip heuristic

Once a captured-item file exists with `Status: Open`, treat the matching failure as a
known-skip for the rest of the session — do not go to FIX. All three conditions
must hold:

1. The failing test name or lint rule matches a `pre-existing-*` captured-item file name.
2. Your diff does not touch the failing file or its direct import dependencies.
3. The failure mode is the same — identical test name, same error message prefix.

If any condition fails, treat the failure as in-scope and go to FIX. Don't use
this heuristic to bury a regression you might have introduced.

## "Made it worse" test

A pre-existing failure becomes in-scope if the diff made the existing breakage
worse. Concrete signs:

- A previously passing variant of the same test now also fails.
- The raw error count in the failing file grew.
- A new error message or traceback appeared alongside the known failure.

When any of these appear, confirm with a worktree-check. If the failure is worse
with your changes in than without, go to FIX.

## Deduplication procedure

Before writing a new file, search for the test or file name:

```bash
ls docs/product/captured/pre-existing-*             # any pre-existing item
grep -rl "<failing-test-name>" docs/product/captured/ # by name
```

If a file from a prior session already exists: update its summary only if new
context warrants it (e.g. you found the root cause). Never create a duplicate
file for the same failure.
