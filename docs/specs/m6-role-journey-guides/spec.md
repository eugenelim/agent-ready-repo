# Spec: m6-role-journey-guides

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (M6 AC line 529; Amendment #3 P5 Adopt; Amendment #4 line 800)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
changelog. This applies to the spec body only — `plan.md` keeps its own
changelog of how the approach evolved. -->

## Objective

`docs/guides/core/explanation/role-journeys.md` orients each primary persona — PM, engineer, and headless AI agent — to how they use the workspace coordination system at their operating altitude. The guide is Diátaxis explanation-quadrant: it explains the system from each persona's vantage point, names their primary altitude touchpoints, and routes to relevant how-tos and the source journey maps without duplicating them.

A common "First install and orientation" anchor at the top links to the existing tutorial (`your-first-workspace.md`) and the session-start how-to (`orient-at-session-start.md`) so the guide avoids re-narrating onboarding content. Each role section zooms in on the altitude and workflow pattern that matters most for that persona.

The PM section covers the full shaping-room human path across altitudes 0–1: the product strategist's direction-setting (OKR cascade, initiative framing) feeds the product engineer's six-step shaping sequence, which feeds the PM's tracker intake into the brief queue. These three sub-personas converge on the same output (a brief in `[brief_queue]`) and the guide addresses all three in one section. The Engineer section covers altitude 2: session orientation via `workspace-status`, day-to-day work-loop execution (plan → build → verify → review), and the initiative vs. ad-hoc path distinction. The Agent section covers altitude 2 autonomous execution: cold-start orientation, spec pick-up from the work queue, headless execution without human intervention, and the ship signal.

Each section is derived from and links back to the source journey maps in `docs/product/journeys/` as the authoritative living reference. The guide summarises and routes — it does not replace the journey maps.

## Boundaries

### Always do

- Write in present tense, retcon style: describe the system as if it already works this way
- Derive each role section from the named source journey maps; link back to them as authoritative references
- Keep every section at explanation altitude: why the system works this way for this persona, not step-by-step recipe instructions (recipes belong in the how-to quadrant — link, do not duplicate)
- Update `docs/guides/core/README.md` (Explanation section) when the guide is added
- Update `docs/guides/README.md` "By role" table so PM and Engineer rows link to the guide (and Agent, if a row exists or is being added)

### Ask first

- Any scope change that adds a fourth role not named in RFC-0064 M6 AC (e.g. designer, architect) — adding roles widens the AC surface beyond Amendment #4's scope boundary
- Any material update to the PM tracker-intake subsection that goes beyond what is currently described in the `pm-intakes-from-tracker` source journey map
- Any restructuring of the `docs/guides/README.md` "By role" table beyond adding or updating links to the new guide

### Never do

- Add numbered how-to recipe steps inside the explanation guide — the explanation quadrant is understanding-oriented; route to a how-to file instead
- Create a new top-level directory under `docs/guides/` or a new Diátaxis quadrant directory under `docs/guides/core/`
- Duplicate content from the source journey maps — summarise, cite, and link; the guide is an entry point
- Write the swarm/coordinated-agent-pipeline content from `engineer-scales-to-swarm` (status: `shaping`) — that extension is deferred until the journey is shaped
- Include pack-specific first-value content (Level A/B pack profiles); per RFC-0064 Amendment #4 line 800, P5 role guides are scoped by Platform Core journey phases, not pack profiles

## Testing Strategy

Documentation-only spec — no runtime logic. Two verification modes:

- **Goal-based check** for file presence and registration: `ls docs/guides/core/explanation/role-journeys.md` confirms the file exists; `grep -c "role-journeys" docs/guides/core/README.md` returns ≥ 1; `grep -c "role-journeys" docs/guides/README.md` returns ≥ 1
- **Register-integrity guard** (not an implementation-time check — pre-satisfied at authoring): `grep -c "role-journey-agent-swarm-section" workspace.toml` returns ≥ 1; ensures the backlog anchor is present so the in-guide deferred marker resolves
- **Manual QA** for content quality: (a) each section is read cold by a reviewer adopting the named persona (PM, engineer, headless agent) and can answer "how does this persona use the system at their altitude?" without needing to consult the source journey map first; (b) no numbered recipe steps appear in any section; (c) at least two distinct `docs/guides/core/` cross-links appear within the role sections (not the common anchor); (d) each source journey link sits within its own role section, not misplaced in another section; (e) the `docs/specs/README.md` row's Status column matches `spec.md`'s `Status:` header — flip both atomically in the shipping PR

## Acceptance Criteria

- [x] AC1: `docs/guides/core/explanation/role-journeys.md` exists as a single guide file containing four named sections: "First install and orientation" (common anchor), "PM", "Engineer", and "Agent"

- [x] AC2: The common section is ≤ 10 lines of prose and links to both `docs/guides/core/tutorials/your-first-workspace.md` and `docs/guides/core/how-to/orient-at-session-start.md`; it does not reproduce the content of either guide

- [x] AC3: The PM section covers the shaping-room human path across altitudes 0–1 — the section heading or opening sentence names that it spans three sub-personas (strategist, PE, and intake PM). Content covers: direction-setting at altitude 0 (OKR cascade, initiative framing — derived from `product-strategist-sets-direction`), the shaping sequence at altitude 1 (six-step sequence — derived from `product-engineer-shapes-initiative`), and tracker intake into the brief queue (derived from `pm-intakes-from-tracker`); the section links to all three source journey maps

- [x] AC4: The Engineer section covers: session orientation via `workspace-status` (queue state, what is ready, what is blocked), work-loop execution at altitude 2 (plan → build → verify → review), and the initiative-path vs. ad-hoc-path distinction — derived from `engineer-adopts-coordination` and `engineer-runs-work-loop`; the section links to both source journey maps

- [x] AC5: The Agent section covers: cold-start orientation (no human context — agent reads queue and workspace state), autonomous spec pick-up, headless execution, and the ship signal — derived from `agent-executes-spec`; the section links to the source journey map

- [x] AC6: The Agent section explicitly marks the swarm extension as deferred with the text `(deferred: role-journey-agent-swarm-section)` in the guide prose; `workspace.toml [backlog].open` contains the matching `role-journey-agent-swarm-section` entry (pre-populated at spec-authoring time; the AC verifies the in-guide marker is present)

- [x] AC7: `docs/guides/core/README.md` Explanation section contains a bullet for `role-journeys.md` with a one-line description

- [x] AC8: `docs/guides/README.md` "By role" table "Product manager / strategist" row links to `docs/guides/core/explanation/role-journeys.md`; an "AI agent" (or equivalent) row is added if absent and also links to it; the Engineer row links to it as well

- [x] AC9: Every role section (PM, Engineer, Agent) contains at least one link pointing to its source journey map file(s) in `docs/product/journeys/`

- [x] AC10: The PM, Engineer, or Agent role sections (not the common anchor) contain cross-links to at least two existing guides in `docs/guides/core/` (e.g. `explanation/two-room-model.md`, `how-to/capture-work.md`, `how-to/plan-and-execute-non-trivial-work.md`)

- [x] AC11: `docs/specs/README.md` contains a table row for `m6-role-journey-guides/` whose Status column matches the spec's current `Status:` field, with RFC-0064 as the constraint

## Assumptions

- Technical: `docs/guides/core/explanation/` is the correct Diátaxis quadrant for an understanding-oriented, role-perspective guide — confirmed by `ls docs/guides/core/explanation/` (7 existing files, all understanding-oriented, none role-persona-shaped; 2026-07-21)
- Technical: No role-specific guide file exists anywhere under `docs/guides/` — confirmed by `ls docs/guides/` (no `roles/` directory; no persona-shaped files in core/ quadrants; 2026-07-21)
- Technical: Source journey maps exist at `docs/product/journeys/` with expected slugs — confirmed: 10 files; PM-relevant: `product-strategist-sets-direction` (planned), `product-engineer-shapes-initiative` (proposed), `pm-intakes-from-tracker` (proposed); Engineer-relevant: `engineer-adopts-coordination` (planned), `engineer-runs-work-loop` (shipped); Agent-relevant: `agent-executes-spec` (shipped) (frontmatter scan; 2026-07-21)
- Process: Constrained by RFC-0064 M6 AC line 529 and Amendment #3 P5 Adopt; Amendment #4 line 800 scopes P5 guides to Platform Core journey phases, not pack profiles — confirmed (`docs/rfc/0064-ini-001-ai-native-ecosystem.md:529,800`; 2026-07-21)
- Process: One combined multi-section guide file (not three separate files, not a new directory) is the correct structure — user confirmation 2026-07-21
- Product: PM and Engineer are the two primary human roles; Agent covers headless AI execution — user confirmation 2026-07-21
- Product: Agent section covers headless execution (agent-executes-spec) now; swarm extension deferred until `engineer-scales-to-swarm` is shaped — user confirmation 2026-07-21
- Product: Common "first install and orientation" links to existing guides; each role section focuses on primary altitude touchpoints — user confirmation 2026-07-21
- Product: This spec is authored now but implemented at P5 terminal phase — by implementation time, M2 (PE shaping skills) and M5 (tracker intake skills) are assumed complete; the guide is written retcon-present for the full shipped system (advisory authoring gate in workspace.toml encodes this expectation; source: workspace.toml P5 comment + user decision to proceed 2026-07-21)
