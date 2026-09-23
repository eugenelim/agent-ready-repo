# Verification ledger — frontend-experience-composition

Execution observations. The spec holds the contract and the plan the strategy;
what actually happened when a check ran belongs here.

## Pre-EXECUTE review, rounds 1–14

Fourteen adversarial rounds, each adjudicated independently before any repair.
**89 findings raised, 71 sustained, 18 refuted.** Every raw report and its paired
adjudication is under `.context/reviews/ce7b491a-3116-4656-8bc7-18b99b2c4477/`.

Rounds 1–4 found defects in the reconciled Draft. From round 5 on, the majority
of findings were defects introduced by the previous round's repair: two vacuous
controls, one deleted task, a grep that rejected the answer the plan instructs,
a duplicated command one field from the comment warning against duplication,
three invented exclusivity claims, and two ordering defects.

**Owner waiver, 2026-09-23.** No round returned the clean sentinel. The owner
approved the spec and plan with round 14's three repairs unreviewed, on the
evidence that the remaining findings were prose-tier and that four standing
instruments now screen the recurring classes faster than a review round does.

## Standing instruments

Each exists because a specific defect reached a review round, and each is
regression-proven against that defect — reverting the repair turns it red.

| Instrument | Built after | Catches |
| --- | --- | --- |
| Structural audit | a scripted edit deleted task T9 | missing tasks, criteria without modes, dangling AC references, under-declared `Touches:` |
| Red-before-work sweep | two vacuous controls shipped | a criterion that passes with the work undone; refuses to run while any criterion is unclassified |
| Exclusivity detector | two invented "the only X" claims | the claim shape in any phrasing; caught a third in the repair that introduced it |
| Schedule check | a guard whose run preceded the edit it covered | a guard scheduled before its last edit, and a task gated on a module it cannot reach |

## Claims the repository falsified

Three claims inherited rather than measured, each wrong:

- **"Three suites pin the frontend journey."** Measured: four. Nine test files
  read a `JOURNEY.md`; the others read `packs/core/JOURNEY.md`, a fixture, or
  pack names only. The count had three homes and drifted in all of them; it now
  has one.
- **"`catalogue verify` is the only check that sees a stale projection."**
  `catalogue self-host --check` sees it too. `catalogue lint --deep`,
  `lint-ruff`, `lint-mypy` and the pack suites do not — which is the half that
  matters and survives.
- **"Any `packs/**/.apm/` edit owes committed `.claude/` and `.agents/`
  projections."** True for `core`, false for the four packs this delivery
  touches: only `core` has declared host projections, so a non-core `.apm` edit
  leaves both `self-host --check` and `catalogue verify` at exit 0.

## Base

Rebased onto `origin/main` at `5a06c2bbf` mid-session, after
`check-base-freshness.py` reported `surface` — five commits behind, one of them
changing `spec-and-plan-contract.md`, the authority every adjudication cites.
Clean rebase, no conflicts; all four instruments re-run green against the new
base. The `brief:<slug>` pointer grammar that commit introduced is additive and
this spec's `Brief: none` stays valid.

## T1 — the derived state map

Walked all 18 states in `frontend-engineering/SKILL.md` § *3. State matrix*
against the seven state lines in `user-flow/assets/screen-brief-template.md`
and the six base states plus gated extension in
`design-review/references/quality-floor.md`.

**Bands.** explore 10, pilot 4, production 2, conditional 2. Cumulative
contract-field obligations 10 / 25 / 32, from 10 `explore+`, 15 `pilot+` and
7 `production+` annotations across 32 sections — recounted, not inherited.

**WCAG-bearing: 8 of 18.** Seven sit in `explore`; the eighth is conditional
and binds at every tier its trigger fires. Each cites the criterion the
judgement rests on, so a reviewer can check the flag rather than re-derive it:

| State | Criterion |
| --- | --- |
| loading | 4.1.3 Status Messages (AA) |
| error | 3.3.1 Error Identification (A); 3.3.3 Error Suggestion (AA) |
| success | 4.1.3 Status Messages (AA) |
| disabled | 4.1.2 Name, Role, Value (A) |
| keyboard-only | 2.1.1 Keyboard (A); 2.4.3 Focus Order (A); 2.4.7 Focus Visible (AA) |
| reduced-motion | 2.2.2 Pause, Stop, Hide (A); 2.3.1 Three Flashes (A) |
| high-zoom | 1.4.4 Resize Text (AA); 1.4.10 Reflow (AA) |
| destructive-confirmation | 3.3.4 Error Prevention (Legal, Financial, Data) (AA) |

### Delta from the plan's starting hypothesis

The hypothesis put all eight brief-carried states in `explore`. One moved.

**`permission/denied` is conditional, not banded.** Both source artifacts
describe it as an extension rather than a base state: the brief line reads
`permission/denied (if gated)`, and the quality floor heads it "Additional
gated-screen state", saying it *extends* the set for gated screens. Trigger:
the surface is behind authorization. It carries no WCAG criterion, so moving it
out of `explore` costs no accessibility — which is why the move was available
at all.

Everything else held. `offline` joins at production as predicted;
`destructive-confirmation` is conditional on an irreversible primary action;
the data-shape states join at pilot, with `long-content` placed at production
as an editorial-scale concern rather than a data-shape one.

### Why the flag is recorded rather than judged

A test that decided whether absence of a state breaches WCAG would be a test
nobody could make green. The map records the judgement and names its criterion;
the assertion reads the recorded value. A wrong flag is a review finding, not a
test failure, and that boundary is deliberate.

## T2 — the map and the owner label in four copies

`apply_contract.py` edited the frontend copy and wrote it to the other three, so
byte equality is produced rather than hand-matched. All four are 8,628 bytes.
The map sits under `States and Permissions`, after that heading's
`<!-- Required: pilot+ -->` annotation, so the annotation stays the first
non-blank line the drift checker's structural fingerprint reads.

T2's three declared checks, run after the edit:

| Check | Result |
| --- | --- |
| `python3 tools/repo/check_contract_drift.py --root .` | exit 0 |
| `## Frontend Engineering [owner: frontend-engineering]` present | 1 match |
| `python3 tools/lint-experience-agnostic.py` | exit 0 — clean |

The portability grep from `packs/AGENTS.local.md` § *Shipped pack content
carries no internal-governance citations* ran over all four changed files and
returned no match. The map cites WCAG success criteria, which are external.

### The red-before-work sweep needed a second direction

Running the sweep after T2 reported `AC-0002 is VACUOUS`. That was the
instrument working, not a defect: its CHANGE bucket asserts a criterion is red
*before* its work exists, and T2 is what makes AC-0002 green. Left as written,
every completed task would have reported as a failure and the sweep would have
gone blind for the eight tasks still to come — the same shape as the round-8
blind spot it was built to close.

It now binds each of the 15 CHANGE criteria to the plan task that implements it
and checks both directions: red while its task is pending, green once its task
has landed. A criterion with no owning task fails the sweep, so the binding
cannot be evaded by omission.

Regression-proven in both directions against the current tree: declaring T8 done
turns AC-0003, AC-0004, AC-0005 and AC-0047 red as `REGRESSED`; declaring T2
pending turns AC-0002 back to `VACUOUS`. Real run: 48 of 48 classified, 1
settled, 14 still owed, PASS.

## T3 — the state-coverage map's assertions

`tests/roster/test_experience_state_coverage_map.py`, ten assertions over three
artifacts none of which can see the others: the contract's map, the eighteen
states in `frontend-engineering/SKILL.md` § *3. State matrix*, and the state
lines in `user-flow/assets/screen-brief-template.md`.

Green against the real artifacts: 10 passed in 0.25s.

**Mutation proof.** The assertions take the artifact text as fixtures, so each
mutation is an injected copy and the tree is never edited. Every mutation is red,
and the baseline is green:

| Mutation | Caught by |
| --- | --- |
| a state removed | covers-every-floor-state, map-is-the-size, brief-line-resolves |
| a state duplicated | covers-every-floor-state, map-is-the-size |
| a brief line unmapped | every-brief-state-line-resolves |
| a tier band emptied | every-band-carries-at-least-one-unconditional |
| a conditional trigger stripped | a-conditional-state-names-its-trigger |
| a WCAG-flagged state moved out of `explore` | no-tier-drops-an-accessibility-bearing-state |
| a flag blanked | every-state-records-a-wcag-flag |
| a success criterion dropped | names-its-success-criterion |

The flag-blanking mutation is the one worth naming: the assertion refuses any
value but `yes` or `no`, so a missing flag fails rather than reading as `no`.
That is what stops the accessibility criterion passing by omission.

This module is not yet wired to CI. T7 adds its `build-check.yml` step above the
job's bulk `pytest tests/ -q` step; until then it runs but attributes no failure.

## T8 — the ADR and the supersession pointer

Ordinal allocated from current repository state, not from the staged draft's
assumption: `0122` is the highest record in the tree, so this one is `0123` —
`docs/adr/0123-experience-contract-frontend-section-owned-by-frontend-engineering.md`.

Shipped `Status: Accepted` rather than the `new-adr` procedure's default
`Proposed`. The owner has settled the decision, and the shape lint's
`_STATUS_TOKENS` admits either, so the lint alone would tick an "accepted" claim
on an unsigned record. AC-0003 reads the status for exactly that reason.

### A defect in the staged draft, corrected before shipping

The draft's `Related:` field linked two `docs/specs/` paths. The spec-and-plan
contract's *Cite upward, never downward* rule says an ADR does not link to a
spec, and the tree agrees: 1 of 123 existing records does it, 122 do not. The
field now cites ADR-0057 alone. The Context prose still names the frozen spec,
which is how the 44 records that mention a spec handle it — naming an artifact
in prose is not citing it.

### The two frozen records

| Record | Edit | Diff |
| --- | --- | --- |
| `digital-experience-contract/spec.md` | `Shipped` token annotated in place | 1 line changed |
| `digital-experience-contract/plan.md` | `Status` line added — the field was absent | 1 line added, 0 removed |

The plan's added line is the single metadata line the owner authorized (spec's
`Never do`, owner decision 2026-09-22); convention rule 4 otherwise reads an
append as a body edit. Nothing else in either file moved.

T8's declared checks, run verbatim from the criteria:

| Check | Result |
| --- | --- |
| AC-0003 — record exists, `Status: Accepted`, shape lint | exit 0 (123 read, 0 refused) |
| AC-0047 — `## Decision` section names `owner: frontend-engineering` | exit 0 |
| AC-0004 — spec `Status` form, diff touches only that line | both hold |
| AC-0005 — plan `Status` form, diff adds exactly that one line | both hold |
