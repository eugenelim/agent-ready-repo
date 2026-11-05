# Pre-existing defect: current ruff flags closure_index.py's nested ifs

- **Kind:** defect
- **Status:** Open
- **Discovered:** 2026-11-05, during the promotion-drain-hardening gates
- **File:** `packs/core/.apm/skills/close-work/scripts/closure_index.py:1375`

## What fails

`ruff check .` under ruff 0.15+ (verified on 0.17.4) reports one
`collapsible-if` (SIM102) violation at
`packs/core/.apm/skills/close-work/scripts/closure_index.py:1375`, inside
`close-work`'s brief-route refusal handling. Under ruff 0.14.0 the same
tree — including the file byte-for-byte — passes every check.

## Why it is pre-existing

The failing file is byte-identical to `origin/main` at `74f4b7248` (merged
in PR #1665); the promotion-drain-hardening branch never touches it. CI
installs ruff unpinned (`pip install ruff`), so a rule-behavior change in
ruff 0.15–0.17 re-flags code that was green when it merged.

## Known-skip treatment

Gate runs on this branch treat the violation as a known skip and pin ruff
0.14.0 — the version the file was green under — for the local gate
evidence. Fixing the nested-`if` is a one-line `and` merge owned by the
`close-work` skill, out of this delivery's scope.
