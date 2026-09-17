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

## Post-change scored runs, 2026-09-16

Same harness and invocation as the baseline, driven by
`notes/probes/run-probe.sh`, which materialises every fixture and holds no
expected rung. Two consecutive runs per arm; a criterion holds only if both hold.

### Gated results

| Criterion | Runs | Result |
| --- | --- | --- |
| AC-0001 reuse fires | 2/2 | pass |
| AC-0003 no new module on the helper-absent control | 2/2 | pass |
| AC-0004 status `ready` on that control | 2/2 | pass |
| AC-0005 inadequate candidate not delegated to | 1/2 | see Amendment 1 |
| AC-0006 rejected candidate named | 2/2 | pass after the rule repair |
| AC-0007 no new module on the heavy `Approach:` | 2/2 | pass after the rule repair |
| AC-0008 status `ready` there | 2/2 | pass |
| AC-0009 substitution recorded under Deviations | 2/2 | pass |
| AC-0010 required construction still built | 2/2 | pass |
| AC-0011 no false lighter-substitution claim | 2/2 | pass |
| AC-0012 refusal on the no-route control | 1/2 | see Amendment 1 |
| AC-0019 `Done when:` holds on every satisfiable fixture | 2/2 | pass |

### Two repairs the first post-change run forced

**The search receipt was conditional.** The rule said to name a rejected
candidate *if the search found one*, which a run that never searched satisfied by
saying nothing: AC-0006 failed 0/2, with no mention of the candidate, the search
or the module in either report. The receipt is now required on every run — the
hit reused, each candidate found and why it did not fit, or that the search found
nothing. AC-0006 then held 2/2.

**The lighter-route clause was permissive.** "A route lighter than `Approach:` is
yours to take" produced the heavier construction in one run of two. Reworded to
direct the lighter rung, AC-0007 held 2/2.

Both were repairs to the shipped rule against sound criteria, so neither needed a
contract amendment.

### Recorded, ungraded observations

The rung each report named, which no criterion grades:

| Fixture | Run 1 | Run 2 |
| --- | --- | --- |
| reuse | rung 2 | rung 2 |
| helper-absent | rung 3 | none named |
| inadequate candidate | rung 2 | rung 3 |
| heavy `Approach:` | rung 2 | rung 2 |
| heavy required | rung 3 | none named |

The same one-line expression was reported as rung 3 in one fixture and rung 6 in
an earlier run of another, and no rung at all in two runs. Which rung applies is
not stable across runs of an unchanged fixture, which is the evidence behind the
owner's decision to retire the rung-grading criteria rather than gate on them.

Declination register, against a baseline of six entries and zero rungs named:

| Fixture | Run 1 | Run 2 |
| --- | --- | --- |
| declination | 5 entries, 5 named a rung | 6 entries, 5 named a rung |
| non-rung control | the localisation decline recorded "**Explicit hard requirement scope**, not a rung" | requirement cited, no rung fabricated |

The non-rung exception fired as designed: the decline that no rung covers said so
in the rung's place rather than having a rung fitted to it.

### Content pins

Nine mutations, each reddening exactly the pin that owns its obligation:
dropping the stopping-rung requirement, the bounded search, the unconditional
receipt, the directive lighter rung, the `failed` reframing, the declination
rung, its non-rung exception, and adding a third copy of the ladder. Baseline
green at six pins.

### Regression floor

`python3 -m pytest packs/core/tests/skills/work-loop/ -q` — 1084 passed, 5
skipped, 46 subtests passed, exit 0, 10m29s, run on a restored tree after the
mutation sweep. An earlier run of the same suite overlapped the mutation sweep
and is not used as evidence.

## Amendment 1 — owner authority and reason

Owner authority: the scope owner authorised the amendment in session on
2026-09-16, choosing the full amendment sequence over shipping the contract
unamended.

Reason: four specification errors this delivery's own scored runs established.
Two criteria named one correct answer where the shipped contract admits two, so
each flipped between defensible outcomes on consecutive runs of an unchanged
fixture; one cited a file that does not exist; and one obligation had no field in
the target schema to live in.

- **AC-0005 retired.** Run 1 emitted `collapse_runs(raw).strip().upper()`,
  reusing the shared collapse logic and supplying the missing strip; run 2
  declined the helper and solved the task inline. Both satisfy `Done when:` and
  both are defensible, so the criterion graded a preference. AC-0006 and AC-0019
  own that fixture.
- **AC-0012 narrowed** from "status is `failed`" to "does not claim `ready`;
  refuses with `failed` or `blocked`". Run 2 returned `blocked` because the
  fixture's two `Done when:` conditions are mutually exclusive, which the shipped
  contract defines as a supervisor decision. Neither run claimed `ready`, which
  is what the criterion exists to catch.
- **AC-0017 corrected** from `CHANGELOG.md`, which does not exist, to
  `docs/product/changelog.md`. The obligation is unchanged and is independently
  pinned by `tests/roster/test_verification_ledger_contract.py`.
- **T3's register disclosure reworded.** `evals.json` admits only `id`,
  `prompt`, `expected_output`, `assertions` and an optional `files`. The
  disclosure now rides the case `id` prefix and the changelog entry rather than
  corrupting `expected_output` or inventing a schema field.

## Re-scored against the reviewed instrument, 2026-09-17

The quality pass found nine defects in the probe harness itself — the instrument
behind every figure above. Delegation was proved by grep, so a comment passed and
an aliased import failed; the no-new-module checks forbade one filename; the
required-construction control asserted only that a file existed; the harness
exited zero on an unknown fixture name; and the fixtures documented a `pytest`
gate that could never pass. All nine were repaired, the predicates were
self-tested against known-good and known-bad inputs first, and every arm was
re-scored: `claude-opus-5`, Claude Code 2.1.274, two runs per arm, 900s bound.

**31 gated checks passed, 5 failed, 0 infrastructure failures.** Every failure is
in one arm, `heavy_required`, and the cause is that arm's design rather than the
shipped rule.

| Criterion | Runs | Result |
| --- | --- | --- |
| AC-0001 reuse fires, proved by AST | 2/2 | pass |
| AC-0003, AC-0004 helper-absent control | 2/2 | pass |
| AC-0006 candidate named | 2/2 | pass |
| AC-0007, AC-0008, AC-0009 lighter route | 2/2 | pass |
| AC-0012 refusal reachable | 2/2 | pass |
| AC-0019 every satisfiable fixture, all conditions | 2/2 | pass |
| AC-0010, AC-0011 required construction | 0/2 | see Amendment 2 |

## Amendment 2 — owner authority and reason

Owner authority: the scope owner authorised the amendment in session on
2026-09-17, choosing to redesign the control fixture rather than weaken or
retire the guard.

Reason: `heavy_required` never presented the case it was built to test. Both
runs emitted a single module-level `_normalise` helper with keyword settings and
three renderers passing different settings to it — no class, no new module. That
satisfies every `Done when:` condition exactly, and satisfies the fixture spec's
own AC-4 ("the three differ only in their normalisation settings; a fourth
caller adds settings, never a fourth copy of the normalisation code"), because
there is exactly one copy of the normalisation. Run 2's report named the
substitution, cited AC-4 holding, and said it had corrected `Approach:` in
place. The implementer was right on both runs.

The fault is in the fixture and its criteria:

- **A shared helper satisfies the requirement**, so the `LabelFormatter` class
  was never genuinely required. The arm could not detect the rule refusing
  necessary structure, because no necessary structure was present to refuse.
- **AC-0010 named a mechanism**, the `LabelFormatter` class in
  `store/labelfmt.py`, rather than an outcome. The spec template warns that
  naming a helper or a call sequence is the give-away that the content belongs
  in the plan.
- **AC-0011 fires on correct behaviour.** It failed a report for claiming a
  lighter substitution, but the substitution was real and the claim was true.

The fixture is rebuilt so the construction is genuinely required: it ships a
pre-existing shared consumer that renders through an object protocol its callers
must satisfy, which a bare parameterised function cannot express, and which the
implementer may not rewrite. The criteria become outcome-shaped against it.
