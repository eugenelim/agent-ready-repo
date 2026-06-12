# Plan: tdd-stub-generation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **documentation, not code**: one new reference file plus pointer-edits to two skills, one agent, and one convention doc — all at their **seeds** under `packs/`, then regenerated into the `.claude/.agents/.codex` projections by `make build-self`. The shape of the work is therefore "author the reference, thread four short pointers into the existing artifacts, regenerate, verify zero drift." The riskiest part is *not* the edits — it is the load-bearing assumption that compilable red stubs can be produced from an acceptance criterion *before* implementation exists; so the **spike (T1) runs first** and de-risks that against a real existing spec. The reference (T2) is the core deliverable; the four pointer-edits (T3–T5) are small and depend only on it; T6 regenerates and runs the drift/skill-spec gates; T7 does docs hygiene and status flips. There is no runtime test surface — every task verifies goal-based (`grep`/build/lint one-liners) except the spike, which is manual QA.

## Constraints

- **RFC-0028 (Accepted)** — the governing decision. No new skill, no new pre-`work-loop` gate, no new artifact type (`coverage-matrix.md`); the vehicle is a progressive-disclosure reference inside `work-loop`'s TDD mode, fed by `new-spec`.
- **Seed/projection discipline** (AGENTS.local.md) — edit seeds, never projections; `make build-check` is the drift gate the eventual PR must pass.
- **Adopter-genericity** (AGENTS.local.md:60-64) — shipped prose must not reference catalogue-internal paths.
- **CONVENTIONS § 4** — the contract-vs-construction-test split the reference's stub-fullness rule maps onto.

## Construction tests

Per-task goal-based checks live under each task's `Tests:` below. Cross-cutting:

**Integration tests:** none beyond per-task checks — there is no runtime code; the closest thing to an integration test is T6's `make build-check`, which verifies the whole seed→projection pipeline is drift-free after all edits.
**Manual verification:** the T1 spike (pytest stubs from a Shipped spec compile against the AC surface and go red against an absent/emptied implementation) and a final read-through that the reference's worked example is itself coherent.

## Design (LLD)

Shape is `service` → the relevant sub-sections are decomposition, interfaces & contracts, behavior & rules, and failure/resilience. The "stack" here is **APM-pack Markdown** (skills/agents projected via `agentbundle.build`) plus **Python tooling** for verification (`pytest` for the spike; `make build-self`/`make build-check`; `tools/lint-skill-spec.py`). Kept deliberately thin per the spec's `Shape`.

### Component / module decomposition
The reference `tdd-stubs.md` is one document with five named phases — **parse → resolve-stack → generate → validate → record**. Its consumers/insertion points: `work-loop` PLAN *Design tests up front* (primary caller, load-on-demand pointer), `work-loop` EXECUTE TDD red step (consumes the stub), and `new-spec` Testing Strategy step (self-check pointer, no generation). New artifact: the reference only. Reused: the existing `references/` mechanism and the per-task `Tests:` subsection structure. Traces to: AC 1, AC 4, AC 5.

### Interfaces & contracts
The only "interface" is the **stub↔EXECUTE handoff convention**: a `// STUB:`/`# STUB:` comment carrying the AC number in the generated test, plus a `stub: true` field in the plan task's `Tests:` subsection. This is a documented convention, not a `contracts/` artifact. Traces to: AC 3, AC 6.

### Behavior & rules
The stub-fullness rule (full assertion when the AC pins behaviour; contract-surface/shape assertion with a placeholder otherwise; never less than a compiling assertion; never a bare `TODO`). Grouping rule: one stub file per plan task. Stack-detection rule: detect the framework from config/manifests; elicit when ambiguous. Degrade rule: on compile failure, emit `draft (uncompiled), reason noted` and surface — never block. Traces to: AC 1, AC 2, AC 3.

### Failure, edge cases & resilience
Stack-detection failure or an unusual test setup → the stub is recorded as `draft (uncompiled)` with the reason in its `Tests:` subsection; the coverage/testability signal survives even when compilation doesn't. A non-compiling stub **surfaces** for human/adversarial judgement; it does not block the plan gate (mirrors RFC-0028 Decision 4 / Risk 3). Traces to: AC 1, AC 9.

> **Rollout & deployment:** see [`## Rollout`](#rollout) — trivial for a docs-only change.

## Tasks

### T1: Spike — stubs from a Shipped spec compile against the AC surface and go red against an absent implementation

**Depends on:** none

**Tests:** (manual QA — this is the de-risk spike)
- Pick `docs/specs/spec-code-ref-lint/` (small, Python-lint, TDD-shaped); if it proves a poor fit, fall back to another small TDD-mode spec and note why. **Note the target is Shipped** — its code already exists — so the spike *simulates* the pre-implementation state rather than observing it on live code (every spec in the repo is already implemented).
- Hand-derive a pytest stub per TDD-mode AC, asserting the AC's observable surface with a placeholder where the value isn't yet knowable.
- Run `python -m py_compile` (or `pytest --collect-only`) on the stubs → they **parse/compile against the contract/AC surface** (this is RFC-0028's structural claim — the AC is concrete enough to type a test against). Record the transcript.
- Demonstrate **redness** by running the stubs against an **absent/emptied implementation** — import the interface from a local empty shim (or target a deliberately not-yet-defined symbol) so the assertion fails — simulating day-0. Record the transcript and the Shipped-target caveat.
- Record any AC that could not be turned into a stub as a "spec under-specified" finding.

**Approach:**
- Read the chosen spec's Acceptance Criteria + Testing Strategy and its contract/LLD if any.
- Write the stubs into `docs/specs/tdd-stub-generation/notes/spike.md` (not into the spiked spec's tree).
- Capture the compile-against-surface evidence and the red-against-absent-impl evidence, plus the "what made a stub easy/hard" observations — these become the reference's worked example and its degrade rule.

**Done when:** `notes/spike.md` shows ≥1 AC turned into a pytest stub that **compiles against the contract/AC surface** and is **red against an absent implementation**, with both command transcripts, the Shipped-target caveat, and a one-line verdict on whether pre-implementation stubbing held. Verification: manual QA. Satisfies AC 9.

### T2: Author the `tdd-stubs.md` reference

**Depends on:** T1

**Tests:** (goal-based)
- `grep` the file for the five phase headings (parse, resolve-stack, generate, validate, record) → all present.
- Assert a fenced ```python pytest worked example exists, plus a stack-agnostic "detect the framework" recipe.
- `grep -E 'tools/lint-|make build-self|\.github/workflows/'` over the file → **no matches**; and no *named* internal spec path (`docs/specs/<concrete-name>/`) → none — the generic `docs/specs/<feature>/plan.md` workflow placeholder is allowed and expected (AGENTS.local.md classes it as workflow vocabulary, not a citation). (adopter-genericity, AC 2)
- `grep` for the stub-fullness rule wording and the `// STUB:` + `stub: true` marker convention → present (AC 1, AC 3).

**Approach:**
- Create `packs/core/.apm/skills/work-loop/references/tdd-stubs.md` (the seed).
- Document the five phases; fold the spike's worked example in as the Python/pytest example; write the generic detection recipe (config files / manifests, elicit-when-ambiguous, mirroring `new-spec` step 4c's elicitation).
- State the stub-fullness rule, the one-file-per-task grouping, and the degrade-to-draft behaviour. Define the `// STUB:`/`stub: true` marker convention **once** (in the generate/record phase) and have any other mention point back to it, so the two ACs that touch it (AC 1's `record` phase, AC 3's marker) don't drift.
- Keep all prose adopter-generic.

**Done when:** the goal-based checks above pass and a read-through confirms the worked example is coherent. Verification: goal-based + manual. Satisfies AC 1, AC 2, AC 3.

### T3: Thread the reference into `work-loop` SKILL.md

**Depends on:** T2

**Tests:** (goal-based)
- `grep` the **seed** `packs/core/.apm/skills/work-loop/SKILL.md` PLAN *Design tests up front* for a `references/tdd-stubs.md` pointer → present.
- `grep` the EXECUTE TDD red step for a sentence noting a pre-written stub may already satisfy the red step → present.

**Approach:**
- Add a one-line load-on-demand pointer in the *Design tests up front* bullet (mirroring the existing `references/supervisor-mode.md` "load it on demand" style).
- Add a stub-aware clause to EXECUTE step 1 (red): if a stub exists for the task, the red test is already written — verify it's red, don't rewrite from scratch.

**Done when:** both greps hit in the seed. Verification: goal-based. Satisfies AC 4.

### T4: Point `new-spec` Testing Strategy at the reference

**Depends on:** T2

**Tests:** (goal-based)
- `grep` the seed `packs/core/.apm/skills/new-spec/SKILL.md` Testing-Strategy step (4) for a pointer to `tdd-stubs.md` as a testability self-check → present.
- Assert the wording states **no committed stubs at spec time** (self-check only).

**Approach:**
- Add a one-line pointer in step 4: an author may sanity-check each AC's stubbability against `tdd-stubs.md` while writing Testing Strategy, without generating committed stubs (those come in `work-loop` PLAN).

**Done when:** the grep hits and the "no committed stubs at spec time" qualifier is present. Verification: goal-based. Satisfies AC 5.

### T5: Document the convention (CONVENTIONS § 4) + quality-engineer timing note

**Depends on:** T2

**Tests:** (goal-based)
- `grep` the seed `packs/core/seeds/docs/CONVENTIONS.md` § 4 for the stub→EXECUTE handoff convention → present.
- `grep` the seed `packs/core/.apm/agents/quality-engineer.md` test-author mode for the in-PLAN-generation vs. post-impl-review timing distinction → present.

**Approach:**
- Add a short paragraph to CONVENTIONS § 4 (contract-vs-construction tests) describing the stub→EXECUTE handoff and the `// STUB:`/`stub: true` markers.
- Add one sentence to `quality-engineer` test-author mode noting the timing/persona distinction from in-PLAN stub generation.

**Done when:** both greps hit in their seeds. Verification: goal-based. Satisfies AC 6.

### T6: Regenerate projections and pass the gates

**Depends on:** T3, T4, T5

**Tests:** (goal-based)
- `make build-self` → exits 0 and regenerates `.claude/.agents/.codex` copies of the edited skills/agent and the projected `tdd-stubs.md`.
- `make build-check` → **zero drift** (exit 0).
- `python3 tools/lint-skill-spec.py` → passes for the edited skills.
- `diff` a projection against its seed for one edited file → IDENTICAL (spot-check the projection actually carries the edits).

**Approach:**
- Run `make build-self`, then `make build-check`; fix any seed/projection drift the gate names (its error message names the seed to edit).
- Run the skill-spec lint; address any spec violation.

**Done when:** all three commands are green and the spot-check diff is identical. Verification: goal-based. Satisfies AC 7, AC 8.

### T7: Docs hygiene + status flips

**Depends on:** T6

**Tests:** (goal-based)
- `grep docs/specs/README.md` for the `tdd-stub-generation` row → present.
- **Structural negative sweep (AC 10):** `git diff --name-only <base>..HEAD` shows no new top-level directory, no new skill directory (`*/.apm/skills/*/SKILL.md`), no `coverage-matrix.md`, and no dependency add or change to `loop-cohort.py` / `lint-spec-status.py` / `state.json` / any `requirements.txt` / `pyproject.toml` dependency list → all absent.
- `spec.md` Status is `Shipped` and every Acceptance Criterion is `[x]` or carries a `(deferred:)` anchor; `plan.md` Status is `Done`.
- `python3 .claude/skills/work-loop/scripts/lint-spec-status.py` → clean for this spec.

**Approach:**
- Add the feature to the live `docs/specs/README.md` active list.
- Run the structural negative sweep above to confirm none of AC 10's forbidden additions landed.
- Flip `spec.md` Status Draft→Shipped and tick each criterion from named evidence: AC 1–AC 8 from their tasks' green gates, **AC 9 from the T1 spike verdict**, **AC 10 from the negative sweep above**; flip `plan.md` Status to Done.

**Done when:** the row exists, the negative sweep is clean, statuses are flipped with every AC ticked from named evidence, and `lint-spec-status.py` is clean for this spec. Verification: goal-based. Satisfies the metadata invariants (CONVENTIONS § 4) and AC 10.

## Rollout

Docs-only, no infrastructure, no deployment sequencing, fully reversible (revert the commit). **Delivery:** the reference and pointers ship together in one branch; once merged, the next full-mode `work-loop` run that loads the PLAN step sees the pointer. No flag, no migration, no external dependency. The only ordering constraint is internal: regenerate projections (T6) after all seed edits, so the drift gate passes.

## Risks

- **The spike falsifies the premise** — if red stubs can't be derived from an existing spec's ACs before implementation, the reference's value proposition weakens. Mitigation: T1 runs first; a negative result is itself a finding (surface to the user before authoring T2 in full).
- **Drift gate friction** — editing a projection by mistake trips `make build-check`. Mitigation: the Always-do boundary and T6 make seed-editing explicit; the gate's error names the seed to fix.
- **Adopter-genericity slips** — a worked example that references a catalogue-internal path would break in adopters. Mitigation: T2's grep test fails closed on any such reference.

## Changelog

- 2026-06-12: initial plan (authored via `new-spec` from RFC-0028; decisions on Shape=service, per-task stub grouping, comment+`stub:true` marker, Python-worked-example+generic-detection, and `spec-code-ref-lint` spike target confirmed by the user).
- 2026-06-12: implemented T1–T7. Spike (T1) confirmed RFC-0028's structural claim — stubs derived from a Shipped spec's ACs compile against the AC surface and go red against an absent impl; finding (positive-contract ACs earn a red, pure-exclusion ACs need a paired positive) folded into the reference's stub-fullness rule. All gates green (build-check zero-drift, lint-skill-spec 0 errors). One adversarial-review round: 3 Blockers were the pending status flips (resolved here), 1 Nit (spike marker form) applied. Status → Shipped/Done.
