# Pre-existing failure capture

> **Loaded when:** a gate fails on a file not in the diff — the "Pre-existing
> failure triage" paragraph in `work-loop` SKILL.md step 3 (GATES) tells you to
> load this reference for the full schema and heuristics.
> **What this is:** the complete doctrine behind that paragraph — entry schema,
> detection methods, known-skip heuristic, "made it worse" test, deduplication,
> and examples.

## Detection: is the failure pre-existing?

**Primary heuristic.** A gate failure is pre-existing when the failing file is
not in the current diff. Run `git diff --name-only HEAD` (or check the set of
files you edited) and compare. If the failing file isn't there, it's almost
certainly pre-existing — proceed to capture.

**Confirmation (when the primary is ambiguous).** Use when the failing file IS
in the diff but the failure looks unrelated to your change:

- **stash-check**: `git stash -u && <gate command> && git stash pop` — if the
  failure reproduces with your changes stashed, it predates your work.
- **HEAD-compare**: `git show HEAD:<failing-file>` — scan for a broken
  implementation, a wrong fixture, or a missing stub that was already broken at
  HEAD before you touched anything.

When the primary heuristic is unambiguous (the failing file is clearly not in
the diff), skip confirmation — the stash-check is an extra step, not the rule.

## Backlog entry schema

```toml
# pre-existing: <test_name or lint_rule> in <file> — present at HEAD before this session
# Fix: <one-line description of root cause and what needs to change>
# Unblocks when: <condition, or "someone decides to address the backlog">
{slug = "pre-existing-<short-name>", source = "pre-flight/<iso-date>"}
```

**`slug`**: always starts with `pre-existing-` so this class of entry is
greppable (`grep "pre-existing-" workspace.toml`). Use the failing test or lint
rule name as the short-name, hyphenated and trimmed to ≤30 chars.

**`source`**: `pre-flight/<iso-date>` — the ISO 8601 date (e.g. `2026-07-22`)
stamps when the failure was first captured. A months-old source value is a
staleness signal for the next agent who picks it up.

**Comment**: cold-start-sufficient. A reader coming back after months should
understand what failed, why it wasn't fixed at discovery time, and what condition
would unblock addressing it.

## Known-skip heuristic

Once an entry exists in `[backlog].open`, treat the matching failure as a
known-skip for the rest of the session — do not go to FIX. All three conditions
must hold:

1. The failing test name or lint rule matches a `pre-existing-*` entry slug.
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

When any of these appear, confirm with a stash-check. If the failure is worse
with your changes in than without, go to FIX.

## Deduplication procedure

Before writing a new entry, grep for the test or file name:

```bash
grep "pre-existing-" workspace.toml      # check for any pre-existing-* entry
grep "<failing-test-name>" workspace.toml # check by name
```

If an entry from a prior session already exists: update the comment only if new
context warrants it (e.g. you found the root cause). Never create a duplicate
entry for the same failure.

## Examples

**Test failure:**
```toml
# pre-existing: test_validate_empty_input in tests/test_validator.py — conftest
# fixture broken; test fails on import before the assertion fires.
# Fix: repair the fixture setup in conftest.py (mock for DatabaseClient is missing).
# Unblocks when: someone picks up the test-health cleanup.
{slug = "pre-existing-test-validate-empty", source = "pre-flight/2026-07-22"}
```

**Lint error:**
```toml
# pre-existing: E501 line-too-long in tools/legacy_script.py — ~40 lines over
# the 88-char limit; file predates the linter config and hasn't been touched since.
# Fix: run black on the file; no logic change expected.
# Unblocks when: a legacy-cleanup sprint is scheduled.
{slug = "pre-existing-e501-legacy-script", source = "pre-flight/2026-07-22"}
```
