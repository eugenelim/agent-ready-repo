# Plan: m6-role-journey-guides

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

One file: `docs/guides/core/explanation/role-journeys.md`. Read each source journey map, extract altitude touchpoints for the persona, write Diátaxis explanation-quadrant prose (no recipe steps), and cross-link back to the sources. The work is authoring and cross-linking — no runtime logic, no code, no build-self needed.

Two README updates (`docs/guides/core/README.md` and `docs/guides/README.md`) register the guide. One workspace.toml entry (`role-journey-agent-swarm-section`) records the deferred swarm extension for the Agent section.

The riskiest part is the PM section: it references M2 (shaping sequence) and M5 (tracker intake) capabilities drawn from `proposed` journey maps — authored before those milestones ship. The PM section is written as retcon-present for the full P5 system. See Risks.

## Constraints

- RFC-0064 M6 AC line 529: "Role journey section committed to `docs/guides/`: PM / engineer / agent — how each uses the system at their altitude; derived from `docs/product/journeys/` living maps"
- RFC-0064 Amendment #3 P5 Adopt: terminal phase (the whole journey must be stable first — advisory gate in workspace.toml)
- RFC-0064 Amendment #4 line 800: P5 role guides scoped by Platform Core journey phases, not pack profiles
- Diátaxis: explanation quadrant — understanding-oriented prose; no recipe steps
- Phase-slice doctrine (CONVENTIONS.md §752): guide ships with its spec

## Construction tests

**Integration tests:** none (documentation only)

**Manual verification:**
- Read the guide cold as each persona (PM, engineer, agent): can answer "how do I use this system at my altitude?" without opening the source journey map
- Confirm no numbered recipe steps appear anywhere in the guide
- Confirm all internal links resolve (journey map links, cross-guide links)

## Design (LLD)

### Component / module decomposition

`docs/guides/core/explanation/role-journeys.md` — one file, four sections:

1. **First install and orientation** (≤ 10 lines) — links to `tutorials/your-first-workspace.md` and `how-to/orient-at-session-start.md`; brief mention of the two-room model link; no recipes
2. **PM** — altitude 0 (direction-setting: OKR cascade, initiative framing via `product-strategist-sets-direction`) → altitude 1 (shaping: six-step sequence via `product-engineer-shapes-initiative`; tracker intake via `pm-intakes-from-tracker`); links to all three source journey maps
3. **Engineer** — altitude 2: session orientation via `workspace-status`, work-loop (plan → build → verify → review), initiative vs. ad-hoc path distinction; links to `engineer-adopts-coordination` and `engineer-runs-work-loop`
4. **Agent** — altitude 2 autonomous: cold-start, spec pick-up from `[work]` queue, headless execution, ship signal; deferred swarm marker `(deferred: role-journey-agent-swarm-section)`; links to `agent-executes-spec`

### Behavior & rules

- No new concepts introduced — the guide synthesises and routes to existing journey maps and guides
- Every role section: explanation prose only (paragraphs, not numbered lists); at least one source link to the journey map file(s) it derives from
- Cross-links: at least two links to other existing guides in `docs/guides/core/`

## Tasks

### T1: Scaffold `docs/guides/core/explanation/role-journeys.md` and author the common section

**Depends on:** none

**Tests:**
- `ls docs/guides/core/explanation/role-journeys.md` succeeds (AC1)
- `grep -c "your-first-workspace" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC2)
- `grep -c "orient-at-session-start" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC2)
- Common section has ≤ 10 lines of prose (AC2 — manual count)

**Approach:**
- Create `docs/guides/core/explanation/role-journeys.md` with a top-level heading and four named section headings (First install and orientation, PM, Engineer, Agent)
- Write the common section (≤ 10 lines): link to the tutorial and the orient how-to; one sentence on the two-room-model explanation for context; no recipe steps
- Leave PM, Engineer, Agent sections as labelled stubs

**Done when:** file exists at the correct path; common section links to both required guides and contains no recipe steps

---

### T2: Author PM altitude section

**Depends on:** T1

**Tests:**
- `grep -c "product-strategist-sets-direction" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC3, AC9)
- `grep -c "product-engineer-shapes-initiative" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC3, AC9)
- `grep -c "pm-intakes-from-tracker" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC3, AC9)
- PM section covers altitude 0 direction-setting, altitude 1 shaping, and brief-queue intake (AC3 — manual)
- No numbered recipe steps in PM section (AC — manual)

**Approach:**
- Read `docs/product/journeys/product-strategist-sets-direction.md`, `product-engineer-shapes-initiative.md`, `pm-intakes-from-tracker.md`
- Extract altitude-0 touchpoints (OKR cascade, initiative framing via `frame-situation` and the six-step shaping sequence entry) and altitude-1 touchpoints (the shaping sequence, brief queue, tracker intake)
- Write explanation prose: why these altitude touchpoints matter for a PM; how artifacts flow from direction → shaping → brief queue → specs
- Add source links for all three journey maps

**Done when:** PM section covers direction-setting, shaping sequence, and tracker intake; all three source journey map links are present; no recipe steps

---

### T3: Author Engineer altitude section

**Depends on:** T2

**Tests:**
- `grep -c "workspace-status" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC4)
- `grep -c "engineer-adopts-coordination" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC4, AC9)
- `grep -c "engineer-runs-work-loop" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC4, AC9)
- Initiative vs. ad-hoc distinction is present in the Engineer section (AC4 — manual)
- No numbered recipe steps in Engineer section (AC — manual)

**Approach:**
- Read `docs/product/journeys/engineer-adopts-coordination.md` and `engineer-runs-work-loop.md`
- Extract altitude-2 touchpoints: session orientation via `workspace-status` (queue state, parallel candidates), the work-loop (plan → build → verify → review), and the two-path distinction (initiative path updates workspace.toml; ad-hoc path does not)
- Write explanation prose: why session orientation matters before picking up work; what the work-loop gives an engineer; when to use each path
- Add source links for both journey maps

**Done when:** Engineer section covers workspace orientation, work-loop execution, and initiative/ad-hoc path distinction; both source links present; no recipe steps

---

### T4: Author Agent altitude section (headless now; swarm deferred)

**Depends on:** T3

**Tests:**
- `grep -c "agent-executes-spec" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC5, AC9)
- `grep -c "deferred: role-journey-agent-swarm-section" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC6 — verifies the in-guide marker is present; workspace.toml entry was pre-populated at spec-authoring time)
- Agent section covers cold-start, autonomous spec pick-up, headless execution, and ship signal (AC5 — manual)
- No numbered recipe steps in Agent section (AC — manual)

**Approach:**
- Read `docs/product/journeys/agent-executes-spec.md`
- Extract altitude-2 autonomous touchpoints: cold-start orientation (agent reads `workspace.toml` and queue state with no human hand-off), spec pick-up from `[work].active`, headless plan → build → verify → review loop, ship signal (spec moves to shipped; no human gate in autonomous mode)
- Write explanation prose: why cold-start orientation is different for an agent; what the autonomous execution loop looks like; what triggers the ship signal
- Add deferred marker for swarm extension: `(deferred: role-journey-agent-swarm-section)`
- Add source link to `agent-executes-spec.md`

**Done when:** Agent section covers cold-start, headless execution, and ship signal; deferred marker present; source link present

---

### T5: Register the guide, update READMEs, add backlog entry, update specs README

**Depends on:** T2, T3, T4

**Tests:**
- `grep -c "role-journeys" docs/guides/core/README.md` returns ≥ 1 (AC7)
- `grep -c "role-journeys" docs/guides/README.md` returns ≥ 3 (AC8 — one match per row: "Product manager / strategist", Engineer, and Agent; a single-row link returns 1 and fails)
- `grep -c "deferred: role-journey-agent-swarm-section" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC6 — in-guide marker; pre-populated workspace.toml entry is already verified at spec authoring)
- `grep -c "m6-role-journey-guides" docs/specs/README.md` returns ≥ 1 (AC11)
- `grep -c "capture-work" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC10 first cross-link — role-section only, cannot appear in the common anchor)
- `grep -c "plan-and-execute-non-trivial-work" docs/guides/core/explanation/role-journeys.md` returns ≥ 1 (AC10 second cross-link — confirms the ≥ 2 distinct role-section cross-link requirement)

**Approach:**
- Update `docs/guides/core/README.md` Explanation section: add a bullet for `[Role journeys](explanation/role-journeys.md)` with a one-line description (e.g. "how PMs, engineers, and agents use the system at their altitude")
- Update `docs/guides/README.md` "By role" table: update PM and Engineer rows to link to the new guide; add an Agent row if absent
- Verify cross-links (AC10): the guide should already link to `two-room-model.md` from the common section and other existing guides from the role sections; add any missing cross-links
- Verify `workspace.toml [backlog].open` contains `{slug = "role-journey-agent-swarm-section"}` (pre-populated at spec-authoring time — do not duplicate; confirm presence only)
- Update `docs/specs/README.md`: add table row for `m6-role-journey-guides/` — set the Status column to the spec's current `Status:` field at implementation time (not the literal "Draft" — the spec will be `Implementing` or `Shipped` by the time T5 runs); Constrained by: RFC-0064 M6 AC line 529; confirm by inspection that the README Status value matches `spec.md` line 3; flip both atomically in the same PR

**Done when:** all five grep checks pass

## Rollout

No infra, no flags, no deployment. Pure documentation addition. Rollback: revert the PR.

## Risks

- **PM section implements M2/M5 capabilities — do not author before they ship.** `product-engineer-shapes-initiative` (proposed) and `pm-intakes-from-tracker` (proposed) describe M2 and M5 capabilities not yet shipped at spec-authoring time. The guide is written retcon-present for the full P5 system; the spec's Assumptions record that M2/M5 are assumed complete by implementation time. The advisory authoring gate in workspace.toml encodes this dependency. There is no degraded partial-PM-section option — implement AC3 in full once M2/M5 are shipped.
- **Engineer section also derives from a `planned` source map.** `engineer-adopts-coordination` is `status: planned` at spec-authoring time. The impact is lower than the PM risk (the core `workspace-status` touchpoint is already shipped), but the same "read source map fresh at implementation" mitigation applies.
- **Journey maps may be revised before implementation.** The source journey maps are living documents; if substantially revised between spec authoring and guide implementation, the derivation claims may be stale. Mitigation: implementation reads each source journey map fresh.

## Changelog

- 2026-07-21: initial plan
