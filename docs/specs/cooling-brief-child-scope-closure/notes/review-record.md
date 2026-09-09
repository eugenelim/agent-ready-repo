# Pre-EXECUTE review record, and one recorded deviation

Every reviewer report is persisted under
`.context/reviews/af7591a2-c3ac-4217-ab31-f3eae06a7d02/` (git-ignored). Every report was adjudicated by `finding-adjudicator` and every paired artifact
validated. Round 3's adjudication ran retrospectively; the deviation that made
that necessary is recorded below.

| Round | Reviewer | Raw findings | Sustained | Refuted | Adjudicated |
| --- | --- | --- | --- | --- | --- |
| 1 | security-reviewer | 8 | 7 | 1 | yes |
| 1 | adversarial-reviewer | 20 | 18 | 2 | yes |
| 2 | security-reviewer | 6 | 6 | 0 | yes |
| 2 | adversarial-reviewer | 16 | 16 | 0 | yes |
| 3 | adversarial-reviewer | 12 | 12 | 0 | yes, retrospectively |
| 4 | adversarial-reviewer | 16 | 11 | 5 | yes |
| 5 | adversarial-reviewer | 15 | 14 | 1 | yes |
| R1 | adversarial-reviewer (rubric) | 9 | 9 | 0 | dispositioned inline |
| R2 | adversarial-reviewer (rubric) | 12 | 12 | 0 | dispositioned inline |
| R3 | adversarial-reviewer (rubric) | 10 | 10 | 0 | dispositioned inline |

## The deviation, and how it was closed

`work-loop` routes every `findings`-classified report through
`finding-adjudicator` and directs that only sustained findings reach a repair.
Round 3's report was persisted and classified (`findings`, count 12) but **not
adjudicated before revision 4 was authored from its raw prose**.

That was a protocol error, not a licensed shortcut. The owner had authorized
ending the review loop, and I read that as covering adjudication too. It does
not: adjudication protects against acting on a finding that would not survive
scrutiny, which is a different risk from running one more review round. The
owner corrected this on 2026-09-04 and directed convergence.

**Closed by running the adjudication retrospectively**, with a second question
added — for each finding, whether the repair already applied was correct,
insufficient, unnecessary, or harmful. All twelve sustained, none refuted, so no
change was made for a reason that would not have survived. Two repairs came back
**insufficient** and are being carried into the next revision:

- **F8** — AC22 cites an owner-decision record in `notes/ask-first-review.md`
  that does not exist there. The decision is real; the citation dangles.
- **F9** — `plan.md:5` was corrected and `plan.md:132` was not, so the plan
  contradicts itself about which fixture helpers need extending.

The retrospective run is why both are known. Had the loop simply stopped, they
would have shipped.

## What was done instead, for the two findings that mattered

Round 3's two load-bearing findings were measured claims about engine behaviour,
so both were verified by construction before being acted on, rather than accepted
from prose:

- **AC9's dispatch-equality clause was vacuous.** All four arms of its fixture
  return an empty `canonical.ready`, so `identical to` was `set() == set()`. The
  clause was deleted. Recorded as probe 13.
- **AC10's control was false.** With the child body at `Shipped` or
  `Implementing`, removing the `Cooling` record yields zero
  `impossible_transition`, not one, because `execution_evidence` accepts either
  token. Only `Approved` produces the asserted control. AC10 now pins the status.
  Recorded as probe 13.

The remaining ten were documentary or mechanical: a two-valued `path` rule
deleted rather than reconciled across four documents, an inverted rationale, a
stale count, three citation repairs, and two wording repairs.

## `reviewers-clean` was fired without a clean reviewer result

The `SPEC-PLAN-REVIEW` exit at seq 8 was taken on the owner's authorization, not
on an adjudicated Clean. No reviewer returned clean at that point, and this note
exists so the transition is not later read as evidence one did.

That approval was subsequently withdrawn in favour of converging, so the seal
recorded at seq 9-11 does not represent a converged contract either. The route
back from `CODE-IMPLEMENTATION` is the `contract-amendment` edge in
`work-loop`'s delivery-contract-lifecycle reference, which clears the approval
and schedule baseline and returns to `SPEC-PLAN-DRAFTING`.

## The three rubric rounds

Rounds 1-5 above ran the repository's default adversarial checklist. Rounds R1-R3
ran a supplied spec-mode rubric whose ordering rule is that a wrong owner
outranks criterion craft, and whose fix shapes prefer removing a defect class
over removing its instances.

| | R1 | R2 | R3 |
| --- | --- | --- | --- |
| findings | 9 | 12 | 10 |
| blockers | 4 | 2 | 1 |
| plan-owned findings in a spec review | 1 | 1 | 1 |
| introduced by the previous round's repairs | 2 | ~8 | ~7 |

Two structural changes came out of them and account for most of the drop in
recurring findings.

**Criteria are transcribed from a reproducible matrix, not written from intent.**
Rounds 3, 4 and 5 each found a criterion whose stated inputs did not determine
its asserted output, on a different axis each time — the child's body status, the
brief's, then the dependant's provenance. `notes/probes.md` probe 14 pins all
seven axes at once and records its own construction, and the criteria state its
literals.

**Cross-references name criteria by title, not by number.** Renumbering broke
references five times. Converting the plan exposed eight references that had
been silently wrong as numbers: `AC17` where `AC18` was meant reads fine, while
the same error written as a title reads as nonsense. The defect was never
carelessness; a number carries no meaning to proofread against.

## Round 4 — spec, rubric mode (2026-09-08)

0 blockers, 4 concerns, 3 nits. All seven premises verified by construction
before adoption; all seven held. The load-bearing finding was AC25: a criterion
asserting what the shipped command emits, with a hand-written note as its only
witness, in a spec whose own *Never do* rail forbids exactly that. Concerns 2
and 3 shared one premise — fixtures reached through sibling ordinals — and one
fix closed both.

## Round 5 — plan, default checklist (2026-09-08)

3 blockers, 11 concerns, 2 nits. First dedicated round on `plan.md`; every prior
spec round had returned exactly one plan-owned finding that a spec reviewer was
the wrong reader for. Blockers: a citation to a home that does not exist (third
instance of that shape here), a task gate unsatisfiable until a later task, and
a `[work]` registration that never named its collection against a fail-closed
`impossible_transition`. Also missing: the `Engine-Change-RFC` trailer step, the
`Highlights` disposition, any invocation that collects the roster suites, and
the PLAN-time stub validation `tdd-stubs.md` requires.

**One repair instantiated its own root cause.** Fixing the unsatisfiable gate, I
wrote `pytest … -k finding_next_actions` as T1's oracle. Measured: that selector
collects nothing — `no tests collected (25 deselected)` — and **exits 0**. The
shipped documentation assertion turned out to be welded inside a single 312-line
node that also asserts the projections and the release version, so no narrower
node exists and T1 asserts documentation coverage in its own suite instead.

## Round 6 — both artifacts, confirming (2026-09-08)

4 blockers, 9 concerns, 2 nits. All 15 verified by construction, all 15 held,
all 15 applied. The blockers split by cause, which is the useful part:

- **Base decay, not authoring error (2).** The pinned bump and the named eval id
  were both correct when written and both false by the time they were read —
  `origin/main` moved 15 commits mid-round. Fixed structurally: the plan now
  names no version and no id, only the derivations. The core version moved
  2.25.2, 2.25.3, 2.25.4, 2.25.6 across this delivery's review.
- **Self-inflicted by the previous repair (1).** Replacing line literals with
  symbols, this delivery invented `_brief_status_satisfied`, which exists
  nowhere. The owning symbol is `_brief_child_scope_is_valid`. A symbol citation
  decays less than a line number but is not self-verifying, so a programmatic
  sweep of every backticked identifier against the engine and the roster now runs
  before each seal; it reports clean at base `6996a9840`.
- **Pre-existing misattribution (1).** *A cooled brief is satisfied ahead of the
  refusal* was attributed to the metadata-safety precedence, which returns
  `False`; only `if cooled_dependency: return True, None` can satisfy a criterion
  asserting the dependant is present in `canonical.ready`.

Probe 16 was added to ground *The shipped command emits the finding*, which
round 4's repair had left resting on no probe: the shipped script exits 0 both
with and without a finding present, so the exit-code half survives once the
finding exists. A reviewer independently confirmed the same from `return 0` in
`workspace_status.py`.

## Rounds 7-9 — implementation review, three reviewers in parallel (2026-09-08)

Run after all three CI workflows were green on the final commit. 24 findings:
security 5, adversarial 9, quality 10. Adjudicated in one pass: **17 sustained,
7 refuted, 0 indeterminate.** Blockers: 5.

**All three reviewers found the same line wrong, in three different
directions.** `brief_membership_paths` keyed on the collection name:

- too wide — no `kind` filter, so a mis-collected `kind = "spec"` entry in a
  brief queue resolved a declared value and released the fail-closed floor;
- too narrow — `[backlog].open` admits `kind = "brief"`, so a brief registered
  there was invisible and a correctly declared child was refused with no repair
  available;
- too narrow again — a legacy bare-string brief entry never enters
  `local_memberships`, with the same consequence.

One kind-based, collection-agnostic predicate over canonical and legacy
memberships closes all three. M6 and M7 pin it.

**Adjudication stopped three fixes that would have made things worse.** The
adversarial fix as written would have admitted `backlog.open` without a kind
filter, making the fail-open reachable in *valid* workspace state. The security
fix as written would have entrenched the too-narrow half. And one finding was
refuted outright: `parent = ""` normalises to empty, so dispatching is the
contract's required outcome, and its proposed fix would have broken three
criteria. This delivery had already reproduced that behaviour and accepted the
reviewer's framing of it as a defect; the adjudicator caught that the behaviour
was correct and the reading was wrong.

**Five refutations rested on authority, not fact.** The `sys.path` line, the
duplicated row parser, and the isolated-seam request are all directed by the
accepted contract or the frozen plan. A reviewer reading only the diff cannot
see that, which is what adjudication against the governing artifacts is for.

**A fix of mine broke a criterion, and the repair caught it immediately.**
Binding AC24's assertion to its named row failed on the first run — because the
markup fix applied alongside it had inserted backticks inside the contiguous
literal the criterion requires. The adjudicator had assumed the literal survives
either way. Resolved as prose with the literal intact.

**Two criteria had shipped with no test anywhere.** AC9 and AC10 were named in
the Testing Strategy with this suite as their evidence home, and nothing built
their fixtures. They exist now, and M8 and M9 kill the suppression mutations
that were undetectable without them.

**Four claims this delivery made about itself were false.** The `/now/`
rendering claim, the mutation record's suite size, the "citation count is zero"
claim, and the fixture writer's equivalence claim. Each is corrected in place
with what was measured. The citation count is the instructive one: it was
truthfully counted against a pattern that matched `AC<n>` and `RFC-<n>` and
missed five wave-vocabulary and spec-slug citations. A count is only as good as
its denominator, so the denominator now travels with the number.

## Round 10 — confirming review of the repairs (2026-09-08)

Scoped to the repair commit and the rebase resolutions. 6 concerns, 1 nit, no
blockers. Six applied; one is an owner decision and is open.

**Three findings were this delivery asserting numbers or mechanisms it had not
constructed — inside the corrections for that exact failure mode.**

- The ADR clause added while correcting probe 6 claimed the Spec map and the
  workspace entries "disagree on 2 of 15 briefs today". Measured: the corpus is
  16 non-template briefs and the two sides disagree on **zero**. The number was
  invented by conflating probe 6's *format* measurement with a *disagreement*
  measurement that had never been run.
- The probe correction carried "2 of 15" and "the 13 that do" forward as the
  surviving facts. Both were stale: 16 briefs, 14 with a `## Spec map`, 5 with
  parseable rows.
- The new AC9/AC10 fixture docstring said a brief in `brief_queue.executing` is
  "out of lifecycle vocabulary for its own status". It is not — that collection
  expects exactly `Executing`. Measured, the `impossible_transition` both cases
  depend on carries detail `brief child scope` and comes from the child-scope
  arm.

The re-measurement validated its own parser before trusting the zero, because a
parser returning empty sets would have produced the same number for the wrong
reason. It extracts real slugs from the 5 briefs that carry them.

**The rejection of the Spec-map alternative survives on a stronger basis than
the one recorded.** Parsing that section would find nothing to attribute for 11
of 16 briefs. Where both sides carry entries they agree, so the objection is
coverage, not conflict — which is what the ADR now says.

**One justification was overclaimed.** The ADR said the too-narrow predicate left
"no repair available" for both the `[backlog].open` and the legacy branch. True
of the first; the legacy branch already emits `legacy_entry`, whose next action
is to register a canonical entry, which resolves the declaration as a side
effect. The legacy inclusion now stands on its own narrower ground: reporting a
correct declaration as unestablished is a misdiagnosis regardless.

**The eval had been left on the pre-repair wording.** Both published cells moved
from "registered membership" to "registered brief entry" precisely because the
old phrasing admitted a non-brief membership, and the eval that grades an agent
reporting that action still quoted the old text. `packs/AGENTS.md` requires a
non-cosmetic pack change to update its eval harness; it now agrees, with an
assertion covering the misattribution caveat.

**The three membership arms are now three cases.** They had been one function
with three sequential arms, so a failure in the first hid the other two — and
those arms are the too-wide and too-narrow directions the whole repair turns on.
Split, each kills its own mutation alone: dropping the legacy half kills only the
legacy case, dropping the kind filter kills only the decoy case.

**Open, and an owner decision.** The repaired predicate is pinned by tests but
by no acceptance criterion: no AC covers which memberships resolve a declared
parent, so the durable contract still permits the collection-keyed defect. Adding
one to a pinned `Implementing` spec needs the `contract-amendment` route.
