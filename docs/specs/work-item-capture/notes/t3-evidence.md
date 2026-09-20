# T3 completion evidence

**Task:** an argv that is not read-only is refused at write time.
**Completed:** 2026-09-20. Blocked once at the frozen boundary; unblocked by
amendment 003, which the block itself established as a class defect.

## What shipped

- `verification_route.command` is an argv array in the canonical schema and
  the packaged mirror, byte-identical.
- `_validate_command_argv` enforces § D6 in the derivation's own check order:
  count, then element type, then the length checks, then the character class,
  then the path rules.
- The character class is anchored `\A`/`\Z` and covers every element after
  `argv[0]`, including `grep`'s pattern slot, which is exempt from the path
  rules only.
- The dot-component rule binds the § D6 stored-path set, including
  `verification_route.path` and `_expect_repo_path`'s `"."` early return.
- `packs/core/tests/skills/project-knowledge/argv_cases.py` is **generated**
  from the derivation script, not transcribed. Regeneration is tuple-equal,
  46 rows both sides.

## Verification, checked by the controller and not taken from the report

- **The shipped validator reproduces the derivation exactly**: all 46 case
  rows driven through `_validate_command_argv`, **0 mismatches**. This is the
  check that matters — the spec's table is generated output, so agreement
  between prose and code proves nothing on its own.
- **`_expect_repo_path` was not widened**: it still admits `.env`,
  `.git/config` and `.ssh/id_rsa`, so the 41 dot-containing paths in the
  committed store stay readable. Amendment 002 records why this matters.
- **The dot rule binds the path field**: `.ssh/id_rsa`, `.env` and `.`
  refused at `verification_route.path`.
- **A real stored legacy record still reads** through
  `validate_capture_request`, taken from `docs/knowledge/**/*.jsonl`.
- Full `packs/core/tests/skills/project-knowledge/` suite: **270 passed, 0
  failed**, against a 220 baseline. Roster test passes. Contract parity
  exits 0.

## Carried forward

`_deterministic_privacy_scan`'s `append`→`extend` fix landed here because the
type change crashed without it. It satisfies the "route every command element
to the scan" half of a criterion T5 owns; T5 should not re-implement it.
