# Plan: construction-time razor

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (pack export boundary, version-bump
  rule, no-internal-citation rule, eval-harness obligation);
  `packs/core/.apm/agents/implementer.md` and
  `packs/core/.apm/skills/work-loop/SKILL.md` as the two contracts under change;
  `packs/core/tests/skills/work-loop/test_sequential_implementer_dispatch.py`
  and `tests/roster/test_sequential_implementer_dispatch_contract.py` as their
  existing construction checks; `packs/core/tests/pack/test_razor_guidance.py`
  as the analogous pinned-prose suite. Named uncertainty: no gate executes
  either changed file's behaviour, so every gated behavioural criterion is
  scored at delivery rather than by a standing suite, and the demoted
  obligations are recorded rather than scored at all.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

## Approach

Three prose deltas land in two shipped files, then one task closes the release
surface. Each delta is placed to avoid an existing anchor: the implementer
bullet sits below the bundled-fixes comment because the envelope anchor test
slices only as far as the first `<!--`, and the declination delta sits at the
PLAN step, outside both sha256-pinned windows.

The riskiest part is not the prose — it is proving the prose moved behaviour
without over-firing. Each **gated** rule is therefore scored against fixtures
differing only in its trigger, and that control's outcome is its own acceptance
criterion rather than plan detail. The rung-recording rule is not gated: its
fixtures are run and recorded, and the content pins are its protection. One committed script materialises the whole
fixture set into a temporary directory so the evidence regenerates rather than
being hand-curated; the script enumerates the fixtures so no count is restated
here to decay. The fixtures are not loose repository files because
`tools/lint-ruff.py` checks the whole repository root and would lint them.

## Constraints

- RFC-0099 § 4 authorises a delta that references the canonical rule; the same
  RFC forbids a third copy of the ladder.
- `packs/AGENTS.md` requires a patch bump in both manifests, a self-host run, an
  eval-harness update, and no internal-governance citation in shipped content.
- `work-loop` is absent from `pack.toml` `[pack.evals].skills`, so cases added
  to its `evals.json` are a documented register and never detection.
- `work-loop/SKILL.md` has 115 body lines of headroom before the 1,000-line
  error and is already above the 500-line warning.

## Construction tests

No new standing repository suite is added. The behavioural properties are model
behaviour against a prose contract; no in-repository runner executes either
changed file, so a standing assertion could only re-read the contract's own
words, which the spec's Testing Strategy excludes as a criterion.

Two existing suites are the regression floor and must stay green because the
implementer delta lands inside a section one of them slices:
`packs/core/tests/skills/work-loop/test_sequential_implementer_dispatch.py` and
`tests/roster/test_sequential_implementer_dispatch_contract.py`.

The runner records the rung each report names but grades none of them. Which
rung applies to a fixture is not resolvable from the ladder by machine, so the
rung is recorded for the ledger and protected by a content pin rather than gated.
Four review rounds each produced a fresh defect in the gated form before that was
settled.

Functional success is read from each fixture's `Done when:` one-liner rather than
from the report's `ready` status, because a status is the run's own account of
itself. The runner records the one-liner's exit code and stdout for every
satisfiable fixture.

Protection, not criteria: T3 adds pack-local content pins covering the three
obligations the demotion left as working material, so the protection fails if any
one of them disappears rather than only if a heading does:

1. `implementer.md` requires the report to record the rung the implementation
   stopped at.
2. `work-loop/SKILL.md`'s declination rule requires each entry to name the rung
   that killed its temptation.
3. That same rule still admits a stated non-rung reason where no rung applies —
   the exception whose removal would turn the rule into a demand for a fabricated
   label.

A fourth pin asserts `implementer.md` names the ladder by its heading and states
no numbered rung of its own, which is what catches a future third copy. Pin 2 and
pin 3 together are the whole protection for T2, whose rule carries no criterion.

These pins are recorded here rather than in the spec because a check that a
sentence exists cannot decide whether the behaviour holds. Their job is to catch
silent deletion of an obligation and to catch a future third copy of the ladder,
not to prove the behaviour.

## Durable-output map

| Spec durable output | Task | Evidence the task produces |
| --- | --- | --- |
| Current product truth | T1 | Scored fixture-pair results in `notes/verification-ledger.md` |
| Current product truth | T2 | Recorded, unscored probe observations in `notes/verification-ledger.md`, plus the pins that protect the rule |
| Interface compatibility | T3 | Matching version in both manifests; `catalogue verify` clean |
| Release history | T3 | `[core]` entry directly under `[Unreleased]` |
| Behaviour register | T3 | Three labelled cases in `work-loop/evals/evals.json` |
| Reusable learning | DECIDE | Observation routed through the `project-knowledge` seam |

## Design (LLD)

### Design decisions

**The delta references and does not restate.** The ladder's rungs live in
`AGENTS.md`, which the implementer already loads as context step 1. The delta's
job is to convert an inherited rule into a triggered one, so it names the
ladder's heading and the specific rung behaviour required at construction time
without reproducing rung text. This is the disposition the governing intent
register already chose for guidance loading: keep the universal subset in
canonical agent guidance and put each workflow delta inside the owning
primitive.

**Why a bullet in the operating envelope rather than a new section.** The
envelope is the list of standing constraints the implementer applies to every
task, which is exactly the scope of the reuse obligation. A new section would
read as a phase and invite narration, which the intent register dispositions
against.

**Rung naming is a record, not narration.** The report names the rung it stopped
at as a one-token disposition. The register's objection is to deliberating the
rungs in user-visible prose; a recorded stopping point is the audit trail a
supervisor needs to see the decision at all.

**`Approach:` is working material, and the `failed` status must stop implying
otherwise.** The plan template declares `Approach` correctable in place and the
spec-authoring skill states that no gate observes it. The current `failed`
wording makes a heavier named construction read as binding, which is the
measured cause of the abstraction the probe produced. The correction reframes
`failed` around `Done when:` — the field a gate does read.

### Behavior & rules

- The bounded search runs once per decision boundary, across the execution root.
- An adequate hit is reused. A decisive empty result ends the search.
- The first rung that satisfies `Done when:` stops the walk.
- A lighter route than the named `Approach:` is taken and recorded as a
  deviation; it never overrides an explicit requirement, a governance decision,
  or a trust-boundary control.
- `failed` means no available route satisfies `Done when:`.

### Failure, edge cases & resilience

The over-fire case is the one to guard: a rule that makes the implementer hunt
indefinitely, refuse to write new code, or fabricate a rung label for a
declination no rung explains. The first two have gated control fixtures whose
outcomes must not move. The third is observation-only: the non-rung control is
run and recorded, and a fabricated label there is a prompt for a reader to look,
not a failed gate.

### Dependencies & integration

No new dependency, module, or top-level directory. The changed files are
projected into `.claude/` and `.agents/` by `agentbundle catalogue self-host`;
those copies are never edited directly.

## Tasks

### T1: the implementer reuses an adequate solution and may take a lighter route

**Depends on:** none

**Touches:** packs/core/.apm/agents/implementer.md, docs/specs/construction-time-razor/notes/probes/*, docs/specs/construction-time-razor/notes/verification-ledger.md

**Verification mode:** goal-based check

**Tests:**
- `docs/specs/construction-time-razor/notes/probes/run-probe.sh` materialises
  every fixture and drives two runs each. It is the generator for every figure in
  the ledger. It scores only the gated outcomes; the rung each report names is
  collected alongside them as recorded evidence and never decides completion, so
  the runner holds no expected rung.
- Reuse fixture, proving AC-0001: the emitted function delegates to the sibling
  helper. Proven red on the pre-change contract — two runs, byte-identical
  duplication, and no report mentioned a search, a candidate or a rung.
- Helper-absent control, proving AC-0003 and AC-0004: no new module is emitted
  and status is `ready`. The runner also records the rung each report names, for
  the ledger; no criterion grades it.
- Every satisfiable fixture's `Done when:` one-liner is run and its exit code and
  stdout recorded, proving AC-0019. This is the external functional signal; a
  `ready` status never stands in for it.
- Inadequate-candidate control, proving AC-0006: its sibling helper collapses
  whitespace runs but does not strip, so reusing it alone breaks `Done when:`.
  The report must name it as a candidate the search found and record what it did
  with it, with the reason; both reusing it in part and declining it satisfy the
  criterion. The predicate reads the candidate's name in the report, which is
  what went missing 0 of 2 times before the rule repair. Whether the implementation composes with it or
  declines it is recorded but not graded — measured runs took one route each and
  both satisfied the outcome. AC-0019 is the over-fire guard on this fixture.
- Heavy-`Approach:` fixture, proving AC-0007, AC-0008 and AC-0009: no new module
  is emitted, status is `ready`, and the substitution is recorded under
  `Deviations from the task body`. Proven red on the pre-change contract — two
  runs, the named class and module built both times.
- Heavy-required control, proving AC-0010 and AC-0011: two callers need different
  configurations, so the named construction is genuinely warranted. It must still
  be built, and the report must not claim a lighter substitution.
- No-route control, proving AC-0012: a `Done when:` no route satisfies is
  refused rather than claimed as `ready`. Accept `failed` or `blocked`; the
  fixture's contradictory conditions are a supervisor decision, which the shipped
  contract routes to `blocked`.
- Regression floor: `python3 -m pytest packs/core/tests/skills/work-loop/test_sequential_implementer_dispatch.py -q` and the roster sibling stay green. The bullet's placement below the first `<!--` is what keeps the envelope slice at two bullets.
- `no stub (goal-based)`

**Approach:**
- Add one operating-envelope bullet below the bundled-fixes comment and above
  `- **Gates:**`, naming the ladder's heading in `AGENTS.md`, the single bounded
  search, reuse of an adequate hit, the recorded stopping rung, the named
  rejected candidate, and the authority to take a lighter route than `Approach:`
  with the swap recorded as a deviation.
- Reword the `failed` status so it turns on no available route satisfying
  `Done when:` rather than on the task body's approach not working.
- Keep the phrase "execution root" out of any bullet placed above the first
  `<!--`.

**Done when:** every check in this task's `Tests:` holds, each behavioural arm
over two consecutive runs.

**Grounding:** intent register CUT-04, CUT-06 and CUT-16.

### T2: a declined temptation names the rung that killed it

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, docs/specs/construction-time-razor/notes/probes/*, docs/specs/construction-time-razor/notes/verification-ledger.md

**Verification mode:** goal-based check

This task carries no acceptance criterion. Which rung a declination names is not
mechanically decidable from the ladder, so the rule ships as working material
protected by the T3 content pins rather than as contract. The spec's Retired
identifiers section records the demotion, its destination, its pin and the owner
authority for it. The probes below are recorded evidence, not gates.

**Tests:**
- Declination fixture, recorded in the ledger: the frozen request plants two
  temptations whose ladder answers differ — one addition the request never asks
  for, and one hand-written routine the language's own library already provides.
  The runner records which rung, if any, each emitted entry names. The
  pre-change baseline is six entries and no rung named, so any rung at all is a
  visible change; the ledger states this is a recorded observation and not a
  detection claim.
- Non-rung control, recorded in the ledger: one temptation declined by an
  explicit accepted requirement rather than by any rung. The runner records
  whether that entry names a rung, which is the over-fire signal a reader
  inspects.
- Body-length floor, gated: `work-loop/SKILL.md`'s body stays under 1,000 lines,
  measured as `skill_spec_lint.py` measures it.
- `no stub (goal-based)`

**Approach:**
- Extend the PLAN-step declination instruction so each line carries the rung that
  killed the temptation alongside the temptation and the reason, and admits a
  stated non-rung reason where no rung applies.
- Disambiguate the word: the line says `Cut before adding` rung explicitly,
  because this file already uses "rung" for recovery rungs, the intent ladder,
  and the fidelity ladder.
- Edit only at the PLAN step, outside both sha256-pinned windows.

**Done when:** the body-length floor holds, both probes are run and recorded in
the ledger, and the T3 pins for this rule and its non-rung exception exist and
each fails on its own obligation's removal.

**Grounding:** the register's disposition that a recorded rung is not ladder
narration.

### T3: the release surface is closed and the deltas are protected

**Depends on:** T1, T2

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md, packs/core/.apm/skills/work-loop/evals/evals.json, packs/core/tests/pack/*, .claude/**, .agents/**

**Verification mode:** goal-based check

**Tests:**
- Both manifests carry the same version, exactly one patch increment above the
  version at `git merge-base HEAD origin/main`, proving AC-0015. Compute the base
  rather than restating a literal target: another change may bump the pack first.
  Fail closed if that ref does not resolve. This is a delivery-time check run
  once, not a standing test — asserting `base patch + 1` on every branch reds
  `main`, where the merge base is `HEAD`, and every branch owing no bump.
- `agentbundle catalogue self-host --root .` reports no drift and
  `agentbundle catalogue verify --root .` passes, proving AC-0016. Run self-host
  on a clean tree: it refuses a dirty one.
- `docs/product/changelog.md` carries `## [core][<version>]` directly beneath
  `## [Unreleased]` with nothing between, proving AC-0017. The repository's own
  `tests/roster/test_verification_ledger_contract.py` pins the same adjacency.
- `evals.json` validates against its schema, and carries one case per rule as the
  Behaviour register durable output rather than as a criterion. The manifest
  admits only `id`, `prompt`, `expected_output`, `assertions` and an optional
  `files`, so the register status rides each case's `id` prefix and is stated in
  full in the changelog entry and the verification ledger — not forced into
  `expected_output`, and not carried on an invented schema key.
- Four new pack-local content pins, anchored at `parents[2]` so none reads above
  its pack, covering the four obligations enumerated under Construction tests.
  Each pin must fail on the removal of its own obligation, so a single pin over a
  shared heading does not satisfy this bullet.
- `make lint-ruff lint-mypy` clean; `python3 -m pytest packs/core/tests/pack/ -q` green.
- `no stub (goal-based)`

**Approach:**
- Bump both manifests, add the changelog entry, add the three register cases,
  add all four independent content pins, then run self-host last so it projects
  the final bytes.

**Done when:** every check in this task's `Tests:` holds.

**Grounding:** AC-0015 through AC-0017; `packs/AGENTS.md` version-bump,
self-host and eval-harness rules.

## Rollout

Adopters receive the change on their next pack install. The deltas tighten an
existing discipline and add no new required field to any artifact an adopter
already maintains, so no migration applies. Reverting is a prose revert plus a
version bump.

## Risks

- **A scored run is not deterministic.** Mitigated by two consecutive runs per
  arm and by paired controls; the three pre-change fixtures each produced
  byte-identical output across runs, so divergence is signal.
- **The rule over-fires into search paralysis or fabricated rung labels.** This
  is what the three control arms exist to catch.
- **The declination rule reads as ladder narration.** Dispositioned as a record
  rather than narration; the spec's Boundaries carry the decision so a reviewer
  sees it was decided.
- **Body-length pressure.** `work-loop/SKILL.md` is already past its advisory
  warning; T2 is one line plus a clause and T2's tests hold the 1,000-line floor.

## Changelog

- 2026-09-16 — Amendment 1. Four specification errors the delivery's own scored
  runs established: AC-0005 retired and AC-0012 narrowed, because each named one
  correct answer where the contract admits two and flipped between them on
  consecutive runs; AC-0017's path corrected; T3's register disclosure rehomed
  where the target schema can hold it. The rule repairs that preceded it — an
  unconditional search receipt and a directive lighter rung — were ordinary
  repairs against sound criteria and needed no amendment.
- 2026-09-16 — Drafted. Scope set by probes taken before authoring: the reuse,
  lighter-route, and declination criteria were each proven red on the pre-change
  contract, and a fourth candidate outcome about reviewer finding determinacy was
  refuted by probe and excluded.
