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

## T9 — the fifth tier table

The page carried a fifth statement of the tier ladder. It said seven fields are
required at explore tier while the contract annotates ten — and its own Explore
row then listed ten, so the page disagreed with itself as well as with the
contract.

Rewritten to reference the annotations rather than restate them, which removes
the home instead of correcting a count that would go stale again:

| Row | Before | After |
| --- | --- | --- |
| Explore | ten named fields | the fields the contract annotates `Required: explore+` |
| Pilot | fourteen named fields | everything in Explore, plus `Required: pilot+` |
| Production | eight named fields | everything in Pilot, plus `Required: production+` |

The two prose counts went the same way, and the section now says the annotations
are the authority, so a reader is sent to the template rather than to a list.

Both citations of the deprecated `tools/check-contract-drift.py` shim — which
forwards to the real checker and is kept only until the next minor release — now
name `tools/repo/check_contract_drift.py`.

| Check | Result |
| --- | --- |
| AC-0016 negated grep, run verbatim | exit 0 — no per-tier field count remains |
| `tools/check-guide-index.py` | exit 0 — 21 active packs present |
| AC-0017 | Review-only; the column references and no longer enumerates |

## T4 — the frontend journey

### The pins, enumerated before the edit

The `Always do` rule requires enumerating every existing assertion over
`packs/frontend-engineering/JOURNEY.md` before editing it. **Sixteen**, across
the four suites AC-0035 names:

| Suite | Journey-reading assertions |
| --- | --- |
| `test_rendered_page_journey_promise.py` | 8 — skip-cost unchanged, unverified-items reason, step names the inspection, its output, the named skip, gate checks the observations field, breakpoint input, minimum input |
| `test_rendered_page_reviewer_sight.py` | 2 — reviewer reads the page; metadata no longer advertises a diff-only reviewer |
| `test_rendered_page_verdict.py` | 3 — gate told to check the verdict, verdict reaches all three result surfaces, the pin spares the sentences that must survive |
| `tools/test_journey_editorial_decisions.py` | 3 — canonical human gates, approved eyebrow and transcript, editorial copy confined |

No edit landed in a stage carrying the byte-exact `PINNED_SKIP_COST` block, so
the spec's `Ask first` route was not needed.

### The edits

Five anchored single-match replacements, each asserting its anchor occurs
exactly once, so a drifted anchor stops the run rather than matching something
adjacent:

1. The depth sub-stage, placed after stage 1's `**State:**` label so both
   journey lints' per-stage label scan still reads the parent's labels.
2. The three crossing artifacts named in stage 2, which previously asked for
   "the surface brief" as if from nowhere.
3. Allowance 1 — a contract proportional to the surface's risk and scope.
4. Allowances 2 and 3 — inapplicable states omitted with a reason, and a
   retrofit narrowing the state matrix.
5. Allowance 4 — the CSS token gate as optional where stylelint is configured.

The sub-stage states the ladder as 10 / 25 / 32 and writes the `explore` state
subset as one backticked comma-separated line, the form T7's parser reads. Its
ten states are exactly the map's `explore` band.

| Check | Result |
| --- | --- |
| AC-0035 — the four suites, all 16 pins | 358 passed in 1.51s |
| `tools/lint-pack-journeys.py` | exit 0 — 14 files valid |
| `tools/lint-journey-contract.py` | exit 0 — 20 journeys conform |
| `tools/lint-web-journey-parity.py` | exit 0 — 20 in parity |
| Portability grep over the edited journey | no match |

The web copy was regenerated in this task rather than at the end, per the
`Always do` rule: no lint compares the source and the committed copy.

## T6 — the contract is loaded by a skill in each pack

`frontend-engineering/SKILL.md` names it at the state-matrix step and
`design-review/SKILL.md` at the quality-floor step, which are the steps the
state-coverage map serves. Both references sit before the state table, so T3's
parse of `### 3. State matrix` is untouched — re-run after the edit: 10 passed.

### A ceiling this edit crossed, found by a lint the plan did not name

The first version added a five-line paragraph. `catalogue lint --deep` then
turned a `CAT-S003` warning into an **ERROR**: the frontend `SKILL.md` body sits
at exactly 1,000 lines, and the error threshold is *exceeds* 1,000. The whole
tree went from `ok: 71 finding(s)` to `FAIL: 71 finding(s)` on six added lines.

Proven mine rather than inherited: stashing the edit returns the tree to
`ok: 71`, and restoring it returns `FAIL: 71`. The reference is now folded into
the existing sentence, so the file is 1,004 lines before and after — byte-level
delta on one line only — and the lint reads `ok: 71` again.

The lesson generalises past this file: a pack `SKILL.md` can sit exactly on the
`CAT-S003` ceiling, where any added line is a gate failure and no local lint in
`make lint-ruff lint-mypy` reports it.

| Check | Result |
| --- | --- |
| AC-0006 / AC-0007 — path named and resolves on disk | both OK |
| T3's state-coverage assertions, after this task's edit | 10 passed |
| `catalogue lint --deep` | `ok: 71` — unchanged from HEAD |
| AC-0043 `catalogue verify` | exit 0 |
| `catalogue self-host --check` | exit 0 |
| `tools/lint-experience-agnostic.py` | exit 0 |
| Frontend pack suites | 355 passed |

`catalogue verify` and `self-host --check` both exiting 0 on an unregenerated
tree re-confirms the ledger's third falsified claim: only `core` has declared
host projections, so these non-core `.apm/` edits owe no `.claude/` or
`.agents/` delta.

## T5 — the design journey

### The pins, enumerated before the edit

Three, all in `tools/test_journey_editorial_decisions.py`, which globs every
pack journey: the canonical human-gate mapping (39 gates across all journeys),
the priority eyebrow and transcript comparison, and the confinement check that
no other journey gains an eyebrow or transcript.

The transcript pin was the one worth checking before editing the illustrative
state lists. It compares against a ledger for `PRIORITY = core,
product-engineering, release-engineering` only, and `experience-design` is not
in that set; its two illustrative lists are body prose, not frontmatter. So
realigning them touches no pinned copy. Suite after the edit: 3 passed.

### The edits

`relatedJourneys` gains `frontend-engineering`, making the link reciprocal. Two
`####` sub-stages were added after their parent stage's `**State:**` label — the
minimal viable thread and the depth selector — and a third section names the
three crossing artifacts with their `<output_dir>`-relative paths.

The say-this table gained a `Needed?` column, one value per row, each resolved
toward the guide that owns it. The three illustrative state lists — two in
`JOURNEY.md`, one in `README.md` — were realigned from
`default · loading · error · success · empty` to the seven-state `explore`
opening set: `default` is not a floor state, and `partial` and `disabled` were
missing. No shipped lint reads any of the three, which is why the walk reached
all three rather than only the one the journey edit touched.

`DESIGN.md`'s sentence two lines above the thread argued against shortcuts while
the section below named one. It now states what a skipped step costs and says
the thread is chosen against that cost. Both documents name the same four steps.

### Mutation proof — the two say-this assertion groups

| Mutation | Result |
| --- | --- |
| a row's optionality blanked | red |
| a row carrying two values | red |
| `design-system` flipped against its how-to | red |
| `content-design` flipped against its how-to | red |
| baseline, unmutated | green |

The flip mutations matter because both values are read from their tables rather
than pinned: the assertion is that the two surfaces agree, not that either says
a particular word today.

| Check | Result |
| --- | --- |
| The three journey lints | all exit 0 — 14 files valid, 20 conform, 20 in parity |
| `tools/test_journey_editorial_decisions.py` | 3 passed |
| The two roster files | 15 passed |
| `tools/lint-experience-agnostic.py` | exit 0 |
| Portability grep over the three edited files | no match |

The module is created here with its two say-this groups only. T7 extends it with
the ladder and composition groups, which need both journeys to state a ladder.

### A scoping error worth recording

Verification here first ran `pytest tools/... tests/roster/` — the whole roster
directory, which is the 7–12 minute suite this delivery is explicitly not to run
locally. It was stopped and re-run against the two named files. Naming a
directory rather than the files is how that suite gets run by accident.

## T7 — the tier-count test and the CI wiring

The composition module now carries all three of its remaining groups; 18
assertions green against the real artifacts, 28 across both roster files.

### A control that could not fail, found by its own mutation

The crossing-artifact assertion used plain substring containment
(`path not in text`). Changing `tokens/<slug>.md` to `tokens/<slug>.mdx` in the
design journey left the test **green**: the correct path is a prefix of the
broken one, so containment cannot tell them apart. AC-0019 asks this assertion
to decide that both journeys name the three artifacts by their paths, and for
this class of defect it decided nothing.

It now matches the backticked form both journeys actually write, `` `<path>` ``,
which closes the token on the right. The mutation is red and the other six stay
red. The two remaining containment checks in the module were walked and left
alone: the allowance cues match the words that carry an allowance, and the
minimal-thread check matches a phrase — neither has a prefix relation to guard.

### Mutation proof — all three groups

| Mutation | Result |
| --- | --- |
| frontend journey states `pilot` as 24 rather than 25 | red |
| WCAG-bearing `high-zoom` dropped from a stated explore subset | red |
| production state `offline` added to a stated explore subset | red |
| the `relatedJourneys` entry removed | red |
| a crossing-artifact path broken | red — green before the repair above |
| the inapplicable-states allowance removed | red |
| the minimal-thread heading removed | red |
| baseline, unmutated | green |

The counts are computed from the contract's own annotations rather than stored,
so the assertion is that the two surfaces agree, not that either states 10 / 25
/ 32 today.

### CI wiring

One named step per module, both registered on **both** roster axes — a
`_LOCAL_STEP_DISPOSITION` entry of the `LOCAL("test-after-build-check")` shape
and membership in `_GATE_MAIN_CHECKS`, which synthesizes the phase entry. A step
on one axis only raises "has no phase-and-dependency axis entry". Neither step
is in the provisioning matrix, so neither takes a `_CHECK_DEPENDENCIES` or
`_CHECK_EVIDENCE` entry.

| Check | Result |
| --- | --- |
| AC-0039 `tools/lint-ci-parity.py --root .` | exit 0 — 107 steps dispositioned, 121 roster keys |
| AC-0038 YAML parse of `gate-main` step indices | 46 and 47, both below the bulk step at 48 |

Placement was verified by index rather than by the parity lint, which cannot see
order: the bulk `pytest tests/ -q` step already collects both modules, so
placement buys failure attribution rather than reach.

## T10 — guides and the release surface

### Guides

One depth-selection how-to per journey — `guides/frontend-engineering/how-to/`
and `guides/experience-design/how-to/choose-the-depth.md` — each with its index
row. Neither carries `order:` frontmatter, so neither is a guidebook *step* and
neither owes the seventeen step-contract obligations; both trees already carry
non-step how-tos, so this follows the existing shape rather than inventing one.
`lint-guidebook-steps.py` exits 0 on both books, and `check-guide-index.py`
reports all 21 active packs present.

### Evals

One case per contract-carrying pack, placed in the skill that reads the contract
copy: `frontend-engineering`, `design-review`, `frame-intent`, and
`synthesize-stakeholder-research`. All four diffs are append-only — after a repair. The first write used
`ensure_ascii=False`, which rewrote case `id: 1` in two of the four files,
turning their `\u2014`, `\u2013`, `\u00d7` and `\u2194` escapes into literal
characters. Round 1 of review caught the ledger claiming append-only while two
files removed three pre-existing lines each. Both were re-dumped under the
convention their own bytes already used, and all four now show `removed=0`
against `origin/main`. The
obligation is per pack for any non-cosmetic update, and bumping all four is this
delivery's own declaration that all four are non-cosmetic.

### Release surface

| Pack | `pack.toml` and `plugin.json` |
| --- | --- |
| `product-strategy` | 0.2.6 → 0.2.7 |
| `product-engineering` | 0.13.16 → 0.13.17 |
| `experience-design` | 2.0.8 → 2.0.9 |
| `frontend-engineering` | 0.3.1 → 0.3.2 |

Four changelog entries, one per pack, each with a `### Highlights` subsection
carrying bullets rather than a recorded `none`: four packs gaining a shared
state-coverage map and a selectable depth ladder changes what a pack consumer
can do. `core`'s newest entry stays adjacent to `[Unreleased]` and the four
follow it contiguously.

`make build-self` was run **unforced, on a clean tree, after committing** —
never with `FORCE=1`. `packs/AGENTS.local.md` § Marketplace and release pipeline
step 2 says to pass it; the root overlay and the owner say not to, and the root
overlay governs.

The regeneration's only delta was the four bumped versions in
`marketplace.json`. No `.claude/` or `.agents/` projection moved, which is the
third falsified claim confirmed once more at the point it would have mattered.

| Check | Result |
| --- | --- |
| AC-0042 version bump, `pack.toml` ↔ `plugin.json` | exit 0 for all four |
| AC-0045 topmost heading names the new version | all four, and all four changed |
| AC-0046 heading order against `origin/main` | exit 0 |
| AC-0048 `### Highlights` bullet on each topmost entry | exit 0 |
| AC-0041 fresh unforced `build-self`, then diff | byte-identical |
| AC-0043 `catalogue verify` | exit 0 |
| `catalogue self-host --check` | exit 0 |
| `catalogue lint --deep` | `ok: 71` — unchanged from the base |

### A placeholder in the sweep that could never pass

`redcheck.py` carried `"0041": "false"` with the comment *marketplace
regenerates only after the bumps*. A command that is unconditionally red proves
nothing while the work is pending and reports a regression once it lands — which
is what it did.

AC-0041 now runs `catalogue self-host --check`, the non-writing form of the
unforced `build-self` the criterion names. Proven to discriminate: reverting one
version inside `marketplace.json` gives exit 1 naming the drift, and the
restored tree gives exit 0.

Its first reading was taken through `| tail -3`, which reported `tail`'s exit
status rather than the command's and so read a `FAIL` line as exit 0. The exit
codes above were re-taken unfiltered.

## Post-gates review, round 1

One `adversarial-reviewer` pass over `git diff origin/main...HEAD`, adjudicated
by `finding-adjudicator`. Raw report and adjudication are under
`.context/reviews/ce7b491a-3116-4656-8bc7-18b99b2c4477/`.

**Ten findings raised: 7 sustained, 3 refuted.** Recorded as a findings round —
`review_round_count` 1, seven fingerprints.

### The adjudication needed a second pass

The first adjudication returned `ADJUDICATION-INDETERMINATE` on two findings,
both for want of a revision-graph fact its envelope cannot read: whether commit
`150e3656b` is an ancestor of `origin/main`, and whether the eval diffs removed
pre-existing lines. Both are machine-checkable, so the guarded evidence retry
applied: the facts were measured, and one complete replacement adjudication ran
over the unchanged source findings and returned no indeterminates. The
superseded verdict is retained beside the replacement.

Both facts resolved against the delivery: `150e3656b` is this branch's own
commit, and two eval files did rewrite case `id: 1`.

### What was refuted, and why it matters that it was

- **Spec still `Implementing`, criteria unticked, workspace entry active.**
  Refuted on authority: that is the finish checklist, which runs after review is
  clean. Outstanding-by-schedule, not a defect.
- **The changelog block breaks AC-0046 after merge.** Refuted on the criterion's
  reach — AC-0046 is measured against this change's own tree with an
  `origin/main` baseline, which the branch satisfied. The *merge-ordering fact*
  was true, and the rebase below acted on it under the freshness gate and owner
  direction rather than as a finding repair.
- **Add a blank line after the frozen plan's new `Status` line.** Refuted, and
  the remedy is forbidden: AC-0005 pins that the diff adds *exactly one* line.
  A reviewer preference that would have broken a criterion.

### Blocker — AC-0026 had no deciding artifact for two of four allowances

`ALLOWANCES` matched whole-file, case-folded substrings. Two cue sets were
already satisfied by prose predating this change: the journey's mode summary
says "a proportional contract", and stage 2 says a retrofit "narrows or expands
the contract". So `("proportional", "contract")` and `("retrofit", "narrow")`
were green with T4's allowance sentences deleted — the third can't-fail control
found in this delivery.

Repaired two ways at once: each cue set now names the phrase its allowance turns
on, and all of a set's cues must land on **one line**. Per-allowance mutation
proof, each allowance's own prose deleted alone:

| Allowance | Deleted alone | Present on `origin/main` |
| --- | --- | --- |
| a contract proportional to risk | red | absent |
| omitting inapplicable states | red | absent |
| a narrowed retrofit state matrix | red | absent |
| the optional token gate | red | absent |

Baseline green. The right-hand column is the half the old check lacked: every
cue set is now absent from the pre-change journey, so the assertion measures
T4's work rather than the file's background vocabulary.

### The other sustained findings

| Finding | Repair |
| --- | --- |
| Eval cases asserted contract-reading two skills never instruct | Reworded both cases. **This repair did not land** — round 2 showed the reworded assertions still rested on the contract reference, which neither skill body names. Superseded by the round-2 repair below |
| Illustrative-state assertions pinned two literal files while AC-0024/AC-0025 quantify over the tree | The file set is now derived from `packs/experience-design/`. Proven: a probe file added under that tree with `default · loading · offline` turns both assertions red, and was silent under the pinned pair |
| Two how-to tables restated state counts, and "the four data-shape states" mislabelled `first-run` and `blocked` | Both tables now express state obligations by reference to the map, as they already did for fields. No state count remains in either file |
| Ledger claimed all four eval diffs append-only | Made true rather than annotated: both files re-dumped under their own escaping convention, all four now `removed=0` |
| Unused `contract` fixture on the ladder assertion | The expected tier set is now derived from the contract's `Required:` annotations, so the fixture is load-bearing |

### Finding 8 — three files outside every task's `Touches:`

Sustained on measured fact: `git merge-base --is-ancestor 150e3656b origin/main`
exits non-zero, so that commit is this branch's own and its three files are
inside the review target. No task's `Touches:` names `docs/product/briefs/` or
`docs/product/intents/`.

The files are `docs/product/briefs/digital-experience-doctrine-completion.md`,
`docs/product/intents/digital-experience-doctrine.md`, and
`docs/product/intents/growth-strategy-pack-charter.md`. The last carries a
separate product decision about measurement operations, pricing doctrine,
conversion experimentation and SEO that this spec does not reach. The fix is an
accounting, not an edit: the PR's *what did you not change that you considered*
answer must name all three, and the growth-charter paragraph is a bundled item
distinct from this spec rather than part of it. Recorded here so the accounting
exists whether or not a PR is opened from this session.

## The rebase onto current `origin/main`

`check-base-freshness.py` returned `surface`: 19 commits behind. Owner directed
the rebase. Run with `rerere.enabled=false`, because rerere replays a
resolution recorded in another worktree and these conflicts are not that.

Two conflicts, both in files where upstream and this branch added independent
things at one anchor:

- `web/src/content/journeys/frontend-engineering.md` — a generated file.
  Resolved by regenerating from the merged source rather than hand-merging
  generated bytes.
- `.github/workflows/build-check.yml` — upstream added a
  backward-traceability roster step at the same anchor as this branch's two.
  Both kept; a YAML parse confirms this branch's steps sit at indices 47 and 48,
  below the bulk `pytest tests/ -q` step at 49.

`tools/lint-ci-parity.py` auto-merged; `workspace.toml` and the changelog did
not conflict. The changelog then needed a move rather than a merge: upstream's
`## [core][2.26.37]` landed above `2.26.36`, leaving the four pack entries
following the second-newest core entry. They were moved to follow the newest.

Base-sensitive readings re-taken on the rebased tree — AC-0046, AC-0048,
AC-0042, AC-0039 and AC-0001 all exit 0. A recovery branch
`recovery/pre-rebase-fec` marks the pre-rebase head.

## Post-gates review, round 2

A second `adversarial-reviewer` pass over the rebased diff, adjudicated
independently. **Eleven findings raised: 8 sustained, 3 refuted.** Recorded as
a findings round — `review_round_count` 2, eight fingerprints.

### The round-1 eval repair did not land

Round 1 sustained that the `frame-intent` and `synthesize-stakeholder-research`
eval cases asserted contract-reading behaviour neither skill instructs. The
repair reworded both cases and the ledger recorded them as "narrowed to what
each skill's body does instruct". Round 2 measured that claim and it was false:

```
grep -rln "digital-experience-contract" packs/*/.apm/skills/*/SKILL.md
  packs/experience-design/.apm/skills/design-review/SKILL.md
  packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md
```

Two files, both edited by T6. In the other two packs the contract reference
ships **unloaded**, so no case about the contract is reachable there, however it
is worded. Rewording could never have fixed it.

**Why the obvious repair was refused.** Adding the contract to those two
`SKILL.md` bodies would have made the cases apt — and was adjudicated *not
permitted*: no task's `Touches:` names `frame-intent/SKILL.md` or
`synthesize-stakeholder-research/SKILL.md`, `Touches` is pinned contract, and it
would create skill-load obligations beyond AC-0006 and AC-0007. It needs a
controlled plan amendment, which this delivery did not open.

Both cases were therefore rewritten to behaviour each skill's own procedure
directs — intent altitude and Scale resolution for `frame-intent`, theme
organisation and coverage gaps for `synthesize-stakeholder-research`. What the
change actually gives those two packs is recorded rather than asserted: **an
updated contract copy carrying the shared state-coverage map and the owner
label, and a refreshed eval case — not a reading capability.** Their skills do
not read the contract and this delivery does not make them.

### The changelog promised the capability the packs did not get

The `product-engineering` and `product-strategy` Highlights said the contract
"its skills read" and that "strategy work can see what the cheap tier owes".
Highlights project to the public `/now/` page, so that would have shipped an
adopter-visible promise these versions do not deliver. Both now state what
shipped — the contract copy and the eval case — and say plainly that the packs'
skills are unchanged and still do not read the contract.

### The derivation repaired in round 1 was still inert

Round 1 made the ladder test's `contract` fixture load-bearing by deriving the
expected tier set from `cumulative_obligations`. Round 2 showed the arithmetic
cannot carry the claim: cumulative sums are running, so once `explore` has one
annotation `pilot` and `production` are non-zero by construction and no tier can
ever drop out. Measured: cumulative 10 / 25 / 32, per-tier 10 / 15 / 7. The
derivation now reads per-tier annotations, where a tier the contract stops
annotating genuinely disappears. The count assertion keeps its cumulative sums,
which is what the plan's Constraints pin.

### The rest

| Finding | Repair |
| --- | --- |
| Three accessibility assertions could go vacuous together on an all-`no` WCAG column | A non-emptiness guard now lives in the module that owns the property. The sibling journey module already had one, so the regression was detectable — but a guard the next reader of this file will not find is a guard in the wrong place |
| The derived illustrative-file scan is case-sensitive and assumed a colon | The docstring now states the shape it actually enforces — capitalised `States` plus a middle dot — rather than claiming every list under the tree. A matching line with no separator now fails naming its file and line instead of raising `IndexError` |
| The say-this table marks `content-design` and `creative-direction` `Required` while the four-step thread omits both | `content-design` is pinned to `Required` by AC-0021 and T5's `Tests:`, so the reconciliation is on the thread side: the journey now says what `Required` means relative to the shorter thread — required for a complete thread, versus an input nothing downstream can reconstruct |
| A draft-time note about a concurrent session shipped in the doctrine brief | Replaced with the standing relationship. `docs/product/AGENTS.md` § *Status has one home* is why it went stale unnoticed: a restated status is never re-checked |

### What was refuted, and what that protected

- **"The journey states 12 and 32 fields for the same contract."** Refuted on
  observation: each count is attributed in its own sentence — the depth
  sub-stage names "the shared experience contract", the allowance names "the
  page/screen contract", matching the skill's own 12-field template.
- **"The frontend tutorial's four-state teaching contradicts the explore
  promise."** Refuted on authority. The promise's subject is tier-band
  membership; the tutorial names the critical states of one worked
  notification-card example and claims nothing about a band. AC-0024 and
  AC-0025 quantify over `packs/experience-design/` by their own text, so
  reaching into `guides/frontend-engineering/` would widen the criterion rather
  than apply it — and the journey's own allowances expressly cover omitting
  inapplicable states for a minor component variant.
- **"A stale six-state count in `core-pack.md` now reads as a contradiction."**
  True as a fact, refuted as an obligation: no criterion reaches it, and the
  root `AGENTS.md` says to keep unrelated discoveries out of the current change.

### The pattern across both rounds

Every sustained finding in round 2 that was not new was a **round-1 repair that
did not do what its ledger row claimed** — the eval rewording, and the fixture
derivation. Both were recorded as done before being measured. The rule this
delivery keeps relearning: write the claim from the result, and measure the
result before writing the claim.

### An instrument that mutates the tree it measures

The round-2 repairs were committed with a stale generated file, and the cause is
worth naming because nothing reported it.

`redcheck.py`'s AC-0037 probe is:

```
python3 tools/build-site.py --journeys-only && git diff --quiet web/src/content/journeys/
rc=$?; git checkout -- web/; exit $rc
```

The `git checkout -- web/` restores the tree so the probe leaves no residue.
Run on a **clean** tree that is what it does. Run while a regenerated web copy
is uncommitted, it **discards that regeneration**. The sequence that bit: edit
`JOURNEY.md`, regenerate, run the instruments, commit — and the commit captures
the pre-regeneration copy, because the instrument reverted it in between.

The probe then reported `AC-0037 REGRESSED`, which was true of the tree and
true because the probe had made it so. Repaired by regenerating and committing;
a fresh regeneration against the committed copy is now an empty diff.

The general rule, and the reason this sits in the ledger rather than in a
commit message: **a standing instrument that writes must only be run on a clean
tree.** Running one over uncommitted work can destroy that work, and the
failure it then reports names the symptom rather than itself.

## Post-gates review, round 3

**Zero blockers.** Four findings: 2 sustained, 2 refuted. The reviewer
independently verified all eight round-2 repairs hold and killed 23 of 24
mutations against the two new roster modules — the survivor is the finding
below. Recorded as a findings round: `review_round_count` 3, review retry 3 of 5.

### The fifth control that could not fail

`test_the_say_this_optionality_agrees_with_the_how_to_guides` opened with
`if skill not in guides: continue`. AC-0021 quantifies over `design-system` and
`content-design` **by name** and requires the journey's mark to *equal* the
guide's — and equality presupposes a guide mark exists. A skip means the
criterion passes on absence.

The path is reachable from the guide side alone: `_guide_optionality()` drops
any row whose last cell stops being one of the three verdicts or whose column
count falls below four, so an ordinary how-to table edit would retire AC-0021's
entire verification with the gate reporting pass.

Reproduced before repairing: removing both named skills from the guide map left
the test green. The two names are now held in `GUIDE_OWNED_SKILLS` and their
absence fails before any comparison. All three variants now die — dropping
both, dropping `design-system`, dropping `content-design` — and the baseline is
green.

That is the fifth can't-fail control in this delivery, after the substring path
check, the `false` placeholder, the allowance cue sets, and the inert cumulative
derivation. Every one passed its own suite while deciding nothing.

### What was refuted, and what it protected

- **"The contract restates its map's counts in prose with no pin."** True on
  fact — the five numbers are correct today and nothing reads them — and
  refuted on authority. AC-0031 assigns the journey paragraph to Review-only by
  owner decision, which a mechanical pin would contradict rather than enforce;
  AC-0016's negated grep is path-scoped to the core guide page, and the plan's
  "number with two homes" Constraint is scoped to the frontend journey's
  assertion count. The proposed pin also ignores that the sentence has four
  byte-identical homes held together by `check-contract-drift`. Refuted on
  authority is not refuted on fact: the staleness risk is real and unpinned.
- **"The minimal viable thread has three homes."** Refuted, and its remedy
  would have broken the spec: AC-0022 requires the journey to state the thread,
  and AC-0023 is written about `DESIGN.md`'s claim and "the minimal viable
  thread it introduces" — so both pack copies are the *specified* state, and
  moving either would fail a criterion. The suggested equality assertion would
  also fail today, because the journey deliberately carries the `Required`-sense
  disambiguation that `DESIGN.md` does not.

That is the second round running in which a reviewer's proposed remedy would
have broken an acceptance criterion had it been applied on sight — the first
being round 1's blank line, which AC-0005 forbids. Adjudication is what caught
both.

### The advisory

The brief's Ready-gaps bullet still said "Wait for the other session's edits to
settle" — the sibling of the note round 2 replaced, and the same defect: an
instruction about the drafting episode rather than a standing condition. It now
states what must hold, which is that the `Brief:` field and the Spec map move
together or not at all.
