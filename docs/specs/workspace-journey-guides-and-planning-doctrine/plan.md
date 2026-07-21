# Plan: workspace-journey-guides-and-planning-doctrine

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Nine artifacts ship: six new guide files and three prose edits (CONVENTIONS.md, new-rfc SKILL.md, receive-brief SKILL.md). No runtime code is touched. The skill edits require `make build-self FORCE=1` to project into the installed `.claude/` tree.

Wave 1 authors the foundational artifacts that later guides reference — the two-room explanation and the workspace-toml schema reference — alongside the independent skill and doctrine edits. Wave 2 adds the orient-at-session-start how-to (which references wave 1 artifacts) and the build-self verification. Wave 3 adds the two how-tos that cross-link orient (capture-work, start-a-project). Wave 4 completes the tutorial, which links all how-tos. Wave 5 closes the spec housekeeping (README).

Each task targets specific file paths and has a goal-based verification command.

## Constraints

- RFC-0064 Amendment #3 (e)(f): phase-slice planning doctrine is canon; guides ship with their capability, not in a terminal wave
- CONVENTIONS.md § 5c (Diátaxis): each guide must land in its correct quadrant subdirectory
- Skill edits are prose-only in this PR — no behavioral changes to `new-rfc` or `receive-brief` branching logic

## Construction tests

**Integration tests:** none beyond per-task goal-based checks

**Manual verification:**
- Diátaxis spot-check: read each guide's opening paragraph and confirm it matches its quadrant (tutorial: learning scenario; how-to: recipe goal; reference: dry table/list; explanation: concept and why)
- Cross-link audit: grep each guide for at least one internal cross-link to another guide in the set

## Design (LLD)

### Design decisions

- **Six files, one PR:** all six guides and three skill/doctrine edits ship together so the orientation path is walkable end-to-end on merge. Traces to: AC1–AC12.
- **`capture-work` gets its own how-to (not embedded in orient):** the orient how-to describes reading the session state; capture-work is a distinct task (adding something new). Keeping them separate follows the Diátaxis how-to principle that each how-to solves one specific problem. Traces to: AC3, AC4.
- **CONVENTIONS.md doctrine appears twice:** once in the working-practices section (where RFC authors and plan authors land) and once in the guides section (where a contributor authoring a guide lands). Both placements are cross-referenced, not duplicated — the authoritative statement is in `§ How we do non-trivial work`; `§ 5c` carries a one-sentence summary + forward reference. Traces to: AC7, AC8.
- **SKILL.md prose additions only, no structural refactor:** new-rfc and receive-brief get targeted prose additions in their existing step sequences — no section heading changes, no reordering. This keeps the diff reviewable and avoids breaking existing references in other docs. Traces to: AC9, AC10.

### Component / module decomposition

**New files:**
- `docs/guides/core/tutorials/your-first-workspace.md` — Diátaxis tutorial (AC1)
- `docs/guides/core/how-to/start-a-project.md` — Diátaxis how-to (AC2)
- `docs/guides/core/how-to/orient-at-session-start.md` — Diátaxis how-to (AC3)
- `docs/guides/core/how-to/capture-work.md` — Diátaxis how-to (AC4)
- `docs/guides/core/reference/workspace-toml-schema.md` — Diátaxis reference (AC5)
- `docs/guides/core/explanation/two-room-model.md` — Diátaxis explanation (AC6)

**Edited files:**
- `docs/CONVENTIONS.md` — new `### Phase-slice planning` subsection under `§ How we do non-trivial work`; cross-reference sentence under `§ 5c. docs/guides/` (AC7, AC8)
- `packs/governance-extras/.apm/skills/new-rfc/SKILL.md` — prose addition in the roadmap-sequencing step (AC9)
- `packs/core/.apm/skills/receive-brief/SKILL.md` — prose addition in the shippable-slice definition (AC10)

### Behavior & rules

**Diátaxis quadrant rules:**
- Tutorial (`your-first-workspace`): one concrete scenario, first-person walk-through, assumes nothing about the reader's existing knowledge of workspace.toml. Ends with the reader having completed a real session action.
- How-to (`orient-at-session-start`, `start-a-project`, `capture-work`): numbered steps toward a specific outcome, assumes the reader knows what they want to do, answers "how do I X".
- Reference (`workspace-toml-schema`): no prose narrative beyond field definitions; every field documented; machine-like accuracy; no tutorial steps.
- Explanation (`two-room-model`): no recipe steps; explains the *why*; uses analogies where helpful; links to how-tos for "what to do next."

**Phase-slice doctrine statement for CONVENTIONS.md:**
> Each journey phase ships its capability and its guide(s) together. A phase whose tooling ships without its guide is not a complete slice — the guide is part of the capability, not a follow-on. When authoring a plan or RFC with multiple phases, assign each guide to the phase that introduces its capability; do not group guides into a terminal documentation wave.

**new-rfc guidance addition:** in the step where the RFC author lays out the implementation roadmap, add a note that each phase should name its guide deliverable alongside its tooling deliverable — referencing the phase-slice doctrine in CONVENTIONS.md.

**receive-brief slice extension:** in the "Cut the brief into slices" step (currently: "each slice must be independently shippable and testable"), extend to: "A slice that introduces a new user-facing capability includes the guide that makes it usable — a capability without its guide is not independently usable."

### Dependencies & integration

- `packs/governance-extras/.apm/skills/new-rfc/SKILL.md` → projected to `.claude/skills/new-rfc/` by `make build-self FORCE=1`
- `packs/core/.apm/skills/receive-brief/SKILL.md` → projected to `.claude/skills/receive-brief/` by `make build-self FORCE=1`
- `docs/guides/core/` → static Markdown; no build step; referenced from CONVENTIONS.md and skill cross-references

## Tasks

### T1: Author `explanation/two-room-model.md`

**Depends on:** none

**Touches:** `docs/guides/core/explanation/two-room-model.md`

**Tests:**
- File exists at `docs/guides/core/explanation/two-room-model.md`
- Opening paragraph is concept-oriented, not recipe-oriented (no numbered steps)
- File contains at least two forward links: one to `orient-at-session-start.md`, one to `capture-work.md`
- `grep -i "build\|shape\|two-room\|shaping queue\|work queue" docs/guides/core/explanation/two-room-model.md` returns ≥ 4 matches

**Approach:**
- Author the explanation covering: the two-room metaphor (build room = `[work].queue`; shape room = `[shaping_queue]`); why the separation exists (different cadences, different skills, different artifacts); how items graduate from shape to build; how `workspace-status` surfaces both rooms; how `capture-work` routes new items to the right room
- Close with "What next?" linking to `how-to/orient-at-session-start.md` and `how-to/capture-work.md`
- No recipe steps — only concepts and prose

**Done when:** `ls docs/guides/core/explanation/two-room-model.md` succeeds and manual Diátaxis spot-check passes (explanation quadrant: concept-oriented, no recipe steps)

---

### T2: Author `reference/workspace-toml-schema.md`

**Depends on:** none

**Touches:** `docs/guides/core/reference/workspace-toml-schema.md`

**Tests:**
- File exists at `docs/guides/core/reference/workspace-toml-schema.md`
- All five top-level sections are documented: `["ini-NNN"]`, `["ini-NNN".shaping_queue]`, `["ini-NNN".brief_queue]`, `["ini-NNN".work]`, `[backlog]`
- `needs` queue-prefix notation table is present (columns: prefix, resolves against)
- `type` vocabulary table is present for shaping entries: `shape | research | strategy | signal | design` — all five values from `packs/core/.apm/skills/capture-work/SKILL.md`
- No tutorial steps or how-to recipes in the body

**Approach:**
- Read `packs/core/.apm/skills/capture-work/SKILL.md` for the authoritative full `type` vocabulary and the canonical field descriptions; read `workspace.toml` to confirm field names, TOML section notation (quoted dotted-key form: `["ini-NNN".shaping_queue]` etc.), and inline-object shapes
- Include: section headers, field names, value types, optional vs. required, inline-object notation for entries with `needs`, the queue-prefix notation table, the shaping entry `type` vocabulary, the list-membership lifecycle for `["ini-NNN".work]` entries (active → queue → shipped — lifecycle is encoded by list membership, not a per-entry field)
- Cross-link to `explanation/two-room-model.md` in the opening context line
- Keep prose to field definitions only — no "you should" narrative

**Done when:** `ls docs/guides/core/reference/workspace-toml-schema.md` succeeds and manual spot-check confirms reference quadrant (no recipe steps, dry and complete)

---

### T3: Add phase-slice doctrine to `docs/CONVENTIONS.md`

**Depends on:** none

**Touches:** `docs/CONVENTIONS.md`

**Tests:**
- `grep -ci "phase-slice" docs/CONVENTIONS.md` returns ≥ 2 (heading in `§ How we do non-trivial work` + cross-reference or prose occurrence in `§ 5c`)
- `grep -n "Phase-slice planning" docs/CONVENTIONS.md` matches a `###` heading under `## How we do non-trivial work`
- `grep -n "phase-slice\|phase.*guide\|guide.*phase" docs/CONVENTIONS.md` shows at least one match in the `5c` section

**Approach:**
- Add `### Phase-slice planning` subsection at the end of `## How we do non-trivial work` (after the existing subsections, before `## Scaling profiles`) with the doctrine statement from Design (LLD) § Behavior & rules above
- Under `### 5c. docs/guides/` add a one-sentence cross-reference: "See [Phase-slice planning](#phase-slice-planning) — guides ship with the phase that introduces their capability, not in a terminal documentation wave."
- Do not rewrite existing subsection content; only add

**Done when:** `grep -c "phase-slice" docs/CONVENTIONS.md` ≥ 2 and both placements are visible in `git diff`

---

### T4: Update `new-rfc` SKILL.md with roadmap-sequencing guidance

**Depends on:** none

**Touches:** `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`

**Tests:**
- `grep -c "phase.*guide\|guide.*phase\|terminal.*wave\|phase-slice" packs/governance-extras/.apm/skills/new-rfc/SKILL.md` returns ≥ 1
- Diff adds prose only — no section heading changes, no existing content removed

**Approach:**
- Target the `## After acceptance` section of `packs/governance-extras/.apm/skills/new-rfc/SKILL.md` — specifically the step that prompts to add implementation specs to `workspace.toml` queue. This is the moment the RFC author plans which specs belong to which phase.
- Add a note after the workspace.toml queue-write prompt: when assigning specs to phases, apply phase-slice doctrine — each guide ships with the phase that introduces its capability; do not defer all guides to a terminal phase. Reference the CONVENTIONS.md `### Phase-slice planning` subsection for the canonical statement.
- Keep the addition to 3–5 lines of prose, inline in `## After acceptance`; do not add a new section heading

**Done when:** `git diff` shows a targeted prose addition in the roadmap-authoring step; no structural changes to the skill

---

### T5: Update `receive-brief` SKILL.md with guide-scope extension

**Depends on:** none

**Touches:** `packs/core/.apm/skills/receive-brief/SKILL.md`

**Tests:**
- `git diff packs/core/.apm/skills/receive-brief/SKILL.md | grep "^+" | grep -i "guide"` returns ≥ 1 line
- Diff adds prose only — no branching logic changes

**Approach:**
- Locate the "Cut the brief into slices" step in `receive-brief` SKILL.md (currently defines each slice as "independently shippable and testable")
- Extend the shippable definition: "A slice that introduces a new user-facing capability includes the guide that makes it usable — a capability without its guide is not independently shippable."
- Keep the addition to 2–3 lines inline with the existing step definition

**Done when:** `git diff` shows the targeted extension in the slice definition; no other changes

---

### T6: Run `make build-self FORCE=1` and verify projection

**Depends on:** T4, T5

**Touches:** `.claude/skills/new-rfc/`, `.claude/skills/receive-brief/` (projected)

**Tests:**
- `make build-self FORCE=1` exits 0
- `grep -c "phase.*guide\|guide.*phase\|terminal.*wave\|phase-slice" .claude/skills/new-rfc/SKILL.md` returns ≥ 1 (projected copy matches source)
- `git diff .claude/skills/` shows both skills updated

**Approach:**
- Run `make build-self FORCE=1` from the repo root
- Verify exit code 0
- Spot-check the projected `.claude/skills/new-rfc/SKILL.md` and `.claude/skills/receive-brief/SKILL.md` contain the additions from T4 and T5

**Done when:** `make build-self FORCE=1` exits 0 and projected files contain the additions

---

### T7: Author `how-to/orient-at-session-start.md`

**Depends on:** T1, T2

**Touches:** `docs/guides/core/how-to/orient-at-session-start.md`

**Tests:**
- File exists at `docs/guides/core/how-to/orient-at-session-start.md`
- Numbered steps are present (how-to quadrant requirement)
- `grep -i "workspace-status\|active.*initiative\|ready.*to.*start\|active.*context" docs/guides/core/how-to/orient-at-session-start.md` returns ≥ 3 matches
- Cross-links to `two-room-model.md` and `workspace-toml-schema.md` present

**Approach:**
- Author a recipe with numbered steps covering: (1) run `workspace-status` at session start; (2) read the active initiative and milestone; (3) read active-context signals; (4) read ready-to-start items; (5) pick the next action
- Include a "What to do with each section" note for each `workspace-status` output block
- Link to `explanation/two-room-model.md` for concept background and `reference/workspace-toml-schema.md` for field definitions
- Do not include capture-work steps — that is `how-to/capture-work.md`

**Done when:** `ls docs/guides/core/how-to/orient-at-session-start.md` succeeds and manual Diátaxis spot-check passes (how-to quadrant: numbered recipe, specific goal)

---

### T8: Author `how-to/capture-work.md`

**Depends on:** T7

**Touches:** `docs/guides/core/how-to/capture-work.md`

**Tests:**
- File exists at `docs/guides/core/how-to/capture-work.md`
- Numbered steps are present
- `grep -i "capture-work\|classify\|build\|shaping\|confirm" docs/guides/core/how-to/capture-work.md` returns ≥ 4 matches
- Cross-link to `orient-at-session-start.md` and `two-room-model.md` present

**Approach:**
- Author a recipe covering: when to use `capture-work` (an item surfaced during a session that should be queued); steps: (1) invoke `capture-work`; (2) describe the item; (3) skill classifies (build vs. shaping, mode); (4) skill shows proposed destination and comment; (5) confirm before write; (6) verify the entry in `workspace.toml`
- Include a "When to use vs. not use" note (capture-work = named item that belongs in the queue; not for items already in `workspace.toml`)
- Link to `orient-at-session-start.md` ("see orientation to know where it lands") and `two-room-model.md` for classification context

**Done when:** `ls docs/guides/core/how-to/capture-work.md` succeeds and manual spot-check passes (how-to quadrant)

---

### T9: Author `how-to/start-a-project.md`

**Depends on:** T7

**Touches:** `docs/guides/core/how-to/start-a-project.md`

**Tests:**
- File exists at `docs/guides/core/how-to/start-a-project.md`
- Numbered steps are present
- `grep -i "core pack\|agentbundle\|workspace.toml\|workspace-status\|ready.*to.*start" docs/guides/core/how-to/start-a-project.md` returns ≥ 4 matches
- Cross-link to `orient-at-session-start.md` present
- Cross-link to `explanation/two-room-model.md` present (start-a-project is a natural entry point to understanding the two rooms)

**Approach:**
- Author a recipe covering: (1) confirm core pack is installed (if not, `agentbundle install --pack core`); (2) confirm `workspace.toml` exists at the repo root (if not, `workspace-status` will offer to initialise); (3) run `workspace-status`; (4) read the orientation output — active initiative, ready-to-start items; (5) pick up the first ready item and invoke `work-loop` on it
- Distinguish from the tutorial (the how-to assumes the reader knows *what* they want to do — start on this project — and gives steps without learning narrative)
- Link to `orient-at-session-start.md` for session-level orientation and to `explanation/two-room-model.md` for concept background (AC12: each how-to links to explanation where relevant — relevant here because a contributor arriving for the first time benefits from the two-room context)

**Done when:** `ls docs/guides/core/how-to/start-a-project.md` succeeds and manual spot-check passes (how-to quadrant, starts with numbered steps not narrative)

---

### T10: Author `tutorials/your-first-workspace.md`

**Depends on:** T7, T8, T9

**Touches:** `docs/guides/core/tutorials/your-first-workspace.md`

**Tests:**
- File exists at `docs/guides/core/tutorials/your-first-workspace.md`
- Learning scenario is concrete (a specific repo/initiative context is used throughout, not a generic "your repo")
- `grep -i "workspace-status\|capture-work\|work-loop\|workspace.toml" docs/guides/core/tutorials/your-first-workspace.md` returns ≥ 4 matches
- Links to at least two of the three how-tos authored in T7–T9

**Approach:**
- Author a learning-oriented tutorial using a concrete stand-in repo context (e.g. "a platform repo with one active initiative, two ready specs, and one shaping item")
- Walk the reader through: arriving at the repo; running `workspace-status` for the first time and reading the output section by section; understanding what "ready to start" means; picking a spec and invoking `work-loop`; during the session, noticing a deferred item and using `capture-work` to log it; session closes with the item in the queue
- End with a "What you learned" paragraph naming the two-room model and the orient → capture → build arc
- Link to `how-to/orient-at-session-start.md`, `how-to/capture-work.md`, and `how-to/start-a-project.md` as "Next steps"

**Done when:** `ls docs/guides/core/tutorials/your-first-workspace.md` succeeds and manual spot-check passes (tutorial quadrant: learning narrative, concrete scenario, ends with what was learned)

---

### T11: Update `docs/specs/README.md` (AC13)

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

**Touches:** `docs/specs/README.md`

**Tests:**
- `grep -c "workspace-journey-guides-and-planning-doctrine" docs/specs/README.md` returns ≥ 1

**Approach:**
- Add a table row to the Active specs table in `docs/specs/README.md` following the existing format (`| [`workspace-journey-guides-and-planning-doctrine/`](workspace-journey-guides-and-planning-doctrine/spec.md) | Draft | RFC-0064 Amendment #3 | …short summary… |`)

**Done when:** `grep -c "workspace-journey-guides-and-planning-doctrine" docs/specs/README.md` returns ≥ 1

## Rollout

Pure Markdown and SKILL.md prose — no infrastructure, no data migration, no deployment sequencing. The `make build-self FORCE=1` projection (T6) is reversible; if it produces unexpected diffs, `git checkout` the projected files and re-run after fixing the source. Guides ship with the PR merge; no flag required.

## Risks

- **Diátaxis drift**: guides written without careful quadrant discipline will need a rewrite pass. The manual spot-check in the construction tests catches this before merge.
- **SKILL.md diff sprawl**: if T4 or T5 accidentally touch more lines than intended (e.g. reformatting), the adversarial reviewer will flag it. Keep edits surgical.
- **build-self projection misaligns**: `make build-self FORCE=1` may project more than just the two edited skills if the working tree has other uncommitted changes. Run `git status` before T6 and stage only the intended files.

## Changelog

- 2026-07-21: initial plan
