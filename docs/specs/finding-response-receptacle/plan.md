# Plan: Finding-response receptacle

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/tests/skills/work-loop/test_non_gating_nits.py`
  for how this pack pins record semantics through content assertions rather than a
  validator; `packs/core/.apm/skills/work-loop/references/review-verdict-record.md`
  for the schema and its authoritative disposition table; `packs/AGENTS.md` for the
  version-bump and eval-harness rules.

## Approach

The whole change is prose plus the tests that pin it. There is no verdict
validator in this repository — the record is a schema an agent reads and a table
it applies — so nothing here computes a state, and no task should invent
something that does.

That shapes the guardrail work. The spec's promise is that the two new fields can
never gate, and the only mechanical form that promise can take is structural: the
sections that decide state must not name them. A test that reads those sections
and asserts their absence reds on the exact way this could go wrong later, which
is someone adding a rule that consults a response.

## Constraints

The spec's `## Boundaries` owns the dependency, gating and version-bump limits;
this plan cites them rather than restating them. One consequence the spec does not
state: because the answers cannot be cited from an internal record, the pack
carries the only copy, and the test that pins them is therefore also the only
guard against the set drifting.

## Construction tests

`packs/core/tests/skills/work-loop/test_finding_response_fields.py`, a new sibling
of `test_non_gating_nits.py`, which it follows in shape. Content assertions over
the reference document and the skill, not behavioural tests, because there is no
behaviour to drive.

## Durable-output map

| Durable output | Task | Evidence |
| --- | --- | --- |
| Interface compatibility (the record schema) | T1 | The two fields in `findings[]`, marked optional |
| Maintainer procedure (DECIDE) | T2, superseded by T4 | The answer ladder at the point of decision |
| Release history (changelog) | T3 | A `core` entry naming the added fields |

## Design (LLD)

### Design decisions

The answers are stated once, in the DECIDE step, and the schema's
`response` field points at that statement rather than repeating the list. A
second copy would be a second thing to drift, and this pack already carries a
rule that a fact belongs in one place.

The two fields are recorded as a pair in both directions. A `reason` with no
`response` records a ground for a decision nobody named; a `response` with no
non-empty `reason` names an answer with nothing behind it. Either is incomplete,
and an incomplete pair is ignored with a note rather than rejected — the record
stays valid, because nothing about this metadata may block a review.

Neither field appears in the disposition table, state precedence, or residual
eligibility. That absence is the guardrail, and AC-0003 makes it a checked
property rather than an intention.

### Failure, edge cases & resilience

An unrecognised or incomplete `response` is ignored with a note, never rejected
and never a gate. Rejecting the record would make advisory metadata blocking by
the back door, which is exactly what the spec's Boundaries forbid: a review that
cannot complete because a note is malformed is a review the note gated.

## Tasks

### T1: Schema fields

- **Implements:** AC-0001, AC-0002, AC-0004
- **Depends on:** none
- **Mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-loop/references/review-verdict-record.md`,
  `packs/core/tests/skills/work-loop/test_finding_response_fields.py`
- **Tests:** AC-0001, AC-0002 and AC-0004. Assertions that the `findings[]` schema
  names both fields and marks them optional; that it names the eight answers as
  `response`'s admitted values by pointing at their single statement; that it
  states BOTH incomplete directions — a `reason` without a `response`, and a
  `response` without a non-empty `reason` — and that each is ignored with a note
  rather than rejected; and that an unrecognised `response` value is likewise
  ignored with a note. Plus a pin on the disposition
  table's rows, which reds if this change alters them — the table is what the
  guardrail protects and it is not supposed to move.
- **Approach:** Extend the `findings[]` bullet and add a short subsection
  describing the two fields and their non-gating status.
- **Done when:** every test this task's `Tests` names passes.

### T2: Non-gating guardrail, and the eight answers as guidance

- **Implements:** AC-0003
- **Depends on:** T1
- **Mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`,
  `packs/core/tests/skills/work-loop/test_finding_response_fields.py`
- **Tests:** AC-0003. Parse the reference document's finding-disposition,
  state-precedence and residual-eligibility sections and assert neither field name
  occurs in any of them, and assert the fields' own description mentions neither
  `status` nor `effective_severity`. Separately, and carrying no criterion, pin
  that the DECIDE step names all eight answers and states that a sustained finding
  does not by itself require an edit — a content pin of the kind this pack uses to
  hold shipped prose whose obligation is deferred elsewhere. The docstring records
  what the absence assertion does not reach.
- **Approach:** Add the eight answers to DECIDE beside the existing severity
  routing, without disturbing it.
- **Done when:** every test this task's `Tests` names passes.

### T3: Release surface

- **Implements:** none directly; carries the spec's release-history output
- **Depends on:** T2
- **Mode:** Goal-based check plus one manual read
- **Touches:** `packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`,
  `packs/core/.apm/skills/work-loop/evals/evals.json`
- **Tests:** `make build-check`'s catalogue legs, which prove version agreement
  across `pack.toml` and `.claude-plugin/plugin.json`. No test in this repository
  asserts that the topmost `core` changelog entry carries the bumped version or
  names the added fields, so that part is verified by reading the entry against
  the two manifests and recording what was read. Claiming a machine here would
  name an oracle that does not exist.
- **Approach:** Patch bump on both manifests — `packs/AGENTS.md` reserves minor
  for a new primitive, and this is changed content in an existing one; a `core`
  changelog entry naming the fields; an eval entry covering the non-gating
  answer, since the pack rule requires a non-cosmetic update to update its eval
  harness.
- **Done when:** the checks this task's `Tests` names pass, including the
  recorded read.

### T4: The answer ladder

- **Implements:** none directly; supersedes T2's guidance prose, which shipped
  under the earlier set and is contract only through its content pin
- **Depends on:** T2
- **Mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`,
  `packs/core/.apm/skills/work-loop/references/review-verdict-record.md`,
  `packs/core/tests/skills/work-loop/test_finding_response_fields.py`
- **Tests:** Replace T2's vocabulary pin with one covering the amended set and
  order recorded in [`notes/owner-decisions.md`](notes/owner-decisions.md): every
  answer present, each under its axis, axes in the order cut, route, fix, hold,
  and the stop instruction stated. Separate assertions per property, because a
  single pin over the whole block cannot show which part moved. Add one asserting
  `drop-the-claim` and `demote-the-claim` are distinguished by what survives —
  the first leaves nothing, the second relocates an obligation and names its pin —
  since a reader who conflates them has the set but not the distinction it was
  added for. Pin the demotion-versus-narrowing question — whether the obligation
  should still be one a completion gate reads — because that pair is the easiest
  to confuse and the ladder stops at the first match. Pin that demotion stays
  unresolved until an owner-authorized amendment lands, so an implementation
  cannot re-imply that removing a criterion is free. Pin the fix axis's
  surface-walk rule and its four orders, pin that EVERY axis walks and that the
  direction differs — cut backwards, route outwards then back, fix sideways, hold
  forwards — pin that it is a walk rather than a flat sweep — following relationships because a paraphrasing companion shares no
  string, and continuing until the frontier is empty because each repair opens its
  own — and pin that the walk feeds back into the choice of rung — those are the halves a later edit would
  separate, leaving a sweep nobody acts on. Assert every cut-axis answer carries its decision predicate as
  `notes/owner-decisions.md` states them, because four answers that all reduce
  something are unusable without the test that says which applies. Assert the
  verdict reference and its own pin name no count: T2 shipped "one of the eight
  answers" with a test pinning that exact phrase, so the count is currently
  contract and would ship false beside a longer set.
- **Approach:** Rewrite the DECIDE answers as the four-axis ladder with its stop
  rule, state the fix axis's surface-enumeration precondition beside the repair
  answers, and make the verdict reference and its pin count-neutral. T2's tests for
  the schema fields and the non-gating guardrail are untouched: none of them
  depends on how the answers are presented or how many there are.
- **Done when:** every test this task's `Tests` names passes.

## Rollout

- **Delivery:** big bang; additive optional fields and prose. Reversible by
  reverting the commit.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none.

## Risks

- **The guardrail test is an absence assertion**, and an absence is only as good
  as the set of places it searches. It names three sections; a future gating rule
  written somewhere else would not be caught. T2 states that limit in the test's
  own docstring so the next reader knows what it does not cover.
- **Demotion blocks, and should.** It removes an accepted obligation, so it needs
  owner authority through the amendment path and stays `unresolved` until that
  lands. No pending-relocation state is invented, because an unremoved criterion
  is honestly unresolved. A finding against material that was never contract is
  not a demotion at all — it is an ordinary in-place repair, which is why the
  earlier two-tier design was dropped.
- **The stop rule could route around an existing owner.** A duplicated obligation
  satisfies both demotion and `route-to-owner`, and demotion comes first. Closed
  by making demotion inapplicable when an adequate owner exists, rather than by
  reordering the axes — a second home for one rule is what the repository
  forbids, and the order carries the philosophy.
- **The surface walk is a discipline, not a control.** Nothing can verify that an
  author walked before repairing; the test pins that the instruction is stated,
  not that it was followed. Its real enforcement is the next review round finding
  what was left, which is the cost it exists to reduce rather than eliminate — and
  a companion that paraphrases with no structural edge stays reachable only by
  reading, so a later round finding one is not proof the walk was skipped.
- **The ladder's order is pinned by a test, and the reason for the order is not.**
  A later edit could preserve the sequence while removing the stop instruction
  that makes it a ladder rather than a list. T4 asserts the stop instruction
  separately for that reason.
- **The changelog entry has no mechanical oracle.** T3 records a read instead of
  claiming one. A wrong entry would survive the gates and be caught only by a
  reader, which is the honest state rather than a gap this change introduces.
- **The answers now have exactly one home in shipped content.** If that
  statement is edited the set changes silently, which is why T1's test pins the
  members rather than only their presence.

## Changelog

- 2026-09-13 — Amended under `contract-amendment` on recorded owner authority.
  The answer set gained `drop-the-claim` and `demote-the-claim`, filling an axis
  no prior response occupied: every existing answer edits the artifact, moves
  ownership, or holds, so a round could only add or hold and never let the
  contract shrink. The set is reordered cut-first and stated as a ladder with a
  stop rule. T4 carries it; T1 and T2 are untouched. AC-0001 stopped naming a
  count, which was a number standing beside the set it enumerates. T1's and T2's
  task sections still say "eight": the amendment contract forbids editing a
  completed task section, so they stand as a record of what those tasks shipped
  rather than as live claims. Everything a reader could act on is count-neutral.
  Review of the
  amendment found the same count shipped in the verdict reference under a test
  that pins it, so T4 carries that file too.
- 2026-09-13 — Spec review round 1: six findings, answered with three responses.
  The criterion naming the eight answers was CUT rather than repaired — it
  reinstated a deferred criterion its owning intent gates — and the prose now
  ships with a content pin and no criterion. Two claims were narrowed: invalid
  response metadata is ignored rather than rejected, and the absence oracle is
  stated as a proxy over named regions rather than as proof.
- 2026-09-13 — Drafted. AC-0003 and AC-0004 were re-cast before review: the first
  draft asserted a verdict state computed from a record, and no script in this
  repository computes one, so both were restated as structural properties that a
  content assertion can actually red on.
