# Spec: construction-time razor

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0099
- **Brief:** none
- **Discovery:** `docs/product/intents/cut-before-adding-solution-ladder.md`
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Objective

The core pack's `Cut before adding` ladder governs the moment code is written,
not only the moment work is shaped. An implementer subagent holding one plan
task searches once for an existing solution before writing a new one, reuses an
adequate hit, and stops at the first rung that satisfies the task's `Done when:`
— including when the task body's `Approach:` names a heavier construction than
that rung. It records which rung it stopped at, so a supervisor reading the
report can see the decision rather than infer it. A supervisor writing the
declination register names the rung that killed each temptation, so a reader can
see a declined addition against the ladder instead of against an ad-hoc reason.
Both recordings are working material: they are read, not graded.

The user is anyone who installs the core pack and runs its delivery loop. Success
is that a reusable helper is reused, an unnecessary abstraction is not built, and
both outcomes are legible in the report.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth, gated | Applicable — the implementer's reuse and lighter-route rules are the gated behaviour | `packs/core/.apm/agents/implementer.md` | pack maintainer | Scored probe runs recorded in the verification ledger | The file carries the rules, its criteria hold, and self-host is clean |
| Current product truth, recorded | Applicable — the rung-recording rules survive as working material | `packs/core/.apm/agents/implementer.md`, `packs/core/.apm/skills/work-loop/SKILL.md` | pack maintainer | Recorded, unscored probe observations in the verification ledger, plus the content pins | Both files carry the rules, each pin fails on its own obligation's removal, and self-host is clean |
| Interface compatibility | Applicable — pack content changed, so installed copies must be re-derivable | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | pack maintainer | Matching patch version in both manifests | Versions match and `agentbundle catalogue verify` passes |
| Release history | Applicable — adopters read the changelog to decide whether to re-install | `docs/product/changelog.md` | pack maintainer | A `## [core][<version>]` section naming the behaviour change | That section sits directly beneath `## [Unreleased]` with nothing between |
| Behaviour register | Applicable — the pack owes an eval-harness update on non-cosmetic change | `packs/core/.apm/skills/work-loop/evals/evals.json` | pack maintainer | Frozen cases for the reuse, lighter-route and declination rules | Cases present and labelled as register entries, not detection |
| Reusable learning | Applicable — the measurement method generalises beyond this delivery | `project-knowledge` public seam | work-loop DECIDE | Distilled observation on differential probing of inherited prose rules | Routed or explicitly discarded at the terminal gate |
| Decision rationale | Not applicable — the governing RFC already carries the decision and its § 4 authorises a referencing delta | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Reference the `Cut before adding` ladder in `AGENTS.md` by name and let it own
  the rungs; a delta states only what the reader must now do differently.
- Place a new `implementer.md` operating-envelope bullet below the bundled-fixes
  comment, because the anchor test slices the envelope only as far as the first
  `<!--` and requires exactly two bullets containing "execution root" above it.
- Disambiguate "rung" wherever it appears in `work-loop/SKILL.md`, which already
  uses the word for recovery rungs, the intent ladder, and the fidelity ladder.
- Score every behavioural criterion over its frozen fixture and its paired
  control, and record both results.

### Ask first

- Adding `work-loop` to `pack.toml` `[pack.evals].skills`, which would reverse a
  deliberate exclusion and make this pack's largest eval set live.
- Converting any behavioural criterion into a standing repository test.
- Any change to either `AGENTS.md`, which sit at 162/170 and 143/150 lines and on
  readability floors.

### Never do

- Write a third copy of the ladder, or restate any rung's text in a delta.
- Introduce a new module, top-level directory, or dependency; this delivery
  changes prose contracts and their manifests only.
- Edit `.claude/` or `.agents/` projections of a changed `.apm/` file.
- Cite a governance record, spec name, acceptance criterion, or repository-only
  path in shipped pack content.
- Claim a case added to `work-loop`'s `evals.json` as detection.

## Testing Strategy

Every **gated** behavioural outcome is verified by **goal-based check**: a
scored run of the shipped contract against a frozen fixture, whose result is read
by a mechanical predicate over what the run emits — which symbol the emitted
module imports, whether a named module exists, which status the report carries.
The rung a report names is recorded but not gated; see the note below the
groups. The mode is goal-based rather than TDD because the subject is
a prose contract consumed by a model session, so no in-process invariant is
compressible; and it is not manual QA because each outcome is decided by a
predicate over emitted bytes rather than by a reader's judgement.

Each criterion is scored over two consecutive runs of its fixture and must hold
in both. Recorded, ungraded observations are collected on the same runs. Two runs is the bar because the pre-change fixtures each produced
byte-identical output across their runs, so a single divergence is signal.

**A code-shape outcome and a report-content outcome are separate criteria.** They
have separate failure modes and separate remedies: an implementation can reuse
the right helper and misreport what it did, or report correctly and build the
wrong thing. Bundling them lets a half-met item read as met.

**The rung a report names is recorded, never graded.** The runner records it
for the ledger, and no criterion decides whether it is the right rung. A constant
or fabricated rung is therefore visible to a reader but has no completion effect,
which is the cost the owner accepted rather than putting a judgement in the
completion path.

**A gated rule's control is a criterion, not plan detail.** Each gated rule
carries a control fixture differing only in the rule's trigger, and that
control's outcome is its own acceptance criterion. A control recorded only in the
plan can never fail the contract, so a remedy that over-fires would still ship.
The rung-recording rule is not gated and its observations are recorded evidence,
which is the cost the owner accepted for it.

- **Reuse of an adequate solution (AC-0001)** — goal-based check on the reuse
  fixture, whose sibling helper fully satisfies the task.
- **No reuse where nothing adequate exists (AC-0003, AC-0004)** — goal-based
  check on the helper-absent control.
- **No reuse of an inadequate candidate (AC-0006)** — goal-based check on the
  inadequate-candidate control, whose helper covers part of the outcome only. It
  is the only fixture in which a rejected candidate exists to be named. Whether
  the implementation composes with the partial helper or declines it is not
  graded: both satisfy the outcome, and a criterion that picked one graded a
  preference. AC-0019 is the over-fire guard here — reusing a hit that genuinely
  does not fit breaks `Done when:`.
- **The lighter route (AC-0007, AC-0008, AC-0009)** — goal-based check on the
  heavy-`Approach:` fixture, whose `Done when:` one function in the existing
  module satisfies.
- **A required construction survives (AC-0010, AC-0011)** — goal-based check on
  the heavy-required control, whose two callers need different configurations.
  AC-0011 keeps the report honest: the rule must not teach a run to claim a
  lighter substitution it did not make.
- **A refusal stays reachable (AC-0012)** — goal-based check on the no-route
  control. Without it the lighter-route rule could pass by relaxing its own bar.
  The criterion reads the refusal, not which refusal: a task no route satisfies
  is usually a task whose body is wrong, and the shipped contract routes that to
  `blocked` rather than `failed`. Claiming `ready` is the failure.
- **The task actually works (AC-0019)** — goal-based check across the closed set
  of satisfiable fixtures. A report's `ready` status is the run's own account of
  itself, so functional success is read from the fixture's `Done when:` one-liner
  instead. This is one predicate substituted at each named fixture, checkable as
  written at every one of them.
- **Release surface (AC-0015, AC-0016, AC-0017)** — goal-based check: two version
  strings compared to each other and to the merge base, two catalogue commands,
  one heading position, each with an exit code.

**Which rung a report names is not gated, and neither is the declination
rule.** Both shipped contracts still require a rung to be recorded, but no
criterion decides whether the recorded rung is the right one, and no criterion
scores the declination register at all. Which rung applies to a given fixture is
not resolvable from the ladder by machine — the standard-library rung and the
one-obvious-line rung both answer a one-line library call — so gating on it would
put a judgement in the completion path.

Three obligations therefore survive as working material: the implementer records
the rung it stopped at, a declination names the rung that killed it, and a
declination declined for a reason no rung covers may state that reason instead.
Their protection is the content pins recorded in the plan, which fail if any of
the three disappears. Probe observations about them are recorded in the
verification ledger and carry no completion effect: a surprising observation is a
prompt to look, not a failed gate.

## Acceptance Criteria

- [ ] **AC-0001.** On the reuse fixture, the emitted function delegates to the
  existing sibling helper rather than reimplementing its behaviour.
- [ ] **AC-0019.** On every fixture whose task is satisfiable — the reuse
  fixture, the helper-absent control, the inadequate-candidate control, the
  heavy-`Approach:` fixture and the heavy-required control — the task's
  `Done when:` one-liner exits zero and prints its stated expected value.
- [ ] **AC-0003.** On the helper-absent control, no new module is emitted.
- [ ] **AC-0004.** On the helper-absent control, the report status is `ready`.
- [ ] **AC-0006.** On the inadequate-candidate control, the report names that
  helper as a candidate the search found, and records what it did with it —
  reused in part, or not used at all — with the reason. Both dispositions
  satisfy this criterion; saying nothing about the candidate does not.
- [ ] **AC-0007.** On the heavy-`Approach:` fixture, no new module is emitted.
- [ ] **AC-0008.** On the heavy-`Approach:` fixture, the report status is
  `ready`.
- [ ] **AC-0009.** On the heavy-`Approach:` fixture, the report records the
  substitution under `Deviations from the task body`.
- [ ] **AC-0010.** On the heavy-required control, whose two callers need
  different configurations, the named construction is still built.
- [ ] **AC-0011.** On the heavy-required control, the report claims no lighter
  substitution.
- [ ] **AC-0012.** On the no-route control, whose `Done when:` no available route
  satisfies, the report does not claim `ready`; it refuses, with either `failed`
  or `blocked`.
- [ ] **AC-0015.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the same version, and it is
  exactly one patch increment above the version at the merge base of this branch
  and `origin/main`. Where that merge base does not resolve, the criterion fails
  rather than assuming a baseline.
- [ ] **AC-0016.** `agentbundle catalogue self-host --root .` reports no drift
  and `agentbundle catalogue verify --root .` passes.
- [ ] **AC-0017.** `docs/product/changelog.md` carries a `## [core][<version>]`
  section directly beneath `## [Unreleased]`, with no other section between
  them.

## Retired identifiers

No identifier listed here is reused. Two different moves are recorded, and they
differ in whether an obligation survived.

**Demoted to working material** — AC-0002, AC-0013, AC-0014 and AC-0018. The
obligation survives in the shipped contracts: the rung-recording rules in
`packs/core/.apm/agents/implementer.md` and
`packs/core/.apm/skills/work-loop/SKILL.md`. Its protection is the four content
pins enumerated in the plan's Construction tests, each failing on the removal of
its own obligation. What was retired is the grading of *which* rung is named: the
reuse fixture's report naming rung 2, each planted temptation's entry naming its
rung, a non-rung declination naming no rung, and the helper-absent control's
report naming the standard-library or one-obvious-line rung. Owner authority:
user confirmation 2026-09-16, after four review rounds located the
non-mechanizable property.

**Retired outright** — AC-0005, under Amendment 1. It required the
inadequate-candidate control to decline the partial helper, but composing with it
and declining it are both correct, and consecutive runs of the unchanged fixture
took one route each. No obligation survives it and no pin is owed, because
AC-0006 already carries the reporting obligation and AC-0019 the functional one.
Owner authority: the amendment recorded in `notes/verification-ledger.md`.

- AC-0002
- AC-0005
- AC-0013
- AC-0014
- AC-0018

## Follow-ons

- pack maintainer: `docs/product/research/behavior-controls-inventory.md:393` —
  that line records, as an inferred claim, that the razor "provides no selective
  trigger" for any authoring agent. This delivery measures and closes the claim
  for the implementer subagent only; the same question for every other authoring
  agent in the pack is unmeasured and separately scoped.

## Assumptions

- Technical: on the pre-change contract the implementer emits byte-identical
  code whether or not a reusable helper exists, so the ladder's search rung
  never fires (source: probe, three runs, `notes/verification-ledger.md`)
- Technical: on the pre-change contract a task whose `Approach:` names a
  class-and-new-module construction produces that construction, so `Approach:`
  is read as binding (source: probe, two runs, `notes/verification-ledger.md`)
- Technical: on the pre-change contract a declination register names no rung
  (source: probe, six entries and no rung named, `notes/verification-ledger.md`)
- Technical: exactly two ladder copies exist, at `AGENTS.md` and
  `packs/core/seeds/AGENTS.md`, pinned for seven numbered rungs, textual
  difference, and positional order (source:
  `tests/roster/test_razor_guidance_repository.py`,
  `packs/core/tests/pack/test_razor_guidance.py`)
- Technical: the envelope anchor test slices `## Operating envelope` only as far
  as the first `<!--` and requires exactly two bullets containing "execution
  root" (source: `packs/core/tests/skills/work-loop/test_sequential_implementer_dispatch.py:53`)
- Technical: no test pins the declination line or the implementer's
  `failed`-status text (source: grep over `packs/core/tests/`, `tests/`,
  `tools/` returning no match)
- Technical: `work-loop/SKILL.md`'s body is 885 lines against a 1,000-line error
  and a 500-line warning, measured as the lint measures it (source:
  `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:518`)
- Technical: `work-loop` is absent from `pack.toml` `[pack.evals].skills`, so
  `pack_evals.py` never opens its `evals.json` (source: `packs/core/pack.toml`)
- Process: a changed `.apm/` file owes a patch bump in both manifests, a
  self-host run, no internal-governance citation, and an eval-harness update
  (source: `packs/AGENTS.md`)
- Process: the eval-harness obligation is discharged by adding labelled register
  cases to `work-loop`'s `evals.json` without claiming them as detection
  (source: user confirmation 2026-09-16)
- Product: naming a rung is a recorded disposition rather than the ladder
  narration the intent register dispositions against (source: user confirmation
  2026-09-16)
- Product: the criteria hold for an adopter who installs the pack, so fixtures
  carry the portable seed `AGENTS.md` rather than this repository's root copy
  (source: user confirmation 2026-09-16)
