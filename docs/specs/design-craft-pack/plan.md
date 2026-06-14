# Plan: design-craft-pack (v1)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. When it changes
> substantially, note why in the changelog at the bottom.

## Approach

A pure-markdown, opt-in, user-scope pack — no code in the pack, no infra. This
follow-on ships in **two PRs**:

1. **This spec/plan PR** — authors `docs/specs/design-craft-pack/{spec,plan}.md`
   and registers the spec in `docs/specs/README.md`. No pack files, no ADR, no
   guides, no version bump. This matches the sibling precedents: RFC-0032's
   `architect-design-reviewer` follow-on shipped spec+plan only (commit
   `89824a6`/#316), and RFC-0030's ADR-0019 landed *with* the `product-engineering`
   build (commit `ce8ce45`), not before it.
2. **The build PR** (tasks T1–T8 below) — scaffolds and registers the pack (T1),
   authors the four skills + the shared `quality-floor` checklist (T2–T6), lands
   the pack-scoped agnosticism lint + CI wiring (T7), then the ADR, guides,
   changelog, and full gate sweep (T8).

The skills are parallelizable once the scaffold exists (each lives in its own
directory). **The riskiest part is *restraint*** — keeping every skill
framework-agnostic (zero stack tokens, no values table) and under the `<100`-line
ceiling rather than smuggling in a stack cheat-sheet; RFC-0033's two guardrails,
the `<100`-line gate, and the **agnosticism lint** (T7) are the guard. The pack
touches `core` **not at all**. The testing story is goal-based (linters + file
presence + line counts + the agnosticism grep) plus manual-QA of a worked example
per skill.

## Constraints

- **RFC-0033** (Accepted 2026-06-14) — the proposal; settles audience, the
  four-skill + one-checklist roster, strict agnosticism (Guardrails A/B),
  all-skills-zero-agents, user-scope-default, no `seeds/`, and the no-CONVENTIONS
  pack-scoped lint. v1 = the four skills + the checklist; the `design-reviewer`
  subagent twin is **out** (OQ#2).
- **RFC-0007** (`converters`) — the user-scope refusal rails (no `seeds/`, no
  hooks, no `<adapt:>` markers) and the **automated-grep enforcement pattern** the
  agnosticism lint reuses (`.github/workflows/build-check.yml` converters scrubs).
- **RFC-0004** — install-scope-per-pack; Rail A (a pack with non-empty `seeds/`
  cannot declare `"user" ∈ allowed-scopes`) — *reused, not changed*.
- **RFC-0032** — the reading that the charter's three-reviewer ceiling scopes the
  core code-review lenses, not opt-in design-side review — *reused, not changed*.
- **docs/CHARTER.md** — opt-in pack; habits not infra; no new top-level directory;
  "not a framework that picks your tech stack" (the agnosticism constraint).

## Construction tests

**Integration tests:** none beyond per-task tests (no code in the pack; the
agnosticism lint carries its own self-test in T7).
**Manual verification:** walk one worked example through each of the four skills,
confirming `aesthetic-direction` produces a named-goals doc, `design-system-
foundations` derives a taxonomy without printing a values table, `layout-and-
information-architecture` applies reading-pattern/wayfinding *concepts*, and
`design-critique` produces severity-rated findings applying the `quality-floor`
checklist; record the walk in the build PR.

## Design (LLD)

This is a content/skill pack; there is no code architecture beyond the
agnosticism lint. The only "design" is the file layout, the per-skill method, and
the lint's token set.

### Component / module decomposition
*Traces to: the pack ACs (skills + checklist + scaffold).* `packs/design-craft/`
mirrors `architect`/`research`: `pack.toml`, `.claude-plugin/plugin.json`,
`README.md`, and `.apm/skills/<skill>/SKILL.md` (+ `references/`, + `assets/`
where a template ships). Four peer skills, each standalone (rubrics/cross-refs
duplicated over shared, per the architect-pack autonomy principle). The shared
`quality-floor` checklist lives as a `references/` file under `design-critique`
(applied there; referenced by the authoring skills).

### Data & schema
*Traces to: the aesthetic-direction-template AC.* The only artifact template is
the **aesthetic-direction doc** (named emotional/brand goals + coherence
arbitration), carried as a `aesthetic-direction/assets/` file the skill copies
into the repo at runtime (RFC-0004 Rail A: no `seeds/`). No required field beyond
the named goals (never a gate).

### Behavior & rules
*Traces to: the agnosticism-lint AC.* `tools/lint-design-craft-agnostic.py` walks
`packs/design-craft/**` (markdown only) and fails on any match of a stack-token
set — framework names (React/Vue/Angular/Svelte/Tailwind), CSS surface (`@media`,
`prefers-reduced-motion`, CSS-grid/flex property syntax), animation libraries
(Framer Motion), ARIA-role tokens — plus a **values-table shape** (hex `#rrggbb`,
`NNpx`/`NNms`/`NNrem` literals, named easing curves). The lint excludes the pack's
own `README.md` install snippet only if a token there is unavoidable (prefer none).
It is catalogue-governance under `tools/`, **not** a pack primitive, and is
**not** promoted to a repo-wide convention (a separate RFC if ever).

## Tasks

> **All tasks below are the build PR.** This spec/plan PR ships only this document
> + the spec + the `docs/specs/README.md` index row.

### T1: Pack scaffolds and is registered in the marketplace

**Depends on:** none
**Touches:** packs/design-craft/pack.toml, packs/design-craft/.claude-plugin/plugin.json, packs/design-craft/README.md, .claude-plugin/marketplace.json

**Tests:**
- Goal-based: `make lint-packs` and `make validate` pass with the new pack present (AC1).
- Goal-based: `make build` is green and `marketplace.json` lists `design-craft` with name + description + version (AC1).

**Approach:**
- Copy the `pack.toml` / `.claude-plugin/plugin.json` / `README.md` shape from `packs/research/`; set name `design-craft`, version `0.1.0`, `default-scope = "user"`, `allowed-scopes = ["user","repo"]`, `[pack.adapter-contract] version = "0.12"`, `allowed-adapters` = the seven shipped adapters (claude-code, codex, copilot, kiro-ide, kiro-cli, cursor, gemini), `[pack.links] documentation` → `docs/guides/design-craft/`, a `[[pack.maintainers]]` entry.
- Add the `design-craft` entry to `.claude-plugin/marketplace.json` (alphabetical with the others).
- README: what the pack is, the four skills + the `quality-floor` checklist, install snippet, "what's NOT in this pack" (no stack specifics, no values tables, no `seeds/`, no subagent — the OQ#2 twin is a later RFC).

**Done when:** `lint-packs`, `validate`, `build` green; `marketplace.json` lists the pack.

### T2: `aesthetic-direction` skill + its doc template ship

**Depends on:** T1
**Touches:** packs/design-craft/.apm/skills/aesthetic-direction/**

**Tests:**
- Goal-based: `tools/lint-skill-spec.py` passes; `SKILL.md` `<100` lines (AC2).
- Manual QA: interrogating a vague "vibe" yields named emotional/brand goals + a written aesthetic-direction doc, and a conflict triggers coherence arbitration (AC2).
- Goal-based: the doc template ships under `aesthetic-direction/assets/` and a grep confirms the pack ships **no `seeds/`** directory (AC7).

**Approach:**
- `SKILL.md`: when-to-invoke; the interrogation sequence (vibe → named goals); the aesthetic-direction doc shape; coherence arbitration (which goal wins, why); hand off to `design-system-foundations`.
- `references/`: `interrogation-sequence.md`, `coherence-arbitration.md`.
- `assets/aesthetic-direction-template.md`: named-goals doc the skill copies into the repo at runtime (no `seeds/`). Method only — no palette/font.

**Done when:** `lint-skill-spec` green, `SKILL.md` `<100` lines, manual-QA walk recorded.

### T3: `design-system-foundations` skill ships

**Depends on:** T1
**Touches:** packs/design-craft/.apm/skills/design-system-foundations/**

**Tests:**
- Goal-based: `lint-skill-spec` passes; `SKILL.md` `<100` lines (AC3).
- Goal-based: the agnosticism lint (T7) finds **no values table** in this skill — the highest-risk skill for Guardrail A (AC3, AC8).
- Manual QA: deriving a taxonomy from a sample intent yields semantic-over-literal names + ratio-as-concept scales, pointing to WCAG / W3C Design Tokens, with no values reprinted (AC3).

**Approach:**
- `SKILL.md`: the derivation method (semantic-over-literal naming, ratio-as-concept, accessibility-as-floor, contrast budgets, purpose-before-token, atomic composition); point to WCAG (contrast floor) + the W3C Design Tokens interchange shape; **never reprint a values table** (Guardrail A).
- `references/`: `token-taxonomy-derivation.md`, `atomic-composition.md`.

**Done when:** `lint-skill-spec` green, `<100` lines, agnosticism lint clean, manual-QA walk recorded.

### T4: `layout-and-information-architecture` skill ships

**Depends on:** T1
**Touches:** packs/design-craft/.apm/skills/layout-and-information-architecture/**

**Tests:**
- Goal-based: `lint-skill-spec` passes; `SKILL.md` `<100` lines (AC4).
- Goal-based: the agnosticism lint finds **no ARIA roles / CSS grid** — Guardrail B (AC4, AC8).
- Manual QA: structuring a sample screen applies hierarchy, F/Z reading patterns, progressive disclosure, and wayfinding *as concepts* (AC4).

**Approach:**
- `SKILL.md`: hierarchy, depth-vs-breadth, reading patterns (F/Z), progressive disclosure, platform-neutral wayfinding/orientation as concepts (Guardrail B); no layout code.
- `references/`: `reading-patterns.md`, `wayfinding-concepts.md`.

**Done when:** `lint-skill-spec` green, `<100` lines, agnosticism lint clean, manual-QA walk recorded.

### T5: The shared `quality-floor` checklist ships

**Depends on:** T1
**Touches:** packs/design-craft/.apm/skills/design-critique/references/quality-floor.md

**Tests:**
- Goal-based: the checklist file exists at its path and carries the three RFC-0033 lines (all-states, accessibility floor, reduced-motion principle) (AC6).
- Goal-based: the agnosticism lint finds **no `@media`/`prefers-reduced-motion` snippet** — the motion line is the principle, not the query (AC6, AC8).

**Approach:**
- Author `quality-floor.md`: handle-all-states (empty/loading/error/success/partial/disabled); accessibility floor (point to the recognized standard, no ratios reprinted); "motion communicates state, honor reduced-motion" as the principle.
- It lives under `design-critique/references/` (applied there); the authoring skills (T2–T4) cross-reference it.

**Done when:** checklist present with the three lines; agnosticism lint clean.

### T6: `design-critique` skill ships

**Depends on:** T5
**Touches:** packs/design-craft/.apm/skills/design-critique/** (SKILL.md, references/heuristics.md, references/quality-floor.md from T5)

**Tests:**
- Goal-based: `lint-skill-spec` passes; `SKILL.md` `<100` lines (AC5).
- Manual QA: critiquing a sample design produces principle-mapped, severity-rated findings and applies the `quality-floor` checklist; confirm it is a **skill**, not a subagent (AC5).

**Approach:**
- `SKILL.md`: structured heuristic evaluation — review against recognized usability principles, map each issue to the violated principle, assign a severity rating, produce a prioritized findings list with recommendations; apply the `quality-floor` checklist; the design-side `architect-review` (a skill, not the RFC-0032 subagent twin).
- `references/`: `heuristics.md` (the recognized heuristic set + severity scale); `quality-floor.md` (from T5).

**Done when:** `lint-skill-spec` green, `<100` lines, manual-QA walk recorded.

### T7: Agnosticism lint + self-test + CI wiring

**Depends on:** T2, T3, T4, T5, T6
**Touches:** tools/lint-design-craft-agnostic.py, tools/test-lint-design-craft-agnostic.py, .github/workflows/build-check.yml, .github/workflows/build-check-windows.yml

**Tests:**
- Goal-based: `tools/lint-design-craft-agnostic.py` exits 0 on the clean shipped pack and non-zero on a fixture containing a stack token / values-table shape — asserted by `tools/test-lint-design-craft-agnostic.py` (AC8).
- Goal-based: the lint runs in both CI workflows and fails the build on a planted hit (AC8).

**Approach:**
- Write `tools/lint-design-craft-agnostic.py` (Python, `sys.executable`-invokable, Windows-safe) walking `packs/design-craft/**` markdown for the stack-token set + values-table shape from Design §Behavior & rules; exit non-zero with a clear `::error::` on any hit, distinguishing no-match from tool error (mirror the converters scrub's exit-code discipline).
- Add a self-test `tools/test-lint-design-craft-agnostic.py` (the loop-cohort/credbroker consumer-test precedent) with a clean fixture and a dirty fixture.
- Wire the lint into `build-check.yml` and `build-check-windows.yml` as a named step (the converters scrub precedent); invoke via `sys.executable`, never `["bash", ...]` (memory: bash-from-pre-pr breaks Windows CI).

**Done when:** lint + self-test green locally and in both CI workflows; planted hit fails.

### T8: ADR, guides, changelog, spec status, and full gate sweep

**Depends on:** T1-T7
**Touches:** docs/adr/00NN-design-craft-upstream-intent-and-agnosticism.md, docs/adr/README.md, docs/guides/design-craft/**, docs/product/changelog.md, docs/specs/README.md, docs/specs/design-craft-pack/spec.md

**Tests:**
- Goal-based: the ADR exists, is registered in `docs/adr/README.md`, and records the scope decision + the strict-agnosticism guardrails (AC10).
- Goal-based: guide files exist at their `docs/guides/design-craft/{explanation|how-to|reference}` paths (AC9); manual-QA accuracy recorded in the PR.
- Goal-based: `docs/product/changelog.md` carries an `[Unreleased]` entry naming the new pack (AC11).
- Goal-based: `make lint-packs`, `make validate`, `make build`, `tools/lint-skill-spec.py`, the agnosticism lint, and the package `pytest` suite are all green; every shipped `SKILL.md` `<100` lines; a grep proves the diff adds nothing under `packs/core/` and no pack file makes `core` depend on `design-craft` (AC11).
- Goal-based (structural Never): a grep of the pack tree confirms **no `hooks/`, no `agents/`, no `*.py` validator in the pack, no `seeds/`**, and that the only new top-level paths the diff adds are `packs/design-craft/`, `docs/guides/design-craft/`, and the two `tools/` lint files (AC11).

**Approach:**
- Author the ADR via `new-adr` (the design-intent scope decision + Guardrails A/B as the durable record); register it in `docs/adr/README.md`.
- Author guides via `new-guide` under `docs/guides/design-craft/`: an explanation (the design-craft loop + why portable discipline), how-to(s) (per skill or grouped), a reference (the four skills + the `quality-floor` checklist).
- Add a `docs/product/changelog.md` `[Unreleased]` entry for the new pack.
- Flip the spec `Status:` to Shipped with the date and check off every AC (memory: set-final-status-in-the-implementing-PR).
- Run the full local gate sweep; fix any findings.

**Done when:** ADR + guides + changelog present; spec Shipped with ACs checked; all gates green; `core` untouched (grep-clean).

## Rollout

- **Delivery:** additive, opt-in, user-scope pack across two PRs (spec/plan, then
  build). No flag, no migration, fully reversible (delete the pack dir, the
  marketplace entry, the two `tools/` lint files, the guides, and the ADR).
  Nothing irreversible. As a user-scope-default pack, `design-craft` aggregates
  into `marketplace.json` but is **not** projected into this repo's working tree,
  so `build-self` is not required (memory `project_self_host_pack_scope`); the
  gate is `lint-packs` + `validate` + `build` + `pytest` + the agnosticism lint.
- **Infrastructure:** none.
- **External-system integration:** none (skills *point to* WCAG / W3C Design
  Tokens as standards; no live fetch, no API).
- **Deployment sequencing:** this spec/plan PR first (T1–T8 reference it); the
  build PR second. Within the build PR, T1 → skills (T2–T6) → lint (T7) → ADR/
  guides/sweep (T8), per the task DAG.

## Risks

- **Agnosticism leak** — the standing temptation is a values cheat-sheet or a
  CSS/ARIA snippet; `design-system-foundations` (T3) and the `quality-floor`
  motion line (T5) carry the only real risk. Mitigated by Guardrails A/B, the
  agnosticism lint + self-test (T7), and adversarial review.
- **Scope creep into infra** — adding a validator/hook/engine *to the pack* or the
  `design-reviewer` subagent; the Boundaries `Never do` + the `<100`-line gate are
  the guard, and the subagent is explicitly RFC-0033 OQ#2 (a later RFC).
- **`SKILL.md` over the line ceiling** — mitigated by pushing depth into
  `references/` from the first draft (T2–T6).
- **Guide drift** — guides authored before skills stabilize go stale; T8 depends
  on T2–T6 to avoid it.
- **CI grep portability** — a bash-invoked lint silently fails on Windows CI;
  mitigated by Python + `sys.executable` and wiring into both workflows (T7;
  memory `feedback_lint_bash_to_py_windows_trap`).

## Changelog

- 2026-06-14: initial plan. Follow-on to Accepted RFC-0033. Split into a
  spec/plan PR (this document) and a build PR (T1–T8), with the ADR deferred to
  the build PR per the RFC-0030 / RFC-0032 precedent (ADR ships with the build).
