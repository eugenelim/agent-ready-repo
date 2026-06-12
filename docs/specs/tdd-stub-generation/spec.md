# Spec: tdd-stub-generation

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** mubeen-acn
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0028
- **Contract:** none — the feature exposes no API surface. The stub↔EXECUTE handoff marker is an in-repo *convention*, not a `contracts/` artifact.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

When an engineer or agent runs `work-loop` in **full mode** on a spec with **TDD-mode acceptance criteria**, the PLAN step's *Design tests up front* should produce **compilable, validated red test stubs** in `plan.md`'s per-task `Tests:` subsections — not merely prose descriptions — so that a vague or untestable acceptance criterion is caught *mechanically at PLAN*, before the expensive EXECUTE phase. The capability ships as a single load-on-demand reference, `work-loop/references/tdd-stubs.md`, pointed to from the existing PLAN step, and surfaced as a testability self-check from `new-spec`'s Testing Strategy step. Success, from the loop-runner's perspective: following the reference turns each TDD-mode AC into a red stub that **compiles in the repo's detected test stack**, asserts the AC's observable contract surface (a full assertion where the AC pins behaviour, a shape assertion otherwise), and is consumed unchanged by EXECUTE's red step; an AC that cannot be stubbed shows up as a testability signal in the plan rather than as a surprise mid-implementation.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit each artifact at its **seed**, never its projection: skills/agents under `packs/core/.apm/…`, conventions under `packs/core/seeds/docs/CONVENTIONS.md`; then run `make build-self` to regenerate projections and `make build-check` to confirm zero drift.
- Keep all shipped reference/skill/convention prose **adopter-generic** — it must read correctly in a downstream adopter's repo, with no catalogue-internal path references (`tools/lint-*`, `make build-self`, `.github/workflows/`, or a *named* internal spec path like `docs/specs/spec-code-ref-lint/`). The generic `docs/specs/<feature>/plan.md` workflow placeholder is allowed and expected (AGENTS.local.md classes it as workflow vocabulary, not a citation).
- Define a stub as **as much of the real failing test as the AC + contract honestly determine** — a full assertion where the AC pins exact behaviour, a contract-surface (shape) assertion otherwise; never less than a compiling assertion, never a bare `TODO` (RFC-0028).

### Ask first

- Any change to `loop-cohort.py`, `lint-spec-status.py`, or `state.json` — RFC-0028 says none is needed; if the implementation appears to require one, stop and surface it.
- Expanding stack coverage beyond the agreed scope (one worked **Python/pytest** example + a generic detection recipe) — e.g. adding full per-language worked examples.
- Renaming/relocating any existing `references/` file, or editing a `work-loop`/`new-spec` SKILL.md section other than the named insertion points (PLAN *Design tests up front*, EXECUTE TDD red step, `new-spec` Testing Strategy step).

### Never do

- **No new skill, no new pre-`work-loop` gate, no new artifact type** — no `generate-test-stubs` skill, no `coverage-matrix.md`. The capability lives inside the existing loop (RFC-0028).
- **No new top-level directory and no new runtime dependency** — the deliverable is Markdown under existing trees.
- Edit a projected/seed-owned path directly (`.claude/`, `.agents/`, `.codex/`, or the live `docs/CONVENTIONS.md`) instead of its seed. (`docs/specs/README.md` and `docs/rfc/README.md` are the exception — they are manual living files, edited directly.)

## Testing Strategy

The deliverable is **documentation / skill content**, not runtime code, so every behaviour is verified by **goal-based checks** (a `grep`/structural assertion or a build/lint one-liner) and **manual review** — there are no TDD-mode tasks, because there is no executable unit to red-green-refactor. (The feature *describes* TDD-stub authoring; it does not itself ship code under test.) The one exception is the de-risk **spike**, verified by **manual QA**: deriving pytest stubs from a *Shipped* spec's ACs, showing they **compile against the contract/AC surface**, and demonstrating **redness against an absent/emptied implementation** that simulates the pre-implementation state. (Every spec in the repo is already implemented, so "red before implementation" can't be observed against live code directly — the honest demonstration is compilability-from-AC plus a red run against an absent symbol; see T1.)

- *Reference exists and is well-formed* (5 phases; Python worked example; generic detection; stub-fullness rule; marker convention) → **goal-based** (`grep`/structural).
- *Adopter-genericity* (no catalogue-internal paths in shipped prose) → **goal-based** (`grep` returns nothing).
- *SKILL.md / CONVENTIONS / agent pointers present at the named insertion points* → **goal-based** (`grep` the seed).
- *Projections regenerate with zero drift* → **goal-based** (`make build-self` then `make build-check` exits clean) — the surface here is the whole projection pipeline, not a single file.
- *Skill files still pass the skill spec* → **goal-based** (`python3 tools/lint-skill-spec.py`).
- *Pre-implementation stubbability is real* → **manual QA**: the spike derives pytest stubs from a Shipped spec's TDD ACs, records they **compile against the contract/AC surface** (RFC-0028's structural claim), and shows them **red against an absent/emptied implementation** simulating pre-implementation — with the Shipped-target caveat recorded.

## Acceptance Criteria

- [ ] `packs/core/.apm/skills/work-loop/references/tdd-stubs.md` exists and documents the five phases — **parse, resolve-stack, generate, validate, record** — and defines a stub as "as much of the real failing test as the AC + contract determine; never less than a compiling assertion on the contract surface; never a bare `TODO`."
- [ ] The reference ships **one fully-worked Python (pytest) stub example** plus a **stack-agnostic detection recipe** for other frameworks, and contains **no** catalogue-internal path reference — `tools/lint-*`, `make build-self`, `.github/workflows/`, or a *named* internal spec path (e.g. `docs/specs/spec-code-ref-lint/`). The generic `docs/specs/<feature>/plan.md` workflow placeholder is allowed and expected.
- [ ] The reference specifies stubs are grouped **one stub file per plan task**, and that each stubbed task carries a `// STUB:`/`# STUB:` + AC-number comment in the test **and** a `stub: true` field in the task's `plan.md` `Tests:` subsection.
- [ ] `work-loop` SKILL.md PLAN *Design tests up front* contains a load-on-demand pointer to `references/tdd-stubs.md`, and the EXECUTE TDD red step notes a pre-written stub may already satisfy the red step.
- [ ] `new-spec` SKILL.md Testing Strategy step points at the same reference for a testability self-check, explicitly *without* committing stubs at spec-authoring time.
- [ ] `CONVENTIONS.md` § 4 (seed) documents the stub→EXECUTE handoff convention, and `quality-engineer` test-author mode notes the in-PLAN-generation vs. post-impl-review timing distinction.
- [ ] Every edit is made to a **seed**; `make build-self` regenerates the projections and `make build-check` reports **zero drift**.
- [ ] `python3 tools/lint-skill-spec.py` passes for the edited skills.
- [ ] A spike note in `notes/` records that stubs derived from a Shipped spec's TDD ACs (target: `spec-code-ref-lint`) **compile against the contract/AC surface** — proving the AC is concrete enough to type a test against (RFC-0028's structural claim) — and are shown **red against an absent/emptied implementation** simulating the pre-implementation state; the note records the Shipped-target caveat and flags any AC that could not be stubbed as the "spec under-specified" signal.
- [ ] No new skill, no `coverage-matrix.md`, no new top-level directory, no new runtime dependency, and no change to `loop-cohort.py` / `lint-spec-status.py` / `state.json`.

## Assumptions

- Technical: skill/agent/reference source-of-truth is `packs/core/.apm/…`, projected verbatim to `.claude/`, `.agents/`, `.codex/` via `make build-self` (source: `diff packs/core/.apm/skills/work-loop/SKILL.md .claude/…` → IDENTICAL; AGENTS.local.md § "Always-projected paths").
- Technical: `docs/CONVENTIONS.md` is seeded from `packs/core/seeds/docs/CONVENTIONS.md`, where § 4 lives (source: `find packs -path "*/seeds/docs/CONVENTIONS.md"`; § 4 grep hit).
- Technical: `docs/rfc/README.md` and `docs/specs/README.md` are living in-repo files; their seeds are empty install templates, so they are edited directly (source: seed contains `<!-- no RFCs yet -->`, zero rows).
- Technical: the deliverable is documentation, verified goal-based + manual; no runtime code (source: RFC-0028 Migration — "Lockstep doc edits, no code").
- Technical: shipped skill/reference prose must avoid catalogue-internal path references (source: AGENTS.local.md:60-64, issue #190 class).
- Technical: post-edit ritual is `make build-self` → `make build-check` → `python3 tools/lint-skill-spec.py`, and the catalogue lints require PyYAML (installed via `tools/requirements.txt`) (source: AGENTS.local.md:173-210).
- Process: Constrained by RFC-0028 (Accepted); convention changes route through an RFC, which RFC-0028 is (source: `docs/rfc/0028-…md`; CONVENTIONS § 3).
- Process: the spec is accepted/owned fork-locally to unblock implementation; `eugenelim` signs off when the branch is PR'd to his repo (source: RFC-0028 Approver; user confirmation 2026-06-12).
- Product: serves agents running full-mode `work-loop` with TDD-mode tasks, and core-pack adopters; the feature ends at red-stub generation + validation in `plan.md` plus the reference that documents it; integration/E2E scaffolding and any separate skill are out (source: RFC-0028 Goals / Non-goals).
- Decisions (user confirmation 2026-06-12): `Shape: service` with a thin LLD; stubs grouped one file **per plan task**; stub marker = `// STUB:` comment + `stub: true` field; reference ships a **Python worked example + generic detection**; spike target is a small Python-lint spec (`spec-code-ref-lint`).
