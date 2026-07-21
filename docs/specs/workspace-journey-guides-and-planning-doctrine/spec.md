# Spec: workspace-journey-guides-and-planning-doctrine

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 Amendment #3 (e)(f) — vertical journey-phase slices, phase-slice planning doctrine
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

The P1 "Orient + Capture" phase ships the workspace journey's first end-to-end walkable slice: six core guides that orient a new user to the workspace model and the planning doctrine that prevents documentation from being deferred to a terminal wave. An engineer or technical PM arriving at a repo that uses `workspace.toml` finds a complete orientation path — tutorial → session-start how-to → schema reference — plus dedicated guides for starting a project, capturing work, and understanding the two-room model. The skills that scaffold plans (`new-rfc`, `receive-brief`) carry phase-slice doctrine so future RFCs and briefs cannot repeat the mistake of deferring all guides to a terminal documentation wave. `docs/CONVENTIONS.md` anchors the doctrine in two places so it is discoverable from both the working-practices lens and the guides lens.

## Boundaries

### Always do

- Write guides in their correct Diátaxis quadrant: tutorials are learning-oriented (walk the reader through one concrete scenario), how-tos are task-oriented (recipe for a specific goal), reference is information-oriented (dry, complete, accurate), explanation is understanding-oriented (concepts and why)
- Cross-link guides within the set: how-tos link to the relevant explanation and reference; the tutorial links to the relevant how-tos; the explanation links to how-tos for next steps
- Reference skills by their shipped canonical names (`workspace-status`, `capture-work`) — never by an older name or an alias
- Run `make build-self FORCE=1` after any SKILL.md edit and verify it exits 0 before marking the task done
- Write all guide prose in present tense, retcon style — the feature already works this way

### Ask first

- Any guide step that describes a workflow or command whose actual behavior differs from the current shipped skill — surface the discrepancy and confirm which is authoritative before writing
- Any CONVENTIONS.md change that touches an existing section heading or rewrites an existing definition rather than adding a new subsection

### Never do

- Add acceptance criteria, spec metadata, or implementation detail to guide documents — guides describe usage; contracts live in `spec.md`
- Create a new top-level directory in `docs/guides/` or add a new quadrant directory under `docs/guides/core/` — the four Diátaxis subdirs are the structure
- Change skill behavior (branching logic, output format, data written) in this PR — SKILL.md edits are prose and cross-reference additions only; behavioral changes require their own spec
- Write a guide for a skill or concept not in scope for P1 — scope is the six guides listed in the Acceptance Criteria

## Testing Strategy

This spec delivers prose artifacts (guides and SKILL.md prose). No runtime logic is introduced.

- **Goal-based check** for guide existence: `ls docs/guides/core/{explanation,how-to,reference,tutorials}/` confirms each of the six files is present after the relevant task
- **Goal-based check** for CONVENTIONS.md doctrine: `grep -ci "phase-slice" docs/CONVENTIONS.md` returns ≥ 2 (one per targeted section — heading `### Phase-slice planning` plus at least one prose or cross-reference occurrence in `§ 5c`)
- **Goal-based check** for new-rfc SKILL.md update: `grep -c "terminal\|phase.*guide\|guide.*phase" packs/governance-extras/.apm/skills/new-rfc/SKILL.md` returns ≥ 1
- **Goal-based check** for receive-brief SKILL.md update: `git diff packs/core/.apm/skills/receive-brief/SKILL.md | grep "^+" | grep -i "guide"` returns ≥ 1 line
- **Goal-based check** for cross-linking (AC12): for each of the six guide files, `grep -l "two-room-model\|orient-at-session-start\|workspace-toml-schema\|capture-work\|start-a-project\|your-first-workspace" <file>` returns the file itself (i.e. at least one sibling guide is referenced)
- **Goal-based check** for AC13: `grep -c "workspace-journey-guides-and-planning-doctrine" docs/specs/README.md` returns ≥ 1
- **Goal-based check** for projection: `make build-self FORCE=1` exits 0
- **Manual QA** for Diátaxis compliance: spot-check each guide for quadrant correctness — tutorial has a concrete learning scenario, how-tos start with a numbered-step recipe, reference has no prose narrative, explanation has no recipe steps

## Acceptance Criteria

- [x] AC1: `docs/guides/core/tutorials/your-first-workspace.md` exists and walks a reader through: arriving at a repo with `workspace.toml`, running `workspace-status`, reading the orientation output, and picking a next action — ending with the reader having completed one agent session
- [x] AC2: `docs/guides/core/how-to/start-a-project.md` exists as a task-oriented recipe covering the steps to begin contributing to an existing project that uses the workspace model (install core pack if not present, run `workspace-status`, identify active initiative and queue, pick up the first ready item)
- [x] AC3: `docs/guides/core/how-to/orient-at-session-start.md` exists as a task-oriented recipe for orienting at each session start, including the `workspace-status` invocation, reading the active-context and ready-to-start sections, and identifying the next action
- [x] AC4: `docs/guides/core/how-to/capture-work.md` exists as a task-oriented recipe covering how to use the `capture-work` skill to triage and route a surfaced item (build vs. shaping, mode classification, confirm before write)
- [x] AC5: `docs/guides/core/reference/workspace-toml-schema.md` exists as an authoritative, dry, complete description of every `workspace.toml` section (`["ini-NNN"]`, `["ini-NNN".shaping_queue]`, `["ini-NNN".brief_queue]`, `["ini-NNN".work]`, `[backlog]`), all fields within each section, the `needs` queue-prefix notation, and the full `type` vocabulary for shaping entries (`shape | research | strategy | signal | design`) as defined in `packs/core/.apm/skills/capture-work/SKILL.md`
- [x] AC6: `docs/guides/core/explanation/two-room-model.md` exists and explains why the build/shape separation exists, what goes in each room, and how the rooms relate — links to `orient-at-session-start` and `capture-work` for next steps
- [x] AC7: `docs/CONVENTIONS.md` contains a `### Phase-slice planning` subsection under `§ How we do non-trivial work` stating: each journey phase ships its capability and its guide(s) together; a phase whose tooling ships without its guide is not a complete slice
- [x] AC8: `docs/CONVENTIONS.md` contains a cross-reference to the phase-slice planning principle under `§ 5c. docs/guides/` — either a forward pointer or a repeated one-sentence summary — so the guides section reinforces the doctrine
- [x] AC9: `packs/governance-extras/.apm/skills/new-rfc/SKILL.md` contains explicit roadmap-sequencing guidance: when an RFC covers multiple phases, guides ship with the phase that introduces their capability — not in a terminal documentation wave
- [x] AC10: `packs/core/.apm/skills/receive-brief/SKILL.md` has its "shippable slice" definition extended to state that a slice's scope includes the guide the capability needs to be independently usable — a slice without its guide is not shippable
- [x] AC11: `make build-self FORCE=1` exits 0 after all SKILL.md edits
- [x] AC12: The six guides are internally cross-linked: each how-to references the two-room explanation and/or the schema reference where relevant; the tutorial links to the how-tos; the explanation links to orient-at-session-start and capture-work
- [x] AC13: `docs/specs/README.md` contains a table row for `workspace-journey-guides-and-planning-doctrine/` in the Active specs table, with Status, Constrained by, and Notes columns populated

## Assumptions

- **Technical**: `docs/guides/core/` has all four Diátaxis subdirs (`explanation/`, `how-to/`, `reference/`, `tutorials/`) and none of the six target files exist yet (source: `ls docs/guides/core/` — confirmed 2026-07-21). Adjacent existing guides that this spec does not duplicate: `tutorials/start-a-new-project.md` (greenfield inception — distinct from `your-first-workspace.md` which targets an existing workspace.toml-bearing repo); `how-to/plan-and-execute-non-trivial-work.md` (the work-loop itself — distinct from `orient-at-session-start.md` which covers reading the session state before picking up work)
- **Technical**: `new-rfc` skill source is at `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`; no existing phase-slice or roadmap-sequencing guidance present (source: `grep` — confirmed 2026-07-21)
- **Technical**: `receive-brief` skill uses "shippable slices" already; no "guide" in its slice definition (source: `packs/core/.apm/skills/receive-brief/SKILL.md` grep — confirmed 2026-07-21)
- **Technical**: CONVENTIONS.md has no existing phase-slice doctrine; natural insertion points are `§ How we do non-trivial work` (line 656) and `§ 5c. docs/guides/` (source: `grep` + heading scan — confirmed 2026-07-21)
- **Technical**: `make build-self FORCE=1` covers the whole catalogue (source: user confirmation 2026-07-21)
- **Process**: Constrained by RFC-0064 Amendment #3 (e)(f) (source: RFC-0064 line 617 + workspace.toml queue comment — confirmed 2026-07-21)
- **Process**: P1 guide scope is all five RFC-0064 AC line 525 items plus the capture-work how-to = six guides total (source: user confirmation 2026-07-21)
- **Process**: CONVENTIONS.md phase-slice doctrine appears in both `§ How we do non-trivial work` and `§ 5c. docs/guides/` (source: user confirmation 2026-07-21)
- **Product**: "Documents capture-work" means a dedicated `how-to/capture-work.md` guide — not reference-only treatment in other guides (source: user confirmation 2026-07-21)
