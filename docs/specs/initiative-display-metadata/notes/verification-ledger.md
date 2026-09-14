# Verification ledger: initiative-display-metadata

Execution observations. Evidence, not contract.

Every observation below was taken on 2026-09-14, against `workspace.toml` as it
stood that day. The corpus values transcribed in T3 are evidence at a moment,
not a current claim: `ini-009`'s milestone is re-narrated whenever a slice
closes, so a later reader comparing this file to the tree should expect drift
and should not read it as a defect.

## T1 — emitter and tests

- Red proven before the emitter changed: the four cases failed with
  `AssertionError: 'workspace.toml' != 'Active Initiative'` and its siblings.
  Restored to green by editing the emitter, not the tests.
- `tools/test_workspace_status_cli.py` — 164 passed, 22 subtests, 90s.
- `catalogue self-host --check: ok`. All three copies of
  `workspace_status.py` hash `b59587dcb8fb03f5629afd8c8bfaa3c6`.
- `catalogue self-host --write` requires `--force` here, as the plan records:
  the bare form returns 2 on the dirty tree T1 leaves.

## T2 — skill contract

- Five redaction statements removed across three locations, including the two
  key-list rows carrying `see "redacted display fields" below` in lower case.
  Case-insensitive sweep over the whole file returns nothing for
  `redacted`, `always the literal`, or `slug alone`.
- Method count measured at **165**, matching the plan's predicted `163 -> 165`.
  Both pinned literals re-pinned with a dispositioned note covering this
  delta and the preceding `162 -> 163` re-pin, which had landed bare.
- `catalogue verify: ok`. All three copies of `SKILL.md` hash
  `c45b0ae66be8c3a8b36187334c731554`.

## T5 — activation eval harness disposition

`packs/core/.apm/skills/workspace-status/evals/evals.json` needs **no edit**,
and the reason is the point.

One of its twelve evals names an initiative name. Eval `id=1` asserts the
agent "Reports the active initiative name from the JSON output ('Example
Initiative')" and lists `Example Initiative` in `expect.output_contains`.

Under the shipped redaction that assertion was **unsatisfiable**: the
projection could only ever surface `workspace.toml`, so no correct agent
behaviour could have produced the expected output. Measured against an
equivalent fixture after T1, the projection returns
`name='Example Initiative'`, and the assertion is satisfiable.

So the harness was not a casualty of this change; it was independent evidence
of the defect the change fixes, written before the redaction landed and never
reconciled with it. Nothing about it needs updating. The eleven other evals
name no initiative name and are untouched.

`packs/AGENTS.md`'s eval-harness obligation is discharged by this record.

## T3 — real-artifact observation (AC-0001, manual-QA altitude)

Ran the shipped script against this repository's own `workspace.toml`. All four
active initiatives project the values that file assigns, compared field-by-field
against a `tomllib` parse of the same file:

```
ini-002 — Platform Core (milestone: P5 · Adopt (M1–M5 shipped))
ini-003 — Digital Experience Doctrine (milestone: M2 · Adoption + Shaping Doctrine)
ini-007 — Catalogue Contracts, Composition, Semantics, and Discovery
          (milestone: M2 · Authoring Discovery + Information Architecture)
ini-009 — Agent Skill Engineering (milestone: M3 · slices 3e and 4 shipped;
          3c unblocked, 3d needs 3c, 5 needs 3c, 6 closes — see the brief's
          slice table)
```

`ini-009`'s milestone is the hard case: 107 codepoints carrying `·`, `—`, a
semicolon and a straight apostrophe. It projects intact.

Observed at the JSON layer, which is the layer the Testing Strategy claims.
The line an agent finally renders from that JSON is documented by the template
AC-0003 pins and is not exercised here.

## T4 — pack release

- `packs/core` 2.26.1 -> 2.26.2. Patch, per `packs/AGENTS.md` § Version bump
  rule: changed content. `origin/main` was checked before choosing the number,
  because a duplicate bump is invisible to every local gate.
- `catalogue verify: ok`, run **after** the bump — its version-parity step, not
  `check-release-impact`, is what compares the two version values.
- `check-release-impact --base origin/main`: pass.

## Suites

- `tools/test_workspace_status_cli.py` — 164 passed before T2, 165 methods after.
- `tools/test_local_ci_shared_test_deduplication.py` — 52 passed with the
  re-pin in place.
