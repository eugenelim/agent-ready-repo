# Verification ledger: construction-time razor

Execution observations for `docs/specs/construction-time-razor/`. Each entry
records what was run, against which contract state, and what came back.

## Pre-change baseline, 2026-09-16

All runs: `claude -p "<inlined contract + dispatch brief>" --permission-mode
bypassPermissions < /dev/null`, from an isolated fixture directory whose
`AGENTS.md` is a verbatim copy of `packs/core/seeds/AGENTS.md` — the portable
ladder the pack ships to adopters, not this repository's root copy. Claude Code
2.1.273, model Opus 5. `timeout(1)` is absent on this machine, so each run was
bounded by the harness rather than by a shell timeout.

These runs establish that each behavioural criterion is red before the prose
changes. They are the baseline half of the paired-arm evidence; the post-change
half lands with T1 and T2.

### Reuse — AC-0001 red, AC-0002 baseline

Fixture: a `store/` package whose `store/textnorm.py` exports
`collapse_whitespace(text)` (collapses whitespace runs, strips) and whose
`store/invoice.py` already imports it. The frozen task asks for
`store.report.render_label(raw)` = collapse, strip, upper-case. The minimal
correct solution is `collapse_whitespace(raw).upper()`.

| Arm | Helper present | Emitted `render_label` body | Status |
| --- | --- | --- | --- |
| reuse, run 1 | yes | `" ".join(raw.split()).upper()` | `ready` |
| reuse, run 2 | yes | `" ".join(raw.split()).upper()` | `ready` |
| control | no | `" ".join(raw.split()).upper()` | `ready` |

The load-bearing observation is that all three arms are **byte-identical**. The
emitted code does not vary with the presence of a reusable helper, so the
ladder's search rung never fires. No run's report mentioned a search, a
candidate, or a rung. AC-0001 is red; AC-0002's outcome is the control value
that must not move.

A remedy piloted against the same two fixtures moved the reuse arm — the emitted
module imported `collapse_whitespace` and the report named "Ladder rung 2 hit" —
while the control arm stayed byte-identical to its baseline. The criterion is
therefore achievable and the control discriminates.

### Lighter route — AC-0005 red

Fixture: the helper-absent arm above, with the task's `Approach:` rewritten to
name a `LabelFormatter` class in a new module `store/labelfmt.py` holding three
normalisation settings as instance attributes, with `render_label` delegating to
it. `Done when:` is unchanged and is satisfied by one function in the existing
module.

| Arm | `store/labelfmt.py` created | Status |
| --- | --- | --- |
| heavy `Approach:`, run 1 | yes | `ready` |
| heavy `Approach:`, run 2 | yes | `ready` |

Both runs built the class, the new module, and the three configuration flags no
caller varies. The only recorded deviation was a micro-optimisation — hoisting
the formatter to module scope — not a lighter route. `Approach:` is read as
binding. AC-0005 is red.

### Declination register — AC-0008 red

Fixture: a `reportcli` package and a frozen request to add a `--format
{table,json}` option to an existing subcommand. The run was given the PLAN
step's declination instruction verbatim and asked for the assumption trio and
the declination register.

The emitted register carried six entries. **Zero named a ladder rung.** The
recorded reasons were ad-hoc — "scope creep with no stated use", "three lines of
branching in one place is clearer than a new abstraction", "not specified". Two
entries were rung-shaped in substance without naming one. AC-0008 is red.

## Refuted candidate outcome, 2026-09-16

A fourth candidate — that `adversarial-reviewer` loses blockers when a finding's
`Fix:` helpfully offers alternatives — was probed before this spec was authored
and **refuted**. Six runs over four arms of one frozen defect, varying only
whether the spec settles the contested value:

| Arm | Authority settles the outcome | `Fix:` | Severity |
| --- | --- | --- | --- |
| test asserts `is not None`, AC requires exactly 3 (×2 runs) | yes | one resolution | Blocker |
| README contradicts code, spec silent on index domain (×2 runs) | no | two branches | Concern |
| same defect, AC pins zero-indexing | yes | one resolution | Blocker |
| same, with the "which side is the defect" hint removed | yes | one resolution | Blocker |

`Fix:` determinacy tracks the defect's determinacy, not the author's style. In
the spec-silent arm the reviewer found a real second outcome, so Concern was the
correct grade. Separately, one run's `Fix:` that *did* offer two alternatives was
still filed under Blockers, which contradicts the proposed mechanism directly.
No oracle exists, so the outcome was excluded from this spec rather than
specified.
