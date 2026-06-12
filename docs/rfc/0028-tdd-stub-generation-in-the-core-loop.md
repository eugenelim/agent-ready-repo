# RFC-0028: TDD stub generation woven into the core loop — a progressive-disclosure reference for `work-loop` TDD mode

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** mubeen-acn
- **Approver:** eugenelim
- **Date opened:** 2026-06-11
- **Date closed:** 2026-06-12
- **Related:** RFC-0025 (`work-loop` light mode — where the full-mode boundary this rides on is drawn); RFC-0019 (LLD-aware spec/plan — the `## Design (LLD)` component names stubs fall back to when a spec names no `Contract:`); `work-loop` skill (PLAN *Design tests up front*; EXECUTE TDD red step); `new-spec` skill (Testing Strategy + Acceptance Criteria); `quality-engineer` agent (test-author mode); `docs/CONVENTIONS.md` § 4 (contract vs. construction tests)

## The ask

- **Recommendation (BLUF):** Do **not** add a standalone `generate-test-stubs` skill with its own pre-`work-loop` gate and its own `coverage-matrix.md` artifact. Instead, fold spec→test-stub generation into **the core loop we already engineer**: a **load-on-demand progressive-disclosure reference** — `work-loop/references/tdd-stubs.md` — that the existing PLAN *“Design tests up front”* step uses to turn each TDD-mode acceptance criterion into a **compilable, validated red stub** in `plan.md`, consumed unchanged by EXECUTE’s red step. `new-spec`’s Testing Strategy is the feeder and points at the same reference for a testability self-check. **No new skill, no new pre-loop gate, no new artifact type.**

- **Why now (SCQA):** *Situation* — the repo runs a tight spec→plan→`work-loop` pipeline where TDD is the default verification mode and tests are *designed up front* (`work-loop` PLAN: “write construction tests for **every** task into `plan.md` … before EXECUTE begins”; `CONVENTIONS.md` § 4). *Complication* — there is a temporal gap: acceptance criteria are designed as **prose** in `new-spec`, and the first time anyone derives a *compilable* test is inside `work-loop` EXECUTE — the most expensive place to discover an AC is vague. The obvious fix is a **separate skill** between `new-spec` and `work-loop` that generates stubs — but that duplicates the loop’s own test-design discipline, bolts a second gate onto a pipeline we deliberately keep lean (RFC-0025), and lands the capability *outside* the core agentic loop rather than *in* it. *Question* — should the fix be a new skill and gate, or a sharpening of the loop’s existing TDD step delivered through the progressive-disclosure mechanism the repo’s skills already use?

- **Decisions requested:**
  1. **Mechanism: no new skill — enhance `work-loop`’s TDD mode in place.** Close the gap by sharpening the loop’s existing test-design step, not with a standalone skill. · recommended: yes · decide-by: on accept · default: yes.
  2. **Vehicle = a progressive-disclosure reference file**, `work-loop/references/tdd-stubs.md`, loaded on demand from the PLAN *“Design tests up front”* step (mirrors `references/supervisor-mode.md`, `references/state-schema.md`, `new-spec/references/contract-types.md`). SKILL.md gains a pointer, not the procedure. · recommended: yes · decide-by: on accept · default: yes.
  3. **Primary home = `work-loop`; `new-spec` feeds it.** Stubs are generated in PLAN (stack + contract are settled there; the plan’s per-task `Tests:` subsections are their home) and consumed in EXECUTE. `new-spec` gains a one-line pointer to the same reference so Testing Strategy can self-check “is each AC concrete enough to stub?”. This resolves the “work-loop or new-spec?” question as **both, asymmetrically**. · recommended: yes · decide-by: on accept · default: yes.
  4. **No new pre-loop gate; no new artifact.** Stub generation is a *step inside PLAN*, not a gate between `new-spec` and `work-loop`. The coverage signal lives in `plan.md`’s `Tests:` subsections and the spec’s Testing Strategy — **not** a new `coverage-matrix.md`. · recommended: yes · decide-by: on accept · default: yes.
  5. **Keep the substance that survives:** assertion-shaped compilable stubs, stack-detected output, single-pass generation with one bounded syntax-correction pass (no iterate-to-coverage retry loop), complements (does not replace) `quality-engineer`. · recommended: yes · decide-by: on accept · default: yes.
  6. **Full-mode-only, TDD-tasks-only.** Stub generation runs where TDD-mode tasks exist; light mode’s lean path (RFC-0025) is untouched, and goal-based / manual-QA tasks generate no stub. · recommended: yes · decide-by: on accept · default: yes.

## Problem & goals

**Diagnosis.** The pipeline has a *temporal* gap, not a *capability* gap. Tests are **designed** during `new-spec` (Testing Strategy + per-task `Tests:` prose in `plan.md`) and **executed** during `work-loop` (red-green-refactor). Between those two, nothing mechanically checks that an acceptance criterion can be turned into a *compilable* test. The loop already names the failure — “If you can’t write the test, the task is too vague to implement — sharpen the plan first” (`work-loop` PLAN) — but only discovers it *inside* EXECUTE, after PLAN has been signed off and the `loop-cohort` plan gate has unlocked. That is the expensive moment: vague-AC discovery during implementation, no batch coverage signal, a prose-only QA handoff.

**Why not a separate skill.** The obvious remedy is a *new* `generate-test-stubs` skill invoked between `new-spec` and `work-loop`, emitting a new `coverage-matrix.md` artifact, with a documented “if stubs exist, start from them” handoff convention. The diagnosis is right; that **vehicle** adds three things this repo is structurally biased against:

1. **A second test-design touch-point that duplicates the loop’s own.** `work-loop` PLAN *already* mandates “write construction tests for **every** task into `plan.md` … before EXECUTE.” A separate skill writes stubs once; the loop then re-derives them. Two owners for one job is exactly the drift surface `CONVENTIONS.md` § 4 (“contract vs. construction tests”) is built to avoid.
2. **A second gate on a pipeline we just made lean.** RFC-0025 (Accepted) removed machinery from the default path on a cost argument. Inserting a mandatory-feeling pre-loop step cuts against that grain; even kept optional, a sibling skill is precisely the kind of capability that doesn’t “stick” (CHARTER principle 4 — *used often enough to stick*) when the loop could own it natively.
3. **A new artifact format** (`coverage-matrix.md`) when the coverage signal already has a home: the plan’s per-task `Tests:` subsections and the spec’s Testing Strategy.

This follows eugenelim’s direction: *enhance the loop’s TDD mode with a reference file for progressive disclosure to generate TDD stubs and validate, as part of either the work loop or the `new-spec` skill — it should be part of the core agentic loop we engineer, not a separate skill.*

**Goals.**
- Make the loop’s *existing* “Design tests up front” step produce **compilable, validated** red stubs, not just prose — closing the gap *at* the step that already owns test design.
- Deliver the how-to via **progressive disclosure** (a reference loaded on demand), so SKILL.md stays lean and the guidance is long enough to be useful.
- Surface the coverage / testability signal **in artifacts that already exist** (`plan.md` `Tests:`, spec Testing Strategy) — no new file format.
- Detect the project’s test stack and emit framework-appropriate stubs.
- Keep the capability **inside the core loop** — one owner for test design, no parallel skill, no new gate.

**Non-goals** (could-have-been goals, deliberately dropped):
- *Not* a standalone skill or a pre-`work-loop` gate — the entire point of this proposal.
- *Not* a new `coverage-matrix.md` artifact — the signal rides existing artifacts.
- *Not* replacing `work-loop`’s TDD discipline — stubs are the *red* step, made concrete; green-refactor is unchanged.
- *Not* replacing `quality-engineer`’s test-author mode — different timing (in-PLAN vs. post-impl review) and different inputs (spec+contract vs. code+spec).
- *Not* an iterate-to-coverage retry loop — generation is single-pass with one bounded syntax-correction pass; gaps go back to the spec author as a sharper PLAN, not into a regenerate loop.
- *Not* integration/E2E scaffolding — unit-level stubs from individual ACs only; integration/E2E stays a `work-loop` concern.
- *Not* a light-mode feature — light mode (RFC-0025) keeps its lean inline spec untouched.

## Proposal

### Where it lives in the loop

```
new-spec ─────────────────────────────► work-loop (full mode)
  │  Testing Strategy + ACs              │
  │  (points at tdd-stubs.md for a       │ PLAN ── "Design tests up front"
  │   "is each AC concrete enough?"      │   │     └─ loads references/tdd-stubs.md
  │   self-check)                        │   │        → writes compilable red stubs
  └──────────────────────────────────────►  │          into plan.md per-task Tests:
                                          │   │        → coverage rolls up in Testing Strategy
                                          │  EXECUTE ── TDD red step starts from the stub
```

The capability is a **step refinement**, not a new node. PLAN’s *“Design tests up front”* sub-step gains: *“For TDD-mode tasks, materialize each task’s `Tests:` as a compilable, validated stub — see [`references/tdd-stubs.md`](references/tdd-stubs.md).”* EXECUTE’s red step is unchanged in shape; it now usually finds the red test already written. The full progression across phases is **red stub (PLAN) → green (EXECUTE) → complete the stub’s deferred assertions and edge cases (EXECUTE) → refactor with the tests as the safety net (EXECUTE)** — the existing red-green-refactor with the red step pulled forward and made compilable, plus an explicit build-out of any deferred assertions *before* the code refactor (which still holds the tests fixed).

### Decision 1 — mechanism (no new skill)

The loop already owns test design up front. We sharpen that step from “prose tests in `plan.md`” to “compilable, validated stubs in `plan.md`,” rather than standing up a parallel skill that re-does the same job one phase earlier. The diagnosis is unchanged; only the vehicle is.

### Stubs vs. full tests — what gets written when

(*“Stub” here means a **compilable-but-failing test**, not a test double / fake dependency.*)

A stub is the **floor, not a mandate to write half a test**. Write the *full* failing test whenever the AC pins exact behaviour — that is just classic TDD red, and it is preferred. The stub exists for the common case where the AC fixes the observable *shape* (“returns 201 with an order ID”) but the exact value only becomes knowable once the implementation exists. Asserting a *full* value you cannot yet know is the over-specification this repo already warns against (`CONVENTIONS.md` § 4: construction tests are “revisable if one turns out to over-specify an internal detail the plan changed”). So the rule is: **assert as much real, failing behaviour as the AC + contract honestly determine — never less than a compiling assertion on the contract surface, a full test when the AC supports one.**

This maps onto the repo’s own split: the **contract-level** assertion (status / shape — durable) is written now as the red stub; the **construction-level** detail (exact values, edge cases — revisable) is built out in the loop. The progression extends the existing **red → green → refactor**: **red stub in PLAN → green in EXECUTE → complete the stub’s deferred assertions and edge cases → refactor with the tests as the safety net.** Building the test out is its own step *ahead of* the code refactor — not the refactor itself, which holds the tests fixed (`work-loop` SKILL.md, EXECUTE: “Refactor with the test as your safety net”). That is *progressive test construction*, deliberately — the novelty is only that the red test is compilable and *validated at PLAN* (so a vague AC is caught mechanically before EXECUTE), not a new ceremony. It is also *not* the “two test-design touch-points” problem this RFC holds against a separate skill (Option B): that is two *tools* with a handoff and two owners; this is **one owner — the loop — progressing across its own phases**, exactly as red-green-refactor already does.

### Decision 2 — vehicle: a progressive-disclosure reference

`work-loop/references/tdd-stubs.md` holds the procedure; SKILL.md holds a one-line pointer (“load it on demand”), exactly as it does today for `references/supervisor-mode.md` and `references/state-schema.md`, and as `new-spec` does for `references/contract-types.md`. The reference documents:

1. **Parse** — read TDD-mode ACs (spec Testing Strategy), per-task `Tests:` prose (plan), and the `Contract:` file if the spec names one.
2. **Resolve stack** — detect framework / assertion lib / test-path convention from config files and manifests (`jest`/`vitest`/`pytest`/`pyproject`/surefire/`*_test.go`); elicit when ambiguous or greenfield, the way `new-spec` step 4c elicits the implementation stack.
3. **Generate** — one stub per task (default; see Open question 1), one test function per AC, named from the criterion, importing contract types (or placeholders). Write **as much of the real failing test as the AC + contract honestly determine**: a *full* red assertion where the AC pins exact behaviour (classic TDD red — preferred), a *shape* assertion (status code, response-body shape, with a placeholder only for values the implementation will fix) where it doesn’t. Never less than a compiling assertion on the contract surface; never a bare `TODO`. Mark anything left to fill with a stub marker (exact form is Open question 2).
4. **Validate** — one language-appropriate syntax/compile pass (`tsc --noEmit`, `python -m py_compile`, `javac`, `go build`); one correction pass; degrade to “draft (uncompiled), reason noted” on failure rather than blocking.
5. **Record** — write stubs into the plan’s per-task `Tests:` subsections; flag each stubbed task with the marker/field from Open question 2; roll the covered/uncovered/goal-based tally into the spec’s Testing Strategy. No separate file.

This keeps SKILL.md lean (the failure mode Option E below) while giving the procedure room to be genuinely useful.

### Decision 3 — primary home `work-loop`, `new-spec` feeds it

PLAN is the right generation site: the stack is resolved there (or in `new-spec` step 4c), the `Contract:` is authored by then (`new-spec` step 4b), and the plan’s `Tests:` subsections are the stubs’ natural home. `new-spec` gains a **pointer only** — its step 4 already promises “every user-visible outcome … precise enough that a test could be derived from it”; the reference is the mechanical self-check of that promise, so an author can sanity-check stubbability while Testing Strategy is being written, without generating committed stubs before the stack/contract exist.

### Decision 4 — no new gate, no new artifact

Generation is a PLAN step, not a new gate: it rides the *existing* `loop-cohort approve-plan` flow and the pre-EXECUTE adversarial review the loop already runs. A non-compiling stub does **not** block — per the graceful-degrade rule (Decision 2 step 4; Risk 3) it lands as `draft (uncompiled), reason noted` in its `Tests:` subsection, where the human and the adversarial reviewer see it as a signal the AC may be under-specified and decide whether the plan is ready. (`approve-plan` only flips the plan-review status; it runs no compiler — the compile check is the reference's step-4 validate, and the surfaced result is what the gate's human judgement reads.) The coverage signal is the set of `Tests:` subsections plus a one-line tally in Testing Strategy; a separate `coverage-matrix.md` table would collapse into those.

### Decision 5 — substance kept

Assertion-shaped (not `TODO`) stubs, stack-detected output, single-pass generation with one bounded correction pass and graceful degrade, and the explicit “complements `quality-engineer`, different timing/inputs” boundary all hold regardless of vehicle — they are properties of the *output*, independent of whether a skill or a reference produces it.

### Decision 6 — full-mode, TDD-tasks-only

Light mode (RFC-0025) writes a lean inline spec and skips the `loop-cohort` machinery; it does not run stub generation. In full mode, stubs are generated only for tasks whose verification mode is TDD — goal-based and manual-QA tasks note “no stub (mode)” in their `Tests:` subsection.

### Migration

Lockstep doc edits, no code: add `work-loop/references/tdd-stubs.md`; add the pointer sentence to `work-loop` SKILL.md PLAN *“Design tests up front”* and a stub-aware sentence to the EXECUTE TDD red step; add the pointer to `new-spec` SKILL.md Testing Strategy step; note the stub→EXECUTE convention in `CONVENTIONS.md` § 4; note the timing distinction in `quality-engineer`’s test-author mode. No `state.json` fields, no `loop-cohort.py`/`lint-spec-status.py` changes.

## Options considered

Axis: **where the spec→stub capability lives × how much new surface it adds** — from no validation, through reusing an existing agent, to a separate skill+gate+artifact, to an in-loop reference, to inlining into SKILL.md. This exhausts the space: do nothing; reuse an existing reviewer; build a parallel skill; enhance the loop via a *separate file*; enhance the loop via *inline prose*; or push it entirely into `new-spec` alone.

| # | Option | Where it lives | New surface | Trade-off vs goals |
|---|--------|----------------|-------------|--------------------|
| A | **Do-nothing** | — | — | Zero cost. The temporal gap persists: vague ACs surface mid-EXECUTE, spec rewrites cost the most there. |
| B | **Separate `generate-test-stubs` skill** | new skill between `new-spec` and `work-loop` | new skill + `coverage-matrix.md` + handoff convention + second gate | Closes the gap, but two owners for test design, a second gate against RFC-0025’s grain, and a new artifact format. The capability sits *beside* the loop, not *in* it. |
| C | **`quality-engineer` test-author mode, run pre-impl** | existing agent, new timing | none (reuse) | Conflates a post-impl review persona with pre-impl spec validation; QE’s “do not auto-edit / surface only” policy means stubs never land in `plan.md`. No native EXECUTE handoff. |
| D ⭐ | **Progressive-disclosure reference inside `work-loop` TDD mode** | `work-loop/references/tdd-stubs.md` + pointers | one reference file + pointer sentences | One owner (the loop’s existing “design tests up front” step), no new gate, no new artifact, SKILL.md stays lean. Cost: a reference can drift from SKILL.md; generation now runs on every full-mode TDD spec. |
| E | **Inline the procedure into `work-loop` SKILL.md** | SKILL.md body | net-new SKILL.md prose | Same logic as D but bloats an already-long SKILL.md and breaks the repo’s own progressive-disclosure convention — the reason `references/` exists. |
| F | **Generate stubs in `new-spec` only** | `new-spec` SKILL.md | stub step at spec time | Too early: stack and `Contract:` may be unsettled (`new-spec` steps 4b/4c run *after* the spec body), and it isn’t “the core loop we engineer.” |

D and B are the genuine fork in the road: both produce compilable stubs; B adds a parallel skill + gate + artifact, D folds the capability into the step the loop already owns. **Grounding:** A is the standing state. B is the separate-skill shape — a standalone generator that then validates its own output — which this proposal simplifies by dropping any regenerate-retry loop. C reuses `quality-engineer` at a new timing. **D is grounded in this repo’s own progressive-disclosure convention** — `references/supervisor-mode.md` (loaded on demand from EXECUTE), `references/state-schema.md`, and `new-spec/references/contract-types.md`. E is the anti-pattern that convention exists to prevent. F front-loads to a phase that lacks the inputs.

## Risks & what would make this wrong

**Pre-mortem — assume this shipped and failed:**

1. **Stubs too shallow to prove anything.** `test_ac_1() { TODO }` is a coverage report wearing a test-file costume. *Mitigation:* the reference mandates deriving assertion *shape* from the AC — “returns 201 with the created order ID” → assert on status and body shape, placeholder value only.
2. **The reference drifts from SKILL.md.** A reference file is a second place the TDD story lives; if SKILL.md’s red-step wording and `tdd-stubs.md` disagree, the loop does one thing and documents another. *Mitigation:* SKILL.md holds *only* the pointer and the one-sentence intent; all procedure lives in the reference (single source), the same split that keeps `supervisor-mode.md` from drifting today.
3. **Stack detection fails → un-compilable stubs.** An unusual test setup breaks the compile check. *Mitigation:* degrade gracefully — emit stubs as “draft (uncompiled)” with the reason in the `Tests:` subsection; the coverage/testability signal survives even when compilation doesn’t.
4. **It runs on every full-mode TDD spec and becomes ceremony.** Unlike an opt-in separate skill, an in-PLAN step always fires. *Mitigation:* it *is* the “design tests up front” step the loop already mandates — we’re making an existing obligation concrete, not adding one; and Decision 6 confines it to full-mode TDD tasks, so light-mode and goal-based work pay nothing.

**Key assumptions (falsifiable):**
- *ACs in our spec format are structured enough to derive a compilable test signature from.* (Falsified if ACs are routinely too abstract for even a human to name a test function — which is itself the signal the spec is under-specified.)
- *`Contract:` files exist by the time PLAN runs.* (Falsified if most specs skip `new-spec` step 4b; then stubs lean on the plan’s LLD component names instead — degraded, not blocked.)
- *EXECUTE implementers start from the stub rather than rewrite it.* (Falsified if stubs are routinely deleted on first contact; the metric is “did it save time vs. from scratch,” not “did it survive unchanged.”)
- *A reference file is the right weight* — falsified if the procedure turns out short enough that a pointer-plus-reference costs more than inlining (then Option E wins).

**Drawbacks (not “none”):**
- **A reference is real net-new prose surface** to maintain across the stacks it names (JS/TS, Python, Java, Go) — a multi-ecosystem commitment, just housed in a reference instead of a skill.
- **Two places to read the TDD story** (SKILL.md pointer + reference). Mitigated by the strict pointer/procedure split, but the seam exists.
- **Generation runs every full-mode TDD spec**, where a separate skill would be opt-in — a deliberate trade: less optionality, but the capability actually sticks (CHARTER principle 4) because the loop owns it.
- **Stale stubs** if the spec changes after PLAN but before EXECUTE. Mitigated by the loop’s existing “spec divergence → update spec in the same PR” rule, which applies symmetrically to stubs.

## Evidence & prior art

**De-risk reasoning.** The riskiest *vehicle* assumption — “a reference file, not a skill, is the right home” — is settled by repo precedent, not a prototype: the loop already delegates heavy procedure to `references/` loaded on demand (`supervisor-mode.md` from EXECUTE; `state-schema.md` from PLAN/termination), and `new-spec` already carries a `references/` file of its own (`contract-types.md`, delegating contract-type mechanics). A reference invoked from a PLAN step is the established pattern, so the vehicle carries no novel risk. The riskiest *capability* assumption — “compilable stubs can be produced before implementation exists” — holds on a structural argument: stubs must *compile*, not *pass*; a test that calls a contract-defined interface compiles without the implementation, and the narrow failure case (no contract, no LLD) is itself the “spec under-specified” signal. A concrete spike (stub an existing `docs/specs/` feature) belongs in the follow-on spec’s research phase.

**Repo precedent (verified by reading the artifacts in this repo):**
- `work-loop` SKILL.md, PLAN *“Design tests up front”*: “write construction tests for **every** task into `plan.md` … before EXECUTE begins. If you can’t write the test, the task is too vague to implement.” — the step this RFC sharpens.
- `work-loop` SKILL.md, EXECUTE TDD-mode: “Write the failing test first (red).” — the consumer of the stub.
- `work-loop` SKILL.md: `references/supervisor-mode.md` “load it on demand”, `references/state-schema.md` — the progressive-disclosure pattern Decision 2 reuses.
- `new-spec` SKILL.md step 4: “Every user-visible outcome named in the Objective must be precise enough that a test could be derived from it”; step 4b (contract), 4c (stack); `references/contract-types.md` — the feeder and the same reference pattern.
- `CONVENTIONS.md` § 4 (“contract vs. construction tests”): “Tests are designed up front, before any implementation.” — the convention this is the logical extreme of (designed *and compiled* up front), and the home of the stub→EXECUTE note.
- `quality-engineer` agent, test-author mode: “draft contract or construction tests … you surface findings or draft tests” (does not auto-edit) — establishes the timing/persona distinction and why C is a poor fit.
- RFC-0025 (Accepted): the light/full boundary Decision 6 rides; the cost-leanness value Decision 4 (no second gate) honours.

**External prior art.** Not surveyed for this proposal. The change is a *vehicle* decision — a reference file versus a standalone skill — and rests entirely on the in-repo precedent above (the loop’s existing `references/` progressive-disclosure pattern and its design-tests-up-front step). The underlying capability — deriving tests from a spec before implementation — is not novel, but this RFC’s claim is only *where it lives*, for which this repo’s conventions are the authority.

## Open questions

1. **One stub file per AC, or grouped per plan task?** Recommended default: **per plan task** — mirrors `plan.md`’s `Tests:` subsections and EXECUTE’s task-by-task rhythm. · owner: eugenelim (assigns at spec authoring) · decide-by: follow-on spec authoring.
2. **Stub marker + plan field so EXECUTE recognizes a pre-written red test?** Recommended default: a `// STUB:`/`# STUB:` comment with the AC number, plus `stub: true` in the task’s `Tests:` subsection. · owner: eugenelim (assigns at spec authoring) · decide-by: follow-on spec authoring.

## Follow-on artifacts

- Spec: `docs/specs/tdd-stub-generation/` — full feature spec + plan (includes the spike: stub an existing spec in this repo).
- Reference: `packs/core/.apm/skills/work-loop/references/tdd-stubs.md` — the procedure.
- `work-loop` SKILL.md edits: pointer in PLAN *“Design tests up front”*; stub-aware sentence in the EXECUTE TDD red step.
- `new-spec` SKILL.md edit: pointer from the Testing Strategy step to the same reference (self-check, no committed stubs).
- Convention update: `docs/CONVENTIONS.md` § 4 — the stub→EXECUTE handoff convention.
- `quality-engineer` agent: note the timing distinction (in-PLAN stub generation vs. post-impl test-author review) in the test-author mode section.
- Deferred: pack-skill enrichment seam for framework-specific stubs — revisit if/when a test-authoring pack skill lands in this repo.
