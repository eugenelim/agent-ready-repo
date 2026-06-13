# Plan: product-engineering-pack (v1)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. When it changes
> substantially, note why in the changelog at the bottom.

## Approach

A pure-markdown, opt-in pack — no code, no infra. Scaffold the pack and register
it (T1), ship the `intent` seed + a worked example (T2), then author the three
skills (T3–T5), each a `<100`-line `SKILL.md` with depth in `references/`. The
skills are parallelizable once the seed exists (each lives in its own directory).
Guides follow once the skills are stable (T6), then the changelog/index/gate
sweep closes it (T7). **The riskiest part is *restraint*** — keeping it
habits-shaped and under the line ceilings rather than porting `ai-product-kit`'s
mass; the Boundaries and the `<100`-line gate are the guard. v1 touches `core`
**not at all**: an app-scale feature intent *is* an ordinary `core` brief, so
`receive-brief` consumes it unchanged. The testing story is goal-based (linters +
file presence + line counts) plus manual-QA of the worked example.

## Constraints

- **RFC-0030** (Accepted) — the proposal; v1 = app-scale + single-component, BU/
  cross-component deferred to phase 2.
- **ADR-0019** — the `intent` ontology, brief-as-projection, contract-maturity;
  corollary 2 (as refined 2026-06-13): the brief carries no `level:`; `receive-brief`
  is level-agnostic; v1 changes nothing in `core`.
- **ADR-0008 / RFC-0017 / RFC-0018** — the contract seam is *reused at the spec
  stage*, not extended here (no contract machinery in this pack).
- **docs/CHARTER.md** — opt-in pack; habits not infra; 3-reviewer ceiling (no new
  subagent); no new top-level directory.

## Construction tests

**Integration tests:** none beyond per-task tests (no code).
**Manual verification:** walk the shipped worked example end-to-end through
`frame-intent` → `de-risk-intent` → `decompose-intent`, confirming the intake
resolves Scale, the prototype-approach toggles behavior, and decomposition yields
a `core`-shaped brief; record the walk in the PR (AC: skill-behavior manual QA).

## Design (LLD)

This is a content/skill pack; there is no code architecture. The only "design" is
the file layout and the `intent` template schema.

### Component / module decomposition
*Traces to: AC1–AC6.* `packs/product-engineering/` mirrors `architect`/`research`:
`pack.toml`, `.claude-plugin/plugin.json`, `README.md`, `.apm/skills/<skill>/SKILL.md`
(+ `references/`), and the `intent` template under `frame-intent/assets/`
<!-- enriched-pack-manifest (2026-06-13): the template was relocated from a
`seeds/docs/product/intents/` seed to the skill's `assets/` so the pack ships no
seeds and stays user-scope (RFC-0004 Rail A); see T2's Superseded note. -->.
Three peer skills, each standalone
(rubrics/cross-refs duplicated over shared, per the architect-pack autonomy principle).

### Data & schema
*Traces to: AC5.* The `intent` template frontmatter (placeholder-shaped): `level`,
`outcome` (input-metric / lagging-metric / guardrail), `opportunity`, `assumptions[]`,
`prototype_approach` (optional), `children[]` (lower-level intents or spec/slice refs),
optional `parent_intent`. No required field beyond outcome + opportunity (never a gate).

## Tasks

### T1: Pack scaffolds and is registered in the marketplace

**Depends on:** none
**Touches:** packs/product-engineering/pack.toml, packs/product-engineering/.claude-plugin/plugin.json, packs/product-engineering/README.md, .claude-plugin/marketplace.json

**Tests:**
- Goal-based: `make lint-packs` and `make validate` pass with the new pack present (AC1).
- Goal-based: `make build` is green and `marketplace.json` lists `product-engineering` with name + description + version (AC1).

**Approach:**
- Copy the `pack.toml` / `.claude-plugin/plugin.json` / `README.md` shape from `packs/research/`; set name `product-engineering`, version `0.1.0`, user-scope default.
- Add the `product-engineering` entry to `.claude-plugin/marketplace.json` (alphabetical with the others).
- README: what the pack is, the three skills, install snippet, "what's NOT in this pack" (phase-2 BU layer, trackers' live API, contract machinery).

**Done when:** `lint-packs`, `validate`, `build` green; `marketplace.json` lists the pack.

### T2: The `intent` seed template + a worked example ship

> **Superseded 2026-06-13 (enriched-pack-manifest):** the `intent` template was
> relocated from this `seeds/docs/product/intents/_template.md` seed into the
> `frame-intent` skill's `assets/intent-template.md` and de-registered from
> `tools/lint-seeds.py`, so `product-engineering` ships no `seeds/` and stays
> user-scope (RFC-0004 Rail A). `frame-intent` copies the asset into
> `docs/product/intents/<slug>.md` at runtime. The task below records the
> original (seed-based) implementation.

**Depends on:** T1
**Touches:** packs/product-engineering/seeds/docs/product/intents/_template.md, tools/lint-seeds.py, packs/product-engineering/.apm/skills/frame-intent/examples/*

**Tests:**
- Goal-based: `tools/lint-seeds.py` passes — the new seed is registered in `REQUIRED_PLACEHOLDERS` and is placeholder-shaped (no `RFC-NNNN`, no `agent-ready-repo`) (AC5).
- Goal-based: an `examples/` file exists under `frame-intent/`, headed as an example-not-a-schema (AC6).

**Approach:**
- Author `_template.md` with the schema from Design §Data & schema; comments frame each field as a prompt, not a gate. **Register it** in `tools/lint-seeds.py:REQUIRED_PLACEHOLDERS` (the lint fails-loud on unknown seeds — catalogue governance, not pack infra; the `product-brief-intake` brief seed set the precedent).
- Write one app-scale worked example (a feature intent → a `core`-shaped brief), labelled an example, under the skill dir (the `receive-brief` examples precedent).

**Done when:** `lint-seeds` green; template + example present at their paths.

### T3: `frame-intent` skill ships

**Depends on:** T1, T2
**Touches:** packs/product-engineering/.apm/skills/frame-intent/**

**Tests:**
- Goal-based: `tools/lint-skill-spec.py` passes; `SKILL.md` < 100 lines (AC2).
- Manual QA: framing resolves Scale on **two** recorded inputs — one unambiguous (infer→confirm) and one ambiguous (→ ask) — and offers current-state inputs only in brownfield (AC2).

**Approach:**
- `SKILL.md`: when-to-invoke; the intake (resolve Scale, ask greenfield/brownfield); author outcome (input+lagging+guardrail) + opportunity + level; hand to `de-risk-intent`.
- `references/`: `intent-model.md` (the recursive tree), `scale-intake.md` (infer→confirm→ask), `current-state-inputs.md` (JTBD job map default; process/journey map only in brownfield).

**Done when:** `lint-skill-spec` green, `SKILL.md` < 100 lines, manual-QA walk recorded.

### T4: `de-risk-intent` skill ships

**Depends on:** T1, T2
**Touches:** packs/product-engineering/.apm/skills/de-risk-intent/**

**Tests:**
- Goal-based: `lint-skill-spec` passes; `SKILL.md` < 100 lines (AC3).
- Manual QA: the worked example's riskiest assumption gets a predeclared kill condition; toggling `prototype-approach` visibly changes behavior (validator vs driver) (AC3).

**Approach:**
- `SKILL.md`: reversibility triage → riskiest assumption ("what would have to be true") → predeclared kill condition (currency-adaptive) → prototype-approach (defaulted by reversibility, overridable) → survive/kill verdict.
- `references/`: `reversibility-triage.md`, `kill-condition.md`, `prototype-approach.md` (the two paths + per-skill behavior).

**Done when:** `lint-skill-spec` green, `< 100` lines, manual-QA walk recorded.

### T5: `decompose-intent` skill ships

**Depends on:** T1, T2
**Touches:** packs/product-engineering/.apm/skills/decompose-intent/**

**Tests:**
- Goal-based: `lint-skill-spec` passes; `SKILL.md` < 100 lines (AC4).
- Manual QA: decomposing the example yields a `core`-shaped brief at the leaf (app scale), and the projection-profile reference maps it to Linear/Jira-Align one-way (AC4).

**Approach:**
- `SKILL.md`: recursive decomposition (next level down — child intents or, at the leaf, specs/slices); the brief = a feature-intent projected onto a repo (identity at app scale); hand the leaf brief to `receive-brief`/`new-spec`.
- `references/`: `recursive-decomposition.md` (+ brief projection), `tracker-projection.md` (one-way profiles: none / Linear-lean / Jira-Align-deep; live API explicitly out of scope).

**Done when:** `lint-skill-spec` green, `< 100` lines, manual-QA walk recorded.

### T6: Diátaxis guides ship

**Depends on:** T3, T4, T5
**Touches:** docs/guides/explanation/*, docs/guides/how-to/*, docs/guides/reference/*

**Tests:**
- Goal-based: the guide files exist at their Diátaxis quadrant paths (AC8).
- Manual QA: each guide reads accurately against the shipped skills (recorded in the PR) (AC8).

**Approach:**
- Author via `new-guide`: explanation ("the intent tree & level-agnostic shaping"); how-to ("shape a feature in an app repo"); reference (intent fields, modes, projection profiles). The BU/cross-component how-to is a forward-flagged stub (phase 2).

**Done when:** guide files present at Diátaxis paths; accuracy review recorded.

### T7: Changelog, spec index, and full gate sweep

**Depends on:** T1-T6
**Touches:** docs/product/changelog.md, docs/specs/README.md

**Tests:**
- Goal-based: `make lint-packs`, `make validate`, `make build`, `tools/lint-seeds.py`, `tools/lint-skill-spec.py`, and the package `pytest` suite are all green (AC11); a grep proves the diff adds nothing under `packs/core/` (AC7).
- Goal-based (structural Never): a grep of the pack tree confirms **no `hooks/`, no `agents/`, no `*.py` validator**, and that the only new top-level path the diff adds is `packs/product-engineering/` (AC9).
- Goal-based: `docs/product/changelog.md` carries an `[Unreleased]` entry naming the new pack (AC10).
- Goal-based: every shipped `SKILL.md` is `< 100` lines (AC11).

**Approach:**
- Add a `docs/product/changelog.md` `[Unreleased]` entry for the new pack.
- Add `product-engineering-pack` to `docs/specs/README.md` active list (index hygiene per `new-spec` step 7) and flip the spec `Status:` per the work-loop.
- Run the full local gate sweep; fix any lint findings.

**Done when:** all gates green; changelog + spec index updated; `core` untouched (grep-clean).

## Rollout

- **Delivery:** additive, opt-in pack. No flag, no migration, fully reversible (delete the pack dir + the marketplace entry). Nothing irreversible.
- **Infrastructure:** none.
- **External-system integration:** none (tracker projection is documentation/mapping only; no live API).
- **Deployment sequencing:** none beyond the task DAG.

## Risks

- **Scope creep into infra** — the standing temptation is to add a validator/hook/engine; the Boundaries `Never do` + the `<100`-line gate are the guard, enforced in T7.
- **`SKILL.md` over the line ceiling** — mitigated by pushing depth into `references/` from the first draft (T3–T5).
- **Guide drift** — guides authored before skills stabilize go stale; T6 depends on T3–T5 to avoid it.

## Changelog

- 2026-06-13: initial plan. Scope corrected pre-implementation to **pure pack, zero `core` change** (a brief is level-agnostic for its own repo; `level:` dropped, `parent-intent:` deferred to phase 2) per owner direction — removed the former core-brief task.
