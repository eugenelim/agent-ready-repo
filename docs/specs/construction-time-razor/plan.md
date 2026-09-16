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
  either changed file's behaviour, so every behavioural criterion is scored at
  delivery rather than by a standing suite.

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
without over-firing. Every criterion is therefore scored against a fixture pair
that differs only in the rule's trigger. One committed script materialises all
six fixtures into a temporary directory so the evidence regenerates rather than
being hand-curated; the fixtures are not loose repository files because
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

Protection, not criteria: T3 adds one pack-local content pin asserting that
`implementer.md` names the ladder by its heading and states no numbered rung of
its own. Its purpose is to catch silent deletion of the delta and to catch a
future third copy; it is recorded here rather than in the spec because a check
that a sentence exists cannot decide whether the behaviour holds.

## Durable-output map

| Spec durable output | Task | Evidence the task produces |
| --- | --- | --- |
| Current product truth | T1, T2 | Scored fixture-pair results in `notes/verification-ledger.md` |
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
declination no rung explains. Each of those has a paired control fixture whose
outcome must not move.

### Dependencies & integration

No new dependency, module, or top-level directory. The changed files are
projected into `.claude/` and `.agents/` by `agentbundle catalogue self-host`;
those copies are never edited directly.

## Tasks

### T1: the implementer reuses an available solution and may take a lighter route

**Depends on:** none

**Touches:** packs/core/.apm/agents/implementer.md, docs/specs/construction-time-razor/notes/probes/*, docs/specs/construction-time-razor/notes/verification-ledger.md

**Verification mode:** goal-based check

**Tests:**
- `docs/specs/construction-time-razor/notes/probes/run-probe.sh` materialises the
  fixture pairs and drives one scored run each. It is the generator for every
  figure in the ledger; no fixture is hand-placed in the tree.
- Reuse pair for AC-0001 and AC-0002: the helper-present arm asserts the
  emitted target module imports the sibling helper and contains no second
  whitespace-collapse implementation; the helper-absent control asserts no new
  module appears and the status is `ready`. The helper-present arm is proven red
  on the pre-change contract (two runs, byte-identical duplication).
- Report-content checks for AC-0003 and AC-0004 read the run's
  returned report for the named rung and, on the helper-present arm, for the
  rejected candidate and its reason.
- Lighter-route pair for AC-0005 and AC-0006: the heavy-`Approach:`
  arm asserts no new module is emitted and the substitution is recorded under
  `Deviations from the task body`; its control names a heavy construction two
  callers genuinely require and asserts the construction is still built. The
  heavy arm is proven red on the pre-change contract (two runs, the named class
  and module created both times).
- `failed`-status control for AC-0007: a task no route
  satisfies still returns `failed`.
- Regression floor: `python3 -m pytest packs/core/tests/skills/work-loop/test_sequential_implementer_dispatch.py -q` and the roster sibling stay green. The bullet's placement below the first `<!--` is what keeps the envelope slice at two bullets.
- `no stub (goal-based)`

**Approach:**
- Add one operating-envelope bullet below the bundled-fixes comment and above
  `- **Gates:**`, naming the ladder's heading in `AGENTS.md`, the single bounded
  search, reuse of an adequate hit, the recorded stopping rung, and the
  authority to take a lighter route than `Approach:` with the swap recorded as a
  deviation.
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

**Tests:**
- Declination pair driven by the same runner. The main arm asserts every entry
  in the emitted register names a `Cut before adding` rung, proving AC-0008; it
  is proven red on
  the pre-change contract (one frozen request produced six entries and no rung).
- The control arm's frozen request carries one temptation declined by an explicit
  accepted requirement rather than by any rung, and asserts that entry records
  its non-rung reason and names no rung, proving AC-0009. This is the over-fire guard: it fails if
  the rule forces a fabricated rung label onto every line.
- Body-length floor: `work-loop/SKILL.md`'s body stays under 1,000 lines,
  measured as `skill_spec_lint.py` measures it.
- `no stub (goal-based)`

**Approach:**
- Extend the PLAN-step declination instruction so each line carries the rung
  that killed the temptation alongside the temptation and the reason, and admits
  a non-rung reason where no rung applies.
- Disambiguate the word: the line says `Cut before adding` rung explicitly,
  because this file already uses "rung" for recovery rungs, the intent ladder,
  and the fidelity ladder.
- Edit only at the PLAN step, outside both sha256-pinned windows.

**Done when:** every check in this task's `Tests:` holds, each behavioural arm
over two consecutive runs.

**Grounding:** the register's disposition that a recorded rung is not ladder
narration.

### T3: the release surface is closed and the deltas are protected

**Depends on:** T1, T2

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, CHANGELOG.md, packs/core/.apm/skills/work-loop/evals/evals.json, packs/core/tests/pack/*, .claude/**, .agents/**

**Verification mode:** goal-based check

**Tests:**
- Both manifests carry the same version, one patch above 2.26.8, proving AC-0010.
- The `[core]` changelog entry sits directly under `[Unreleased]`, proving
  AC-0011.
- `agentbundle catalogue self-host --root .` reports no drift and
  `agentbundle catalogue verify --root .` passes, proving AC-0012. Run
  self-host on a clean tree: it refuses a dirty one.
- `evals.json` validates against its schema and carries one case per rule,
  proving AC-0013. Each case's own text records that the set is a
  behaviour register, because this skill is outside the eval allowlist.
- One new pack-local content pin asserts `implementer.md` names the ladder
  heading and contains no numbered rung of its own — the protection recorded
  under Construction tests, anchored at `parents[2]` so it never reads above its
  pack.
- `make lint-ruff lint-mypy` clean; `python3 -m pytest packs/core/tests/pack/ -q` green.
- `no stub (goal-based)`

**Approach:**
- Bump both manifests, add the changelog entry, add the three register cases,
  add the content pin, then run self-host last so it projects the final bytes.

**Done when:** every check in this task's `Tests:` holds.

**Grounding:** `packs/AGENTS.md` version-bump, self-host and eval-harness
rules.

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

- 2026-09-16 — Drafted. Scope set by probes taken before authoring: the reuse,
  lighter-route, and declination criteria were each proven red on the pre-change
  contract, and a fourth candidate outcome about reviewer finding determinacy was
  refuted by probe and excluded.
