# RFC-0064: INI-001 AI-Native Ecosystem — Platform Core

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-18
- **Date closed:** —
- **Decision weight:** heavy
- **Related:**
  - [docs/product/shaping/product-vision-INI-001.md](../product/shaping/product-vision-INI-001.md) — initiative vision and maturity model
  - [docs/product/shaping/ecosystem-overview.md](../product/shaping/ecosystem-overview.md) — six-initiative dependency map
  - **Journey maps** — `docs/product/journeys/` — eight living journey maps covering adoption, all personas, and both shaping and build rooms; see [README](../product/journeys/README.md) for the full index and status lifecycle
    - [team-evaluates-and-adopts.md](../product/journeys/team-evaluates-and-adopts.md) — planned; prerequisite journey covering self-serve and enterprise adoption paths; surfaces live-demo gap and org-level measurement gap as primary pains; feeds M6 (tutorial, rollout playbook, live-demo guide) and Unknown #8 (portfolio pack)
    - [engineer-adopts-coordination.md](../product/journeys/engineer-adopts-coordination.md) — planned; install through session continuity; surfaces `author-brief` gap and brief queue creation problem
    - [engineer-runs-work-loop.md](../product/journeys/engineer-runs-work-loop.md) — planned; core build cycle before and after M1.7 workspace integration; surfaces post-ship state gap as primary pain
    - [agent-executes-spec.md](../product/journeys/agent-executes-spec.md) — planned; headless autonomous execution; surfaces orientation accuracy and exit-state integrity as primary failure modes
    - [engineer-scales-to-swarm.md](../product/journeys/engineer-scales-to-swarm.md) — shaping; adapter setup through exception recovery; surfaces atomic claiming, stale-active, partial-progress, and mixed-concurrency open design questions for INI-003 sub-RFC
    - [product-engineer-shapes-initiative.md](../product/journeys/product-engineer-shapes-initiative.md) — proposed; six-step shaping sequence; surfaces session-bound shaping chain as primary pain; feeds M2 sub-RFC
    - [product-strategist-sets-direction.md](../product/journeys/product-strategist-sets-direction.md) — proposed; altitude-0 artifacts and OKR cascade; surfaces altitude-0 → altitude-1 handoff gap; feeds M4 sub-RFC
    - [pm-intakes-from-tracker.md](../product/journeys/pm-intakes-from-tracker.md) — proposed; tracker-to-brief intake; surfaces duplicate-write friction and tracker-brief drift; feeds M5 sub-RFC

## How to orient at session start

**Until `check-workspace` (M1.5) exists:** read this file + `docs/product/roadmap.md` + `docs/product/shaping/product-vision-INI-001.md` + `docs/product/shaping/ecosystem-overview.md`. Then check `docs/product/briefs/` for any in-progress brief stubs.

**Once `check-workspace` exists (after M1.5 ships):** run `check-workspace` — it reads `workspace.toml` and surfaces the current queue state and next action. This is the single cold-start command from M1.5 onward.

**Once `rfc-status` (M3 AC 3) exists:** run `rfc-status` — it will surface active sub-RFCs and milestone status.

**Queue unlock progression** — M1.5 unlocks visibility of all three queues; full operational wiring arrives in steps:

| Queue | Visible | Fully wired | What wires it |
|---|---|---|---|
| `[work]` | M1.5 | M1.7 | `work-loop` reads queue at step 0; marks spec shipped on complete |
| `[brief_queue]` | M1.5 | M1.8 + `author-brief` | `receive-brief` moves draft → ready; `author-brief` creates briefs from external input |
| `[shaping_queue]` | M1.5 | M2 | New PE skills (`frame-situation`, `map-capabilities`, `place-bet`) write to/from shaping queue; existing skills (`frame-intent`, `de-risk-intent`) work items but do not write back |

Between M1.5 and M1.7: you can see the work queue but `work-loop` does not yet auto-read it at session start. Between M1.5 and M2: shaping queue items can be manually placed and worked with existing PE skills but state is not written back automatically.

**Batch ↔ milestone label crosswalk** (journey files and the queue-unlock table above use the M1.x labels; the AC section uses the Batch labels):

| AC label | Milestone label | Key delivery |
|---|---|---|
| Batch 2 | M1.5 | `check-workspace` ships; all three queues become visible |
| Batch 3 | M1.7 | `work-loop` workspace integration; work queue fully wired |
| Batch 4 | M1.8 | `receive-brief` + `author-brief`; brief queue fully wired |
| Batch 5 | M1.9 | `new-rfc` workspace prompt; governance integration |

M1 is the initial implementation scope. M2–M6 begin sequentially when the prior milestone ships. Sub-RFCs govern net-new design decisions within M2, M4, and M5. Post-acceptance corrections to this RFC's own decisions are recorded as **Errata** per RFC-0055.

## Implementation guide

Each spec is one work-loop round (`new-spec` → plan → build → verify → review). Each milestone contains multiple specs. This section gives the spec dependency graph and recommended order so a cold session can start immediately without re-reading the full design history.

### M1 delivery batches — estimated 2–3 weeks

M1 is organised into five functional delivery batches. Each batch ships as one PR (or two tightly-coupled PRs where noted). No batch leaves dangling work — each is a self-contained, non-breaking improvement. Batches 1 and 2 must ship first in sequence; Batches 3, 4, and 5 can overlap once Batch 2 lands.

**Batch 1 — Foundation docs** (ship first; no code; pure additions)

| Delivers | Notes |
|---|---|
| ADR: D2 (TOML format) + revised D4 (workspace.toml on main, no umbrella branch) | Doc only. Records the decisions before any implementation begins. |
| CONVENTIONS.md §5b: admit `projects/`, `shaping/`, `findings/`, `initiatives/`, `research/` under `docs/product/` | Small amendment. Clears the path for Batch 5 seeds and M3 research output. |

**Batch 2 — Workspace core** ← *unlock batch; ship as one PR*)

| Delivers | Notes |
|---|---|
| `workspace.toml` schema seed committed to `main`, pre-populated with INI-002 queue | New file on main. Non-breaking — nothing reads it yet. |
| `agentbundle-layout.toml [product]` table: configurable `projects/` and `shaping/` paths | Config extension alongside the seed. |
| `check-workspace` skill in core pack | Reads local `workspace.toml`; resolves DAG across all three queues; surfaces ready/blocked/parallel across all active initiatives. Offers to initialise if file absent. |

After this batch merges, **run `check-workspace` at every session start** — it orients in one command from here on.

**Batch 3 — Work queue end-to-end** (after Batch 2; one PR)

| Delivers | Notes |
|---|---|
| `work-loop` workspace integration | Reads `workspace.toml` at step 0 for initiative context; on ship, moves spec `active → shipped` and surfaces `roadmap.md` update reminder. Degrades gracefully if file absent (existing behavior unchanged). |

After this batch: specs are claimed, executed, marked shipped, and the next ready item surfaces — all automatically. The work queue is live end-to-end.

**Batch 4 — Brief queue end-to-end** (after Batch 2; one PR; independent of Batch 3)

| Delivers | Notes |
|---|---|
| Brief template DoR fields: `Status`, `Rabbit holes`, `Instrumentation`, `## Design artifacts` | Grandfathered for existing briefs — new fields optional retroactively; `receive-brief` handles both shapes. |
| `receive-brief` workspace integration | Sets `Status: Ready` after decomposition; writes `workspace.toml` (brief `draft → ready`). Degrades if absent. |
| `author-brief` skill | Takes unstructured external input (email, prose, Linear text); elicits missing DoR fields; creates brief file; writes to `[brief_queue].draft`. |

After this batch: any input source (external email, shaped artifact, tracker copy-paste) becomes a queued brief in one invocation. The brief queue is live end-to-end.

**Batch 5 — Governance integration + shaping home** (safe to ship any time after Batch 1; `new-rfc` queue-write is a no-op until Batch 2 lands — degrades gracefully)

| Delivers | Notes |
|---|---|
| `new-rfc` workspace prompt | Accepted-RFC path prompts "Add implementation specs to `workspace.toml` queue?" Degrades if absent. |
| `docs/product/projects/_template.md` seed | Project index template. Batch 1 CONVENTIONS amendment should land first. |
| Shaping + initiative artifact seeds (`docs/product/shaping/`, `findings/`, `initiatives/`) | Seed files for shaping artifacts. Bundle with the template — same PR. |

**Recommended session order:** Batch 1 → Batch 2 (same or next session) → Batches 3, 4, 5 in any order or concurrently.

### M2 JIT scenario — build the skill, then use it

M2 skills should be built and used in sequence: each skill ships, then is immediately used to produce a shaping artifact or brief that feeds the next spec. This is the JIT build-then-use pattern.

| Step | Build | Then use it to |
|---|---|---|
| M2.1 | `frame-situation` (signal → typed finding → six-step route; embeds Wardley) | Run `frame-situation` on the current INI-002 shaping queue — produce a typed finding that validates the M2 opportunity assessment and updates the shaping queue in `workspace.toml` |
| M2.2 | `identify-opportunities` (JTBD framing: functional / emotional / social jobs) | Run `identify-opportunities` on the PE pack gap — produces an opportunity assessment artifact in `docs/product/shaping/` that shapes the `diverge-solutions` brief |
| M2.3 | `diverge-solutions` (step-3 option generation; resolve overlap with `explore-options`) | Run `diverge-solutions` on the workspace coordination design — generates solution options for M3+ shaping work |
| M2.4 | `place-bet` (human commitment gate; betting table surface) | Run `place-bet` on the validated option from the M2.3 diverge-solutions output — produces a committed bet artifact that anchors the capability map |
| M2.5 | `map-capabilities` (product vision → all capability areas) | Run `map-capabilities` on INI-002 using the M2.4 bet — produces a capability map in `docs/product/shaping/` that becomes the shaping anchor for M3–M6 |
| M2.6 | Initiative brief artifact + `docs/product/initiatives/_template.md` + Lean Canvas | Use the bet from M2.5 to author the INI-002 initiative brief using the new template |
| M2.7 | JTBD framing embedded in `frame-intent` (shipped skill modification — own spec, not bundled with M2.6) | Run `frame-intent` on an existing project after the JTBD extension ships — verify functional / emotional / social job output appears in the frame-intent artifact |

If implementing a skill reveals the RFC's AC was wrong or too narrow, write an **Errata** to RFC-0064 in the same PR per RFC-0055. Do not silently diverge.

### M3–M6 ordering notes

- **M3** covers four groups: findings register seeds, `rfc-status` skill, `research-project-start` bug fix, and two pack renames (`research` → `desk-research`; `experience` → `experience-design`). No sub-RFC. The renames and bug fix are independent and can ship in parallel PRs; seeds and `rfc-status` form one PR.
- **M4** (product-strategy pack full build-out) — RFC-0063 is already open as a draft; M4 begins on RFC-0063 acceptance. No new RFC to open.
- **M5** (tracker integration) similarly opens RFC-00XX · linear-pack. The github-brief-intake skill can ship independently of the linear pack; do it first as a confidence-building spec.
- **M6** (documentation wave) is parallelisable — skills docs, seeds docs, and the Astro site project index are independent. Run three parallel specs if bandwidth allows.

## Reviewer brief

- **Decision:** Establish INI-001 (AI-Native Ecosystem) as the governing initiative, define INI-002 (Platform Core) as this repo's scope, adopt `workspace.toml` as the in-repo coordination artifact, adopt a standard vocabulary (Project / Milestone / Brief / Spec), introduce the shaping queue concept, and authorise a six-milestone implementation roadmap.
- **Recommended outcome:** accept.
- **Immediate change if accepted (M1 — begins on acceptance):**
  - New `workspace.toml` file format and seed in the core pack.
  - New `check-workspace` skill in the core pack.
  - New `[shaping_queue]` section in `workspace.toml` (upstream of the existing `[brief_queue]` concept).
  - Extended brief template: adds `Status`, `Rabbit holes`, `Instrumentation`, and `## Design artifacts` fields.
  - Extended `work-loop`: reads `workspace.toml` at step 0; pops queue and updates brief Coverage post-ship.
  - Extended `receive-brief`: sets `Status: Ready`; optionally writes `workspace.toml`.
  - Extended `new-rfc`: Accepted path prompts to add implementation specs to the queue.
  - New initiative and shaping artifact seeds.
  - `CONVENTIONS.md § 5b` amended for new `docs/product/` subdirectories.
  - ADR authored recording D2 (workspace.toml TOML format) and revised D4 (workspace.toml on main, no umbrella branch, spec branches target main directly).
  - Sub-RFCs govern M2, M4, and M5 implementation (see § Sub-RFCs).
- **Affected surface:** core pack (skills + seeds), governance-extras pack (rfc-status skill), PE pack (new skills), adopter-facing `workspace.toml` convention; M3 pack renames: `research` → `desk-research` and `experience` → `experience-design` (pack manifests, `plugin.json`, `agentbundle-layout.toml`, deprecation aliases, build-self).
- **Stakes:** high — introduces new adopter-facing file format and vocabulary; reversible at pack level (no database, no breaking schema change to existing artifacts).
- **Review focus:** (1) vocabulary choices (Project / Milestone / Brief / Spec) and tracker mapping; (2) `workspace.toml` schema and the three-section split (shaping / brief / work) with typed shaping queue entries; (3) workspace.toml on main as the git coordination pattern (revised D4 — no umbrella branch); (4) scope boundary between INI-002 and sister initiatives.
- **Not in scope:** INI-003 (Coding CLI Adapter Pack), INI-004 (Remote Agent Runtime), INI-005 (Infra & Observability), INI-006 (Control Plane) — separate initiatives, mentioned for ecosystem context only. This RFC ships when M1–M6 in-repo ACs are complete, regardless of whether sister initiatives have started.

## The ask

- **Recommendation (BLUF):** Adopt `workspace.toml` as the in-repo declared-intent coordination artifact, establish the three-queue model (shaping → brief → work), standardise vocabulary, and authorise six milestones of implementation work within INI-002.
- **Why now (SCQA):**
  - *Situation.* The three loops (discovery, work, release) are shipped and proven. Teams can run individual specs end-to-end.
  - *Complication.* There is no coordination layer above the spec. Strategic context lives in session logs that expire. No structured mechanism exists to queue briefs, track initiative scope, or orient an agent at session start without manual file-reading.
  - *Question.* What is the minimal in-repo structure that enables a team to declare intent, queue work, and orient any agent at any session start — without locking into a specific harness or tracker?
- **Decisions requested:**

  | ID | Question | Recommendation | Why | Decide by | Reviewer action |
  |---|---|---|---|---|---|
  | D1 | Standard vocabulary? | **Project / Milestone / Brief / Spec** | Cross-tool consensus; maps cleanly to Linear, Jira, GitHub, Azure DevOps; carries more semantic weight than "Issue" at the brief level | RFC acceptance | Accept or propose alternate term set |
  | D2 | Coordination artifact format? | **`workspace.toml` (TOML)** committed on `main` | Declared intent only; TOML's structured-data strengths (nested sections, typed lists, co-located comments) fit a file agents read programmatically; execution state lives in the platform | RFC acceptance | Accept or propose Markdown+frontmatter |
  | D3 | Three-queue split? | **`[shaping_queue]` + `[brief_queue]` + `[work]`** | Maps to the six-step development sequence: shaping (upstream) → brief (step 5) → spec (step 6); different skills operate on each queue; `[shaping_queue]` handles all upstream work via typed entries (`research`, `strategy`, `shape`, `signal`) so non-technical users (researchers, product strategists) have queue visibility without separate sections | RFC acceptance | Accept or propose separate `[research_queue]` / `[strategy_queue]` sections |
  | D4 | Git coordination pattern? | **`workspace.toml` on `main`** — spec branches target `main` directly; each spec PR updates `workspace.toml` in the same diff; no umbrella branch | Fast-merge, no-long-lived-branch model. Concurrent specs touch different TOML entries; rebase conflicts are trivially resolved. Umbrella branches solve a coordination problem that only exists with long-lived in-flight work — unnecessary here. | RFC acceptance | Accept or propose umbrella branch |
  | D5 | Shaping artifacts in-repo? | **Yes — vision, capability maps, opportunity assessments committed to `docs/product/shaping/`** | Strategic shaping artifacts are decisions, not corpora; they belong in the committed tree | RFC acceptance | Accept or propose external-only |
  | D6 | Brief-level `Status` field? | **Explicit hand-set field** (Draft → Ready → Executing → Shipped) distinct from spec-level Coverage | Spec Coverage is auto-derived from each spec's own `Status:` field (CONVENTIONS); brief-level Status is declared intent, hand-set at DoR gate and at ship — two different fields on two different artifact levels. DoR "Ready" gate: brief has Outcome, Appetite, ≥1 Rabbit hole, and a Spec map skeleton | RFC acceptance | Accept or propose auto-derive brief Status from spec rollup |
  | D7 | Dependency model for queue entries? | **Inline `needs` field on queue entries** — entry is a string (no deps) or `{path/slug, needs}` (with deps); `needs` uses a queue-prefix notation (`work:`, `shape:`, `brief:`) to express cross-queue deps; cross-initiative deps prefix the initiative slug: `"ini-002:work:spec/..."` | Flat lists can't express "these three run in parallel, this one waits for that one." The JIT build-then-use pattern (build a skill → use it to do shaping work) requires cross-queue deps. Cross-initiative prefix enables `check-workspace` to resolve deps that span parallel initiatives in the same file. Enforcement stays with `check-workspace` (display); work-loop enforcement deferred | RFC acceptance | Accept or propose a separate `[deps]` table |
  | D8 | Research output path? | **`docs/product/research/<slug>/`** (repo-scoped default); personal workspace is user-configured (e.g. Obsidian ACE vault at `<vault>/efforts/research/<slug>/`) | `.context/research/` (current pack.toml default) is gitignored ephemeral scratch — not durable across sessions, not committed, not team-visible. Research artifacts are decisions that belong in the committed tree alongside `docs/product/shaping/`. `research/` is separate from `findings/` (structured registers: `rfc-candidates.md`, `roadmap-intents.md`). No universal Obsidian vault default path exists — personal branch of the elicitation prompts for the vault path explicitly. Dropped as part of M3 `research-project-start` fix. | RFC acceptance | Accept `docs/product/findings/` (mixes artifacts with registers) or external-only |
  | D9 | Typed shaping_queue entries? | **`type` field on shaping_queue entries** — `research` (desk-research pack), `strategy` (product-strategy pack), `shape` (PE six-step, default), `signal` (ongoing landscape monitoring — does not graduate to a brief; surfaced by `check-workspace` as "active context," not "ready to start"; subtypes deferred — e.g., regulatory, market, technology, risk; hand-authored in `workspace.toml` by the strategist — no skill produces a `signal` entry); `check-workspace` surfaces each type with the right skill prompt; cross-type deps use the queue prefix: `needs = "research:<slug>"`. **Terminology note:** `frame-situation` consumes raw input signals (market events, OKR gaps) and routes them into the six-step sequence as `shape`-typed queue entries — distinct from `type = "signal"` entries. Input-signal = raw triggering event; `type = "signal"` = standing non-graduating landscape concern. | Research and altitude-0 strategy are upstream of PE shaping but are done by different people (researchers, product strategists). `signal` entries represent ongoing landscape concerns (regulatory surveillance, competitive monitoring, technology watch) whose lifecycle is fundamentally different — they inform shaping decisions without producing a brief; the canonical term is from strategic foresight practice (STEEP, horizon scanning). Typed entries give all roles queue visibility without adding separate sections. Default `shape` means existing entries require no migration. | RFC acceptance | Accept separate `[research_queue]` + `[strategy_queue]` sections |

## Problem & goals

### Problem

Teams operating at Step 1–2 of AI-native maturity have no structured way to:
1. Declare which initiative a body of work belongs to and what its outcome is.
2. Queue briefs in priority order and track their readiness (Draft → Ready → Executing → Shipped).
3. Queue specs for execution and have an agent orient to them at session start.
4. Capture product vision, strategy, and capability maps as committed artifacts that survive session boundaries.
5. Connect work in a component repo to an initiative that may span multiple repos.
6. Express dependencies between work items within and across queues — what can run in parallel, what must sequence, and where a build ship unlocks shape work or a shape output unlocks the next brief.

### Goals

- Any agent can open a session and, with one skill invocation, know: current initiative → shaping queue → brief queue → active specs → what to work on next.
- `check-workspace` resolves the dependency graph and surfaces parallel candidates (what can start now) separately from blocked items (what is waiting and why).
- A team can bootstrap `workspace.toml` from an RFC or roadmap — pre-seeded with all known work items and cross-queue deps — so cold-start is immediately useful from the first session after `check-workspace` ships.
- `workspace.toml` works without any particular harness, tracker, or CI system.
- The vocabulary maps to every major tracker so no team abandons their existing tools.

### Non-goals

- Real-time execution state in git (that lives in the harness platform).
- Cross-repo coordination above the initiative level, CLI/cloud harness adapters, session management, UI/dashboards, or observability infrastructure — these are sister initiatives (INI-003/004/005/006) painted in `docs/product/shaping/ecosystem-overview.md` for context; none are in scope here.
- Prescribing which harness or model is used.

## Proposed design

### Vocabulary

| Our term | Definition | Maps to |
|---|---|---|
| **Initiative** | Cross-repo, multi-quarter strategic goal | Linear Initiative / Jira Initiative (Premium) / Jira Align Theme |
| **Project** | Per-repo, time-bounded outcome (3–8 weeks) | Linear Project / Jira Epic / GitHub Milestone / Asana Project |
| **Milestone** | Named checkpoint within a project (set of briefs) | Linear Milestone / GitHub Milestone / GitLab Milestone |
| **Brief** | Shaped work unit — problem + appetite + rabbit holes + instrumentation | Linear Issue / Jira Story / GitHub Issue / Shape Up Pitch |
| **Spec** | Technical decomposition of a brief | Linear Sub-issue / Jira Sub-task / GitHub Sub-issue |

### `workspace.toml` schema

`workspace.toml` lives on `main`. It is a **repo-level artifact** that persists with the repo across initiatives — not scoped to any one initiative's lifetime. Each initiative gets its own named section. Multiple initiatives can run in parallel. When an initiative ships, its section is removed; git history preserves the record. Blank file (or empty-sections file) = no active initiatives.

Queue entries are **strings** (no dependencies) or **inline objects** `{path/slug, needs}` (with dependencies). `needs` is a string or list; prefix with the queue: `"work:path"`, `"shape:slug"`, `"brief:path"`. Cross-initiative deps prefix the initiative slug: `"ini-002:work:spec/m1-check-workspace"`. `check-workspace` reads all sections, resolves the DAG across all active initiatives, and surfaces (a) items ready to start now, (b) blocked items with reason, (c) parallel candidates.

**Schema — per-initiative named section:**

```toml
["<initiative-slug>"]
name      = "<human name>"
status    = "active"          # active | shipped
milestone = "<current milestone name>"
parent    = "<INI-ID or URL>"

["<initiative-slug>".shaping_queue]
# All upstream work. Entries are strings or {slug, type?, needs?} objects.
# type: "shape" (default — PE six-step), "research" (desk-research pack), "strategy" (product-strategy pack), "signal" (ongoing monitoring — does not graduate to brief)
# check-workspace surfaces each type with the right skill prompt for the user's packs.
# signal entries surface as "active context" (not "ready to start"). Cross-type deps: needs = "research:<slug>" or "strategy:<slug>"
active  = []
backlog = []

["<initiative-slug>".brief_queue]
# Status lifecycle: Draft → Ready (DoR gate) → Executing → Shipped
# Skills: receive-brief, author-brief, new-rfc
executing = ""
ready     = []
draft     = []

["<initiative-slug>".work]
# Entries are strings or {path, needs} objects.
# needs resolves within any queue or across initiatives.
# work-loop updates this file on ship (edit in working directory, committed in same PR).
active  = []
shipped = []
queue   = []
```

**Blank state** — no active initiatives:

```toml
# workspace.toml — add ["<initiative-slug>"] sections to declare initiatives
```

**Closeout** — when all specs reach `shipped` and `active = []`, `check-workspace` surfaces: "ini-002: all specs shipped — run closeout?" Closeout removes the `["ini-002"]` section block. Git history preserves the record; no archive file needed.

**Multi-initiative example** — two parallel initiatives with a cross-initiative dependency:

```toml
["ini-002"]
name      = "Platform Core"
status    = "active"
milestone = "M1 · Workspace Foundation"
parent    = "INI-001"

["ini-002".work]
active  = []
shipped = ["spec/m1-workspace-core", "spec/m1-work-queue"]
queue   = []  # all shipped — closeout pending

["ini-003"]
name   = "Coding CLI Adapters"
status = "active"
parent = "INI-001"

["ini-003".work]
active  = []
shipped = []
queue   = [
  # ini-003 cannot start until ini-002 workspace-core ships
  {path = "spec/ini003-adapter-foundation",
   needs = "ini-002:work:spec/m1-workspace-core"},
]
```

**Bootstrap example — INI-002 M1, committed to `main` with the workspace-core batch (Batch 2):**

```toml
# workspace.toml

["ini-002"]
name      = "Platform Core"
status    = "active"
milestone = "M1 · Workspace Foundation"
parent    = "INI-001"

["ini-002".shaping_queue]
active  = []
backlog = [
  # Signal items — hand-authored by strategist; ongoing, non-graduating
  {slug = "ai-native-regulatory-watch", type = "signal"},
  # Research items — any user with the desk-research pack can pick these up
  {slug = "adopter-persona",   type = "research"},
  # Shaping items — PE picks up when upstream research is done
  "ini-002-initiative-brief",
  {slug = "opp-assessment-pe-pack",  needs = "work:spec/m2-frame-situation"},
  {slug = "capability-map-ini-002",  needs = "work:spec/m2-map-capabilities"},
]

["ini-002".brief_queue]
executing = ""
ready     = []
draft     = []

["ini-002".work]
active  = []
shipped = ["spec/m1-workspace-core"]  # Batch 2 — workspace core ships with this file
queue   = [
  # Batch 3 — work queue end-to-end (after workspace-core)
  {path = "spec/m1-work-queue",
   needs = "work:spec/m1-workspace-core"},
  # Batch 4 — brief queue end-to-end (after workspace-core, independent of Batch 3)
  {path = "spec/m1-brief-queue",
   needs = "work:spec/m1-workspace-core"},
  # Batch 5 — governance + shaping (independent)
  "spec/m1-governance-integration",
  "spec/m1-shaping-seeds",
]
```

Note: Batches 1 and 2 (foundation docs + workspace core) need no spec entries — they are the infrastructure. `spec/m1-workspace-core` covers the workspace.toml seed, layout config, and check-workspace skill shipped as one unit.

Once the workspace-core batch ships, run `check-workspace` — it reads this file and surfaces what is ready to start next.

**Scale — start minimal, add sections as the team grows:**

| Team size | Start with | Add when |
|---|---|---|
| Solo / 1–5 | `["slug".work]` only | More specs in flight than you can track mentally |
| 5–20 | Add `["slug".brief_queue]` | PMs write briefs; engineers pick them up |
| 20–50 | All three sections per initiative | A dedicated PE role works the shaping queue |
| 50+ / multi-repo | One `workspace.toml` per repo; cross-repo initiative tracking via external tracker | Multiple repos contributing to one initiative |

### Three-altitude model

The six-step development sequence (Outcome → Problem → Diverge → Validate → Bet → Spec) operates at every altitude with different time horizons:

| Altitude | Scope | Skills | Artifacts |
|---|---|---|---|
| 0 — Company | Years; C-suite | product-strategy pack (future) | PRFAQ, OKR, Wardley Map |
| 1 — Initiative | Quarters; PM + senior eng | frame-situation, frame-intent, de-risk-intent (existing); identify-opportunities, map-capabilities (M2) | Vision, capability map, initiative brief, briefs |
| 2 — Project | Weeks; product trio | receive-brief, new-spec, work-loop | Brief, spec, plan |

### Shaping queue concept

The `[shaping_queue]` sits upstream of `[brief_queue]`. It holds all pre-brief upstream work via typed entries (D9):

- **`type = "shape"`** (default) — PE six-step sequence: `frame-situation` → `identify-opportunities` → `diverge-solutions` → validate → `place-bet` → `map-capabilities`. Produces shaping artifacts in `docs/product/shaping/`.
- **`type = "research"`** — desk-research pack: `research-project-start <slug>`. Produces findings in `docs/product/research/<slug>/` (or user-configured personal workspace). Non-technical users can pick these up without PE skills.
- **`type = "strategy"`** — product-strategy pack (M4): altitude-0 analysis (SWOT, PESTLE, OKR cascade, PRFAQ). Non-technical product strategists pick these up. Artifacts committed to `docs/product/shaping/`.
- **`type = "signal"`** — ongoing landscape monitoring (regulatory, competitive, technology, risk — subtypes deferred). Does not graduate to a brief. `check-workspace` surfaces signals as "active context" separately from project-bound "ready to start" items; the strategist acknowledges and notes shaping implications rather than promoting to a brief. Canonical term from strategic foresight practice (STEEP, horizon scanning at EU JRC and product strategy firms).

`check-workspace` surfaces each type with the appropriate skill prompt. A shaping item can depend on a research item: `needs = "research:adopter-persona"` — the shaping item becomes ready only when the research project's findings are committed.

### INI-002 milestone map

| Milestone | Scope |
|---|---|
| M1 · Workspace Foundation | workspace.toml seed, check-workspace, brief template DoR fields, work-loop / receive-brief / new-rfc extensions |
| M2 · Strategic Shaping | frame-situation, identify-opportunities, diverge-solutions, place-bet, map-capabilities, JTBD + Wardley in PE pack |
| M3 · Findings & RFC Management | findings register seeds, rfc-status skill, research-project-start .context/ bug fix |
| M4 · Product Strategy Layer | product-strategy pack, OKR → gap analysis routing, PRFAQ template |
| M5 · Tracker Integration | github-brief-intake, linear pack + linear-brief-intake, jira-align-brief-intake |
| M6 · Documentation Wave | workspace-toml guides, PE pack Diátaxis guides, Astro site project index |

> **Ecosystem context (not in scope):** INI-003 (Coding CLI Adapter Pack), INI-004 (Remote Agent Runtime), INI-005 (Infra & Observability), and INI-006 (Control Plane) are separate initiatives in their own repos, each with its own RFC when triggered. They are painted in the product vision and `docs/product/shaping/ecosystem-overview.md` to complete the picture; they are not part of this RFC's scope or completion condition.
>
> **INI-004 note — remote agent runtime and non-technical users:** Two execution paths for non-local harnesses. **Path A — skill adaptation (INI-003 scope):** skills become MCP tools or system-prompt injections in the remote agent session; stateless single-pass skills port cleanly to the Claude Agents SDK; orchestration-heavy skills (e.g., `work-loop` supervisor mode) require re-plumbing because the SDK's "agent as tool" multi-agent pattern differs from Claude Code's `Agent` dispatch. **Path B — ephemeral box (INI-004 scope):** spin up a full Claude Code sandbox on demand (Modal, E2B, Daytona, Databricks), pass in `workspace.toml` and the task, execute the complete skill ecosystem natively; nothing to port, at the cost of cold-start latency and per-session sandbox overhead. `workspace.toml` is harness-agnostic under either path — it is a local file the agent reads and writes regardless of execution environment. **Non-technical user story (agentic UI):** for non-technical users on a hosted agentic UI (researcher, product strategist), `check-workspace` output is the natural session entry point; `type = "research"` and `type = "strategy"` entries surface the right skill prompt with no CLI required; the harness provides the environment. INI-004 RFC governs path selection, sandbox provider choice, and non-technical user onboarding.

## Acceptance criteria

> **Shipped when:** all M1–M6 ACs below are complete. Sister initiatives are not a completion condition for this RFC.
>
> **Implementation sequence:** M1 begins immediately on acceptance. Each subsequent milestone begins when the prior one ships. Sub-RFCs for M2, M4, and M5 are opened at the start of each milestone and govern decisions not yet made. M3 and M6 are direct implementations from this RFC's design; no sub-RFC needed.

### M1 · Workspace Foundation — initial implementation, begins on acceptance

ACs are grouped by delivery batch (see spec map above). Each batch ships as one PR; batches within a group are independent.

**Batch 1 — Foundation docs**
- [ ] ADR authored recording D2 (`workspace.toml` TOML format) and revised D4 (`workspace.toml` on `main`; no umbrella branch; spec branches target `main` directly)
- [ ] `CONVENTIONS.md §5b` amended: admit `projects/`, `shaping/`, `findings/`, `initiatives/`, `research/` under `docs/product/`

**Batch 2 — Workspace core** ← *unlock; ship as one PR*
- [ ] `workspace.toml` schema seed committed to `main` — repo-level artifact; per-initiative named sections (`["ini-002"]`, etc.); multi-initiative parallel sections supported; blank-file valid; closeout = remove the section when shipped
- [ ] `agentbundle-layout.toml [product]` table: configurable paths (`projects/`, `shaping/`; briefs path stays pinned)
- [ ] `check-workspace` skill: reads local `workspace.toml`; resolves DAG across all sections using `needs` fields and cross-initiative prefix (`ini-002:work:...`); surfaces (a) ready to start, (b) blocked with reason, (c) parallel candidates; surfaces each `[shaping_queue]` entry by `type` (`shape`/`research`/`strategy`/`signal`) with the matching skill prompt for the user's installed packs; `signal` entries surfaced as "active context" distinct from project-bound "ready to start" items (D9); offers to initialise if file absent; surfaces closeout prompt when all specs shipped
- [ ] Pre-populated INI-002 queue committed in the same PR as the seed — all Batch 3–5 specs pre-seeded so `check-workspace` is immediately useful

**Batch 3 — Work queue end-to-end** (after Batch 2)
- [ ] `work-loop` extended: reads `workspace.toml` at step 0 for initiative/milestone context; on ship, edits `workspace.toml` in working directory (`[work].active → [work].shipped`) and surfaces `roadmap.md` update reminder; degrades gracefully if file absent

**Batch 4 — Brief queue end-to-end** (after Batch 2; independent of Batch 3)
- [ ] Brief template updated: `Status`, `Rabbit holes`, `Instrumentation`, `## Design artifacts` fields; existing briefs grandfathered — new fields not required retroactively; `receive-brief` handles both shapes
- [ ] `receive-brief` extended: sets `Status: Ready` after decomposition; edits `workspace.toml` in working directory (brief `draft → ready`); degrades if absent
- [ ] `author-brief` skill: takes unstructured external input (email, prose, Linear Issue text); elicits missing DoR fields interactively; creates a compliant brief file; writes to `[brief_queue].draft` in `workspace.toml`

**Batch 5 — Governance integration + shaping home** (after Batch 1; independent of Batches 2–4)
- [ ] `new-rfc` extended: Accepted path prompts "Add implementation specs to `workspace.toml` queue?"; degrades if absent
- [ ] `docs/product/projects/_template.md` seed + shaping/findings/initiatives artifact seeds — one PR
- [ ] `workspace.toml` dependency model documented: inline `{path/slug, needs}` format; cross-queue prefix notation; cross-initiative prefix; `check-workspace` is the display surface; `work-loop` enforcement of DAG deferred to post-M1 backlog

### M2 · Strategic Shaping

- [ ] RFC-00XX · pe-pack-strategic-shaping sub-RFC opened and accepted before any M2 skill implementation begins; boundaries for all overlap pairs are already decided (Known Unknowns, resolved 2026-07-18): `frame-intent` vs `frame-situation` — coexist (different scopes and output contracts); `explore-options` vs `diverge-solutions` — coexist (different output contracts); `de-risk-intent` vs `place-bet` — sequential, not overlapping (steps 3.5 and 5 respectively). Sub-RFC documents implementation guidance (when to reach for each skill) and governs remaining implementation details; it does not re-open boundary decisions. After sub-RFC is accepted, use `new-rfc` extension (M1.9) to prompt adding M2 implementation specs to `[work].queue` in `workspace.toml`.
- [ ] `frame-situation` skill in PE pack: signal → typed finding → six-step route; Wardley capability maturity embedded
- [ ] `identify-opportunities` skill in PE pack + opportunity assessment artifact seed; JTBD framing (functional / emotional / social jobs) embedded
- [ ] `diverge-solutions` skill in PE pack; overlap with `explore-options` resolved per sub-RFC before this spec is authored
- [ ] `place-bet` skill in PE pack: human commitment gate, betting table surface; overlap with `de-risk-intent` resolved per sub-RFC before this spec is authored
- [ ] `map-capabilities` skill in PE pack: product vision → all capability areas in one pass
- [ ] Initiative brief artifact + `docs/product/initiatives/_template.md` seed
- [ ] JTBD framing embedded in `frame-intent` — this is a modification to a shipped skill; backward-compatibility impact assessed in its own spec (not bundled with other M2.6 items); existing `frame-intent` outputs remain valid
- [ ] Lean Canvas initiative framing template

### M3 · Findings & RFC Management

- [ ] `docs/product/findings/rfc-candidates.md` seed with schema: `| Problem | Source | Surfaced by | Date | Priority | Disposition |` — one row per candidate RFC; entries added by convention when `work-loop` defers something out of scope, or when `frame-situation` escalates a finding
- [ ] `docs/product/findings/roadmap-intents.md` seed with same schema adapted for roadmap items
- [ ] `rfc-status` skill in governance-extras: scans `docs/rfc/*.md` grouped by lifecycle state (valid states per CONVENTIONS.md §3 RFC lifecycle: `Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental | Superseded`; CONVENTIONS.md already defines this closed set — no update needed; `Shipped` is a spec status, not an RFC status); also scans `rfc-candidates.md` and surfaces candidate count separately
- [ ] `rfc-status` surfaced in `check-workspace` output as a count line: "N rfc candidates · M roadmap intents"
- [ ] `work-loop` convention documented: on spec ship, if anything is deferred out of scope, agent prompts "Add to rfc-candidates.md or roadmap-intents.md?"
- [ ] `research-project-start` bug fix (D8): remove `parent = ".context/research"` from resolution order in the skill — `.context/` is gitignored ephemeral scratch; the M3 fix also adds `[research] output_dir` key to `agentbundle-layout.toml` (new key — does not exist before this fix); resolution order: (1) user-scope `~/.agentbundle/agentbundle-layout.toml [research] output_dir` — personal workspace; (2) repo-scope `agentbundle-layout.toml [research] output_dir` — team convention; (3) neither → two-branch elicitation: repo branch ("Commit to this repo? [`docs/product/research/`]" → writes repo-scope config) or personal branch ("Write to personal workspace? Enter path:" → writes user-scope config; no default — Obsidian has no universal vault path; skill uses `~/Documents/<VaultName>/efforts/research/` as illustrative example only); output always at `<output_dir>/<research-project-slug>/`; co-land a test asserting elicitation fires rather than `.context/` fallback
- [ ] `research` pack renamed to `desk-research` — canonical practitioner term (desk research in consulting / secondary research in design-UX practice); scope: AI-assisted synthesis of existing sources, finding summary schema, research project scaffolding; pack manifest, `plugin.json`, and `agentbundle-layout.toml` updated; build-self run; deprecation alias for the old pack name assessed before ship; migration path documented in pack `AGENTS.md`
- [ ] `experience` pack renamed to `experience-design` — canonical agency term (Experience Design, abbreviated XD; used by frog, Fjord/Accenture Song, AKQA, Huge); zero-ambiguity alignment with practitioner taxonomy; same migration-alias assessment as desk-research rename

### M4 · Product Strategy Layer

- [ ] RFC-0063 · product-strategy-pack is already open as a draft; M4 implementation begins when RFC-0063 is accepted; RFC-0063 governs framework skill designs, pack scope (fully building out the product-strategy pack), and the cross-pack dependency contract with PE pack
- [ ] ADR recorded before implementation begins: decision to add `product-strategy` as a new pack, recorded in `docs/adr/` and in this repo's `AGENTS.md` (per CONVENTIONS — new dependencies recorded before adding)
- [ ] `product-strategy` pack (new): SWOT, Porter's Five Forces, PESTLE, BCG Matrix, OKR cascade; `agentbundle-layout.toml` updated to register the pack; `plugin.json` updated; build-self run to propagate
- [ ] OKR cascade skill routes to `frame-situation` (PE pack) — cross-pack dependency documented in `product-strategy` pack's `AGENTS.md`: PE pack is a required co-install; skill invocation is agent-mediated (not mechanical cross-pack call), so absent PE pack produces a graceful "frame-situation not found — install PE pack" diagnostic rather than a silent failure
- [ ] PRFAQ template as altitude-0 initiative framing artifact

### M5 · Tracker Integration

- [ ] `github-brief-intake` skill: GitHub Issue / Milestone → brief with `Epic:` pointer (implement first — independent of linear pack, builds pattern confidence)
- [ ] RFC-00XX · linear-pack sub-RFC opened and accepted before implementation begins; sub-RFC governs: (a) `linear-brief-sync` delta model (diff fields, PE-approval gate before write, lock when brief is `executing`); (b) AC export direction (`push-acs-to-linear` skill — write ACs back to Linear story for review round; stretch goal, sub-RFC decides scope); (c) field mapping between Linear and brief DoR fields
- [ ] `linear` pack + `linear-brief-intake` skill: Linear Issue / Project → brief (first-time intake); `linear-brief-sync [LIN-123]` skill: re-fetch issue, diff against current brief, present delta for PE approval, write approved changes; refuse to update if brief `Status: Executing` (spec locked)
- [ ] `jira-align-brief-intake` skill (atlassian pack): Jira Align Feature → brief; **1-way intake only** with configuration-guided field mapping for org-specific workflow states and PI cadences; generic portable sync is not a goal (see Known Unknowns — Unknowable)
- [ ] Tracker decision tree and vocabulary mapping table in guides

### M6 · Documentation Wave

- [ ] `workspace.toml` Diátaxis guides: 1 tutorial (your-first-workspace), 2 how-tos (start-a-project, orient-at-session-start), 1 reference (workspace-toml schema), 1 explanation (two-room model — shaping vs. build)
- [ ] PE pack Diátaxis guides: 2 tutorials, 4 how-tos, 2 reference, 2 explanation — named artifact list to be confirmed at M6 spec authoring time
- [ ] `author-brief` documentation: how-to (intake-an-external-brief) + reference (DoR field definitions)
- [ ] Astro site: project index view for non-engineer (PM) visibility — requires `docs/product/projects/` as a data source registered in the Astro build config; AC is complete when the index page renders project entries from committed `_template.md`-shaped files
- [ ] Role journey section committed to `docs/guides/`: PM / engineer / agent — how each uses the system at their altitude; derived from `docs/product/journeys/` living maps
- [ ] Live-demo guide: scenario selection criteria (≥3 representative team types); pre-flight checklist (installs, auth, repo state); narration script targeting the full shaping → brief → spec flow on the org's own codebase in ≤30 minutes — primary M6 deliverable from the enterprise adoption path (surfaced by `team-evaluates-and-adopts` journey Stage 3)
- [ ] Enterprise rollout playbook: champion → CTO → platform team → engineers adoption path; staged rollout phases (pilot team → wave → org-wide); rollout checklist and retrospective template

## Sub-RFCs

This RFC authorises the roadmap and vocabulary. M1 is fully specified by this RFC's design and ACs. Detailed implementation governance for M2, M4, and M5 is delegated to sub-RFCs opened when each milestone begins:

| Sub-RFC | Milestone | Governs |
|---|---|---|
| RFC-00XX · pe-pack-strategic-shaping | M2 | frame-situation, identify-opportunities, diverge-solutions, place-bet, map-capabilities; must resolve overlap with existing PE skills (see Known unknowns) |
| RFC-0063 · product-strategy-pack | M4 | Full build-out of the product-strategy pack; framework skill designs and cross-pack dependency contract with PE pack; already open as draft — M4 begins on acceptance |
| RFC-00XX · linear-pack | M5 | Linear integration and 2-way sync design |

## Evidence and prior art

**Six-step sequence validated across eight methodologies** (Shape Up, Amazon PRFAQ, SVPG dual-track, Torres Opportunity Solution Tree, OKR-driven planning, modern SaaS startups, Design Sprint, Lean Startup). All converge on: Outcome → Problem → Diverge → Validate → Bet → Spec. Primary disagreement is sequential vs. parallel discovery/delivery; both are supported by the `[shaping_queue]` / `[brief_queue]` split.

**Platform-owns-execution-state confirmed** (Devin: VM snapshots; Manus: TiDB database; GitHub Copilot Coding Agent: platform session). All store execution state in the platform; git is the output boundary. This validates `workspace.toml` as declared intent only.

**Vocabulary cross-tool consensus** (Linear, Jira Standard, Jira Premium, Jira Align, Azure DevOps, GitHub, Asana, SAFe): "Project" and "Brief" (≈ Issue / Story) have the widest cross-tool agreement. "Initiative" is widely used but inconsistently defined; its use here (cross-repo, multi-quarter) matches Linear and Jira Premium.

**Initiative umbrella branch** is an established git coordination pattern (kernel topic branches, Shopify release cycles, large OSS feature work) — considered and rejected for this use case; see Alternatives Considered. The coordination problem umbrella branches solve only exists with long-lived in-flight work; the fast-merge model avoids that. `workspace.toml` on `main` (D4) is adopted instead.

## Alternatives considered

**State branch for `workspace.toml`:** A dedicated `state/<slug>` branch storing live execution state. Rejected — no established git precedent; breaks rebase, merge, and PR workflows; conflicts with how Devin / Manus / GitHub Copilot all handle state (platform-owned, not git-owned).

**Option B — brief as directory containing supporting info:** Brief becomes a folder (`docs/product/briefs/<slug>/`) containing the brief plus upstream research, journey maps, and screen flows. Rejected — the brief is an independent shaped artifact; supporting material lives in its own location and is linked from the brief's `## Design artifacts` section.

**Configurable `[container]` type field:** Allow `type = "epic" | "initiative" | "theme"` in the container section. Rejected — adds complexity without benefit; the `name` field and external tracker fields carry org-specific vocabulary; the standard vocabulary is fixed as Project.

**Research registry in the build repo:** `docs/product/findings/research-registry.md` tracking research project folders. Rejected — research corpora belong outside the build repo (private vault or private team repo); only governance briefs bridge back. The research pack manages its own project registry wherever it is configured.

**Initiative umbrella branch:** Keep spec branches targeting a long-lived initiative umbrella branch; batch-merge to `main` on ship. Considered and rejected — the umbrella solves a coordination problem that only exists when specs are long-lived in-flight. With fast-merge, each spec's `workspace.toml` update is a different TOML entry; rebase conflicts are trivially resolved; no umbrella needed. `workspace.toml` on `main` is simpler, removes branch management overhead, and is consistent with the no-long-lived-branches principle. Adopted as D4.

**Markdown+frontmatter for `workspace.toml`:** Use `workspace.md` with YAML frontmatter, matching every other product artifact in the repo. Considered — frontmatter works for flat key-value but requires a custom parser for the three nested sections with per-section comments. TOML was chosen because `workspace.toml` is read by skills programmatically and its nested structure is a first-class use case for TOML. Human readability is comparable.

## Known unknowns

**Resolved (2026-07-18):** Adopter persona — persona is pack-segmented, not monolithic. (1) Core pack alone: primary adopter is a senior engineer / tech lead at a 2–20 person team, already using AI agents, frustrated by session amnesia and lack of structure; self-serve install, no demo required. Enterprise variant: same technical depth, but adoption lands as part of an org-wide AI adoption strategy — enterprise requires live demonstration and champion sponsorship, not documentation-only onboarding. (2) Full stack (PE pack + shaping sequence): primary adopter is a technical PM or PE with both product and engineering depth. (3) Desk-research pack / product-strategy pack: non-technical researchers and product strategists — these now have first-class queue visibility via `type = "research"` / `type = "strategy"` / `type = "signal"` entries in `[shaping_queue]` (D9). Adopter-persona research project added to bootstrap `workspace.toml` as `{slug = "adopter-persona", type = "research"}` — findings will refine M6 onboarding guide design and the enterprise live-demo gap. The enterprise adoption dynamics (live-demo dependency, champion sponsorship) are an open design input to M6.

**Known-unknown (Unknown #8): Portfolio pack design and pack taxonomy.** Four related problems investigated during INI-001 design; three partially resolved.

*(1) Pack taxonomy — resolved.* Research types are professional disciplines, each warranting a dedicated pack rather than overloading a single research pack. Pack renames and new packs planned (see M3 ACs and future items):

| Pack | Canonical discipline | Canonical term | Status |
|---|---|---|---|
| `desk-research` (rename from `research`) | Secondary / desk research | Desk research (consulting); secondary research (design/UX) | M3 rename |
| `design-research` (future, no timeline) | Primary user research | Design Research (IDEO, frog, Fjord); UX Research (product companies) | Future RFC |
| `experience-design` (rename from `experience`) | Experience Design (XD) | Experience Design — frog, Fjord/Accenture Song, AKQA, Huge | M3 rename |
| `product-strategy` (RFC-0063) | Strategy + market intelligence + UX strategy + stakeholder research + content strategy | Strategic Design / Experience Strategy | Draft |
| `regulatory-intelligence` (future, no timeline) | Regulatory landscape monitoring | Regulatory Intelligence | Future RFC |

`design-research` is a sibling of `experience-design` (research → insights → design artifacts), not nested within it. Small teams use experience-design pack only (T1 research primers built in); larger teams with dedicated researchers install both, experience-design declaring a T2 prereq on design-research where primary research depth is needed.

*(2) Evidence lifecycle — partially resolved.* Fast-moving teams run a two-layer model: **Layer 1 — atomic evidence** (interview transcript, competitive observation, regulatory document); **Layer 2 — synthesis artifact** (finding summary with six-part schema: context → key learning → root cause → motivation → consequences → next steps; JTBD opportunity score as portfolio handoff format). Genesis/extension hierarchy: a foundational genesis research project anchors a domain; extension projects refine or add to specific findings without restarting. Layer-2 artifacts bridge from personal vault / private repo into the team repo's shaping queue — the specific bridging mechanism is the open portfolio coordination question below.

*(3) Non-graduating shaping items — resolved.* Regulatory intelligence, competitive monitoring, technology watch, and risk surveillance have a lifecycle incompatible with the shape→brief graduation path — they are ongoing, inform shaping from the sidelines, and never "complete." Resolved by `type = "signal"` in `[shaping_queue]` (D9 addition). "Signal" is the canonical term in strategic foresight practice (STEEP, horizon scanning); subtypes (regulatory / market / technology / risk) are deferred — the generic `signal` type is the catch-all, taxonomy follows practitioner need.

*(4) Portfolio coordination — open.* How does a portfolio-level pack move Layer-2 synthesis artifacts from a private research repo into shaping queues across multiple build repos? `workspace.toml` is per-repo; a CTO or AI adoption lead also needs aggregate adoption metrics (org activation rate, cross-repo throughput, value stream latency). Both may require a portfolio-level artifact (`portfolio.toml` or lightweight registry) aggregating per-repo `workspace.toml` status. **Feeds INI-006** (control plane) directly. Would be closed by: a follow-on RFC after M3 ships; org-level measurement requirements surface from the `team-evaluates-and-adopts` journey and the `adopter-persona` research project.

**Resolved:** `check-workspace` absent-file behaviour — reads local `workspace.toml` from the current working directory (file lives on `main`; always present after Batch 2 ships). If absent: interactive sessions offer to initialise (copy seed); headless/CI sessions fail loudly with a named diagnostic. No `git show`, no branch detection needed.

**Resolved:** Write protocol — `workspace.toml` is a local file on the working branch. Skills (`work-loop`, `receive-brief`, `author-brief`) edit the file in the working directory and stage it as part of the spec diff; it commits to `main` with the spec PR. No worktree, no sidecar, no cross-branch write. Headless and remote-agent adapters (INI-003, INI-004) follow the same pattern — they edit the local file before committing; adapter-specific invocation details are each initiative's own concern.

**Resolved (N/A):** Umbrella branch merge cadence. The umbrella branch model was superseded by D4 revision — `workspace.toml` on `main`, spec branches target `main` directly. No umbrella branch; no merge cadence to decide.

**Resolved (pre-M3 check, 2026-07-18):** `rfc-status` lifecycle vocabulary — CONVENTIONS.md §3 already defines the closed set: `Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental | Superseded`. No CONVENTIONS.md update needed. `Shipped` is a spec status, not an RFC status. `Superseded` is a valid post-accepted transition per CONVENTIONS.md line 103. The M3 AC now references the CONVENTIONS.md set directly.

**Resolved (2026-07-18):** `research-project-start` elicitation behaviour — see D8. Repo default: `docs/product/research/<slug>/` (committed, team-visible, separate from structured registers in `findings/`). Personal workspace: user-configured path, no default (Obsidian has no universal vault path; ACE convention `<vault>/efforts/research/<slug>/` is illustrative). Resolution order: user-scope config → repo-scope config → two-branch elicitation. Pack.toml line `parent = ".context/research"` is the line the M3 fix removes.

**Resolved (2026-07-18):** M2 skill boundary — PE pack has 9 skills; M2 adds 5. All four overlap pairs resolved by output contract and scope: (a) `frame-intent` vs `frame-situation` — not overlapping: `frame-intent` is any-level quick framing, no committed artifact; `frame-situation` is initiative-scope six-step entry, committed typed-finding artifact. (b) `de-risk-intent` vs `place-bet` — sequential, different steps: `de-risk-intent` is validate-step support — identifies the riskiest assumption and prototype approach before the PE conducts validation; `place-bet` is the bet-commitment step after validation. (c) `decompose-intent` vs `receive-brief` — different levels (intent → briefs vs brief → specs); not overlapping. (d) `explore-options` vs `diverge-solutions` — distinct skills with different output contracts: `explore-options` is freeform brainstorm, no minimum, no forced structure, any context; `diverge-solutions` is formal step-3 requiring ≥3 structured comparable options that `place-bet` can reason against — the structured output is the point, making `diverge-solutions` a wrapper over `explore-options` would be wrong. Both stay; the M2 sub-RFC documents when to reach for each but does not decide the boundary (already decided here).

**Resolved (2026-07-18):** M5 — tracker sync model. No webhook, no running infrastructure. The lifecycle is iterative: (1) first intake: `linear-brief-intake` creates brief from story; (2) spec written, ACs pasted back into tracker story for review round (write direction 2 — manual now; `push-acs-to-linear` is a sub-RFC stretch goal); (3) review round changes the story; (4) delta catch-up: `linear-brief-sync` re-fetches, diffs against current brief, presents delta for PE approval before writing — PE-authored brief fields (Appetite, Rabbit holes, Instrumentation) are protected; (5) lock: brief `Status: Executing` (spec building) → sync skill refuses further updates. Zero infrastructure at every step — all PE-triggered, no event subscription. Sub-RFC governs: delta model details, AC export scope, field mapping. `github-brief-intake` establishes the pattern first (M5 AC unchanged).

**Unknowable:** Exact adoption journey for enterprise teams with Jira Align mandates. The integration surface is org-specific (custom workflow state names, program increment cadences); a generic portable sync is impossible — this will always require harness-layer configuration. The M5 `jira-align-brief-intake` AC is intentionally scoped to 1-way intake (Jira Align Feature → brief) with configuration-guided field mapping; it does not claim generic portability.
