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
