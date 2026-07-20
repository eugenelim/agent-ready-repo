# Plan: spec-B-pack-status-skills

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure SKILL.md authoring plus two manifest updates and one config-comment addition. No compiled code. The shape: read the existing skills in each pack to understand their SKILL.md structure, then author two new SKILL.md files following the same conventions. The riskiest task is `experience-status`'s steel-thread check logic (AC9) — it depends on all three writing skills' frontmatter conventions being verified before the skill body claims to read them.

The three-task ordering: `desk-research-project-status` (T1, independent), `experience-status` (T2, reads verified frontmatter conventions), then the workspace-status routing + config update (T3, requires T2 to exist). All three can be included in one PR; T3 explicitly depends on T2.

## Constraints

- RFC-0067 §Change B: both skills are strictly read-only; `experience-status` uses the `agentbundle-layout.toml` config chain, no elicitation fallback.
- ADR-0054: `status` verb = read-only orient; no state advancement.
- CONVENTIONS §Pack source-of-truth split: SKILL.md files live under `packs/<pack>/.apm/skills/<name>/`; `make build-self` regenerates projected paths.
- Implementation sequencing: B3 (`design` type routing) must land in the same PR as B2 (`experience-status`) so the routing entry is valid on merge.

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.

**Manual QA (cross-cutting, runs at T4):** after `make build-self`, confirm both skills appear at their projected paths and are absent if the pack is not installed.

**Build gate (cross-cutting, runs at T4):** `make build-check` exits 0.

## Tasks

### T1: Author `desk-research-project-status` SKILL.md

**Depends on:** none
**Touches:** packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md, packs/desk-research/pack.toml

**Tests:**
- Goal-based (AC1): file exists at `packs/desk-research/.apm/skills/desk-research-project-status/SKILL.md`; `name: desk-research-project-status`.
- Goal-based (AC2): SKILL.md body reads `[research] output_dir` from the config chain; no-project branch surfaces the RFC-specified message; no phase-advancement logic present.
- Goal-based (AC3): SKILL.md body surfaces phase, working_hypothesis, stop-signal verdict, and next-step recommendation.
- Goal-based (AC4): `description:` field includes the required trigger phrases.
- Goal-based (AC5): `packs/desk-research/pack.toml` `[pack.evals].skills` array includes `desk-research-project-status`.

**Approach:**
- Read `packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md` to confirm the `overview.md` format (phase, working_hypothesis, stop_signal fields).
- Read an existing `*-status` skill (`packs/governance-extras/.apm/skills/rfc-status/SKILL.md`) for structural reference.
- Author `desk-research-project-status/SKILL.md`:
  - `name: desk-research-project-status`
  - `description:` with all AC4 trigger phrases
  - Body: (1) read config chain for `[research] output_dir`; (2) check for `overview.md`; (3) no-project branch → RFC-specified message; (4) project-found branch → surface phase/working_hypothesis/stop-signal/next-step per AC3.
- Add `desk-research-project-status` to `packs/desk-research/pack.toml` `[pack.evals].skills` array.

**Done when:** AC1–AC5 hold.

---

### T2: Author `experience-status` SKILL.md

**Depends on:** none
**Touches:** packs/experience-design/.apm/skills/experience-status/SKILL.md, packs/experience-design/pack.toml

**Tests:**
- Goal-based (AC6): file exists; `name: experience-status`.
- Goal-based (AC7): SKILL.md resolves `[design] output_dir` read-only; not-configured branch surfaces the RFC-specified message; no elicitation present.
- Goal-based (AC8): SKILL.md reads frontmatter from journeys/*.md, screens/*-flow.md, blueprints/*.md.
- Goal-based (AC9): steel-thread check logic present — journey-map → screen-flow → per-screen briefs coverage.
- Goal-based (AC10): no-artifacts branch surfaces the journey-mapping pointer.
- Goal-based (AC11): `description:` includes all AC11 trigger phrases.
- Goal-based (AC12): `[pack.evals].skills` updated.

**Approach:**
- Read `packs/experience-design/.apm/skills/journey-mapping/SKILL.md`, `user-flow/SKILL.md`, `service-blueprint/SKILL.md` to confirm the `type:` frontmatter field values (customer-journey, screen-flow, service-blueprint) — these are the oracle for AC8.
- Author `experience-status/SKILL.md`:
  - `name: experience-status`
  - `description:` with all AC11 trigger phrases
  - Body: (1) resolve `[design] output_dir` from config chain (no elicitation); (2) not-configured branch → RFC-specified message; (3) found branch → read frontmatter from journeys/screens/blueprints paths; (4) steel-thread check (journey → flow → briefs coverage); (5) no-artifacts branch → journey-mapping pointer.
- Add `experience-status` to `packs/experience-design/pack.toml` `[pack.evals].skills` array.

**Done when:** AC6–AC12 hold.

---

### T3: Update workspace-status routing + workspace.toml schema

**Depends on:** T2
**Touches:** packs/core/.apm/skills/workspace-status/SKILL.md (or check-workspace if Spec A not yet merged), packs/core/seeds/ (workspace.toml seed comment), docs/product/workspace-toml-deps.md

**Tests:**
- Goal-based (AC13): `workspace-status` routing table contains an entry for `{type = "design"}` → `experience-status` (fallback `journey-mapping`).
- Goal-based (AC14): workspace.toml seed comment documents `design` as a valid `shaping_queue` type.
- Goal-based (AC15): `docs/product/workspace-toml-deps.md` updated to list `design` type.

**Approach:**
- Locate the routing table in `workspace-status` SKILL.md (or `check-workspace` if Spec A is not yet merged; note the dependency).
- Add `design` entry to the routing table: `{type = "design"}` → `experience-status`; if experience-design pack not installed: `journey-mapping`.
- Update the workspace.toml seed comment to document `design` alongside the existing type enum.
- Update `docs/product/workspace-toml-deps.md`.

**Done when:** AC13–AC15 hold.

---

### T4: Build-self + manual QA + gates

**Depends on:** T1, T2, T3

**Tests:**
- Goal-based (AC16): `make build-self` exits 0; both skills appear at projected paths; `make build-check` exits 0.
- Manual QA: projected `.claude/skills/desk-research-project-status/` and `.claude/skills/experience-status/` (or adapter-equivalent) exist after build-self.

**Approach:**
- Run `make build-self` (with `FORCE=1` if needed).
- Confirm both skills appear at projected paths; confirm `make build-check` exits 0.
- Run `scripts/lint-spec-status.py`; confirm `git status` clean.
- Run adversarial review; address any Blockers.

**Done when:** AC16 holds; adversarial-reviewer returns `Clean — ready to commit.`

## Design (LLD)

### Behavior & rules

**`desk-research-project-status` resolution chain:**
1. Read `[research] output_dir` from `agentbundle-layout.toml` (repo-root first, then user-profile).
2. If no `output_dir` or no `<output_dir>/overview.md`: surface no-project message (AC2).
3. If `overview.md` exists: parse `phase:`, `working_hypothesis:`, `stop_signal:` fields and surface them per AC3.
4. Compute next-step recommendation based on current phase: capture → "run `desk-research-project-digest`", digest → "run `desk-research-project-synthesize`", synthesize → "run `desk-research-project-feedback`", feedback → "project complete."

**`experience-status` resolution chain:**
1. Read `[design] output_dir` from `agentbundle-layout.toml` (repo-root first, then user-profile).
2. If no `output_dir`: surface not-configured message (AC7).
3. Glob `<output_dir>/journeys/*.md`, `<output_dir>/screens/*-flow.md`, `<output_dir>/screens/<slug>/*.md` (matching `- **Type:** screen-brief` bold-body marker), `<output_dir>/blueprints/*.md`.
4. Read `type:` frontmatter from screen-flow files; match `- **Type:** screen-brief` marker from screen-brief files.
5. If no files at all: surface no-artifacts message (AC10).
6. Steel-thread check (AC9):
   - Journey map exists? (any file with `type: customer-journey`)
   - Screen flow exists? (any file with `type: screen-flow`)
   - Per-screen brief files exist? (any `screens/<slug>/*.md` with `- **Type:** screen-brief` marker)
   - Journey stage action → screen-brief coverage: report as "manual check required" (deep cross-reference; not resolvable from markers alone)
7. Report what exists, what's missing, next skill to run.

## Rollout

Pure source edits + build-self regeneration. No external-system dependency. B2 and B3 land in the same PR (spec Assumption, RFC-0067 §Drawbacks); B1 can ship independently or in the same PR. The `design` type is additive and backwards-compatible with existing `workspace.toml` files.

## Risks

- The steel-thread check in `experience-status` (AC9) may not be fully automatable if journey-stage action cross-referencing requires deep parsing. Mitigation: the spec deliberately phrases AC9 as "reports gaps" — the skill surfaces what it can check and notes what requires manual verification; it does not fail silently.
- `desk-research-project-status` phase labels (capture/digest/synthesize/feedback) must match the phases documented in `desk-research-project-start`. Mitigation: T1 approach step 1 reads the source SKILL.md before authoring.

## Changelog

- 2026-07-20: initial plan, authored alongside the spec for RFC-0067 spec/plan/ADR follow-on work.
