# RFC-0067: Session-arc naming conventions and pack workflow guide

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-20
- **Date closed:** 2026-07-20
- **Decision weight:** standard
- **Related:** RFC-0025, RFC-0055, RFC-0064, ADR-0051, ADR-0053

## Reviewer brief

- **Decision:** Adopt a session-arc naming convention across packs (rename `check-workspace` → `workspace-status`, establish a verb taxonomy, add pack-specific status skills, wire argless work-loop resume, and create a pack workflow design guide).
- **Recommended outcome:** Accept all four changes.
- **Change if accepted:**
  - `check-workspace` renamed to `workspace-status` (clean retire; operative references swept; frozen ADR bodies left as historical record per CONVENTIONS §2).
  - Two new status skills: `desk-research-project-status` and `experience-status`; `design` added to workspace.toml `shaping_queue` type enum.
  - `work-loop` gains argless resume wiring and description triggers.
  - New explanation guide `docs/guides/_shared/explanation/pack-workflow-design.md`; `CONTRIBUTING.md` and `author-a-skill.md` updated.
- **Affected surface:** core pack, desk-research pack, experience-design pack, workspace.toml schema, docs/guides, CONTRIBUTING.md.
- **Stakes:** Reversible — rename is mechanical with a lint gate; new skills are additive; doc guide is net-new.
- **Review focus:** (1) Verb taxonomy completeness and the banned-label list. (2) Argless work-loop disambiguation: Change C rule 4 lists-and-asks whenever more than one active item exists — whether from a single initiative's multi-element `.active` array or across initiatives — replacing the existing "auto-pick first path" behavior in SKILL.md Step 0.
- **Not in scope:** Status skills for episodic packs (architect, product-strategy, converters, iac-terraform). Workspace.toml schema version bump. Automated arc-compliance checking for existing packs.

## The ask

**Recommendation (BLUF — Bottom Line Up Front):** Accept four interdependent changes that establish a naming and skill convention for the session arc (Arrive → Orient → Work → Persist → Collaborate — the five-stage vocabulary from the `workspace-design` skill, which defines how a sustained professional tool structures a user's session). Every pack whose work spans sessions will have a consistently-named `*-status` skill that answers cold-start orientation, and future pack authors will have a documented design framework to follow before writing their first skill.

**Why now (SCQA — Situation / Complication / Question):**
- **Situation:** The catalogue has three packs that produce durable work across sessions (desk-research, experience-design, product-strategy). A **pack** (a unit of cohesive skills distributed as one installable bundle) whose work spans sessions needs a cold-start orient skill. The workspace-level orient skill is named `check-workspace` — an action, not the information it provides. Pack authors have no documented framework for deciding whether their pack needs a status skill, a project-start skill, or a vault-path pattern (a config-driven output directory where the pack writes durable artifacts).
- **Complication:** As more packs land, pack authors will independently solve the same arc-design questions without a shared vocabulary — leading to inconsistent naming, missing orient skills, and repeated reviewer cycles catching the same gaps.
- **Question:** Can we establish a shared naming convention and design framework now, before the next wave of packs, that prevents this drift?

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Rename `check-workspace` → `workspace-status` via clean retire (no alias) | Accept | Aligns with `*-status` verb convention; no alias maintenance debt; RFC-0048 clean-retire precedent | This review | Confirm clean retire |
| D2 | Frozen ADR treatment: leave ADR-0051 and ADR-0053 bodies as historical record (per CONVENTIONS §2, frozen ADR bodies are never edited); direct body edit for RFC-0064 (Draft, editable) | Accept | CONVENTIONS §2: frozen ADR text is the audit trail; a mechanical rename is not a decision reversal and does not warrant a superseding ADR | This review | Confirm leave-as-historical approach |
| D3 | Argless work-loop: list-and-ask whenever more than one active item exists — whether from a single initiative's multi-element `.active` array or across initiatives — replacing the existing "first path" auto-pick | Accept | Non-surprising; consistent with workspace-status disambiguation behavior; replaces SKILL.md:166 "first path" auto-select and the singular framing at SKILL.md:176–177 | This review | Confirm list-and-ask replaces first-path auto-pick |
| D4 | `experience-status` when `[design] output_dir` not configured: surface "not configured" message + point to `journey-mapping` | Accept | Read-only contract; elicitation is a write-time side effect, not an orient action | This review | Confirm read-only behavior |

## Problem & goals

**Goals:**
1. Establish a verb taxonomy so users can predict skill names across packs.
2. Give desk-research and experience-design first-class cold-start status skills.
3. Wire argless `work-loop` invocation to auto-resume the active spec.
4. Add `design` as a valid `shaping_queue` type in `workspace.toml` (a repo-level TOML file that declares the current initiative's work queue — shaping items, work specs, and briefs — so agents can orient at session start) so experience threads get the same queue visibility as research and strategy items.
5. Document the arc-design framework for future pack authors before the next wave of packs.

**Non-goals:**
- Status skills for episodic packs (architect, product-strategy, converters, iac-terraform) — episodic work has no persistent thread state to orient to.
- A workspace.toml schema version bump — `design` is additive and backwards-compatible with existing entries.
- Automated arc-compliance lint for existing packs.
- Porting the session-arc framework to non-pack authoring contexts.

## Proposal

### Change A — Rename + verb taxonomy

**A1. Rename `check-workspace` → `workspace-status` (clean retire, no alias).**

Rename `packs/core/.apm/skills/check-workspace/` to `packs/core/.apm/skills/workspace-status/`; update the `name:` frontmatter; update the `description:` to trigger on "workspace status", "where am I", "orient me", "session start", "what's ready", "show the queue", "what's next", and any cold-start orientation phrasing.

**Clean retire** (no alias): the old name is removed entirely and all operative references are updated in one PR. Adopters who invoke the old name will get a "skill not found" signal immediately — there is no backward-compatible shim.

Sweep all **operative** references in the same PR. The implementing spec derives the full list from `git ls-files | xargs grep -l "check-workspace"` (approximately 46 tracked files at time of writing) and classifies each hit as operative or historical:

- **Operative** (rewrite): skill directory + `name:`/`description:` fields, `[pack.evals]` blocks (the per-pack allowlist declaring which skills participate in automated trigger-rate evaluation), live skill bodies, `AGENTS.md`, `packs/core/seeds/AGENTS.md` (seed files — the upstream source text the build pipeline projects into adapter-specific locations), `packs/core/pack.toml` (pack manifest — the `skills = [...]` array must match the renamed directory or the skill won't load), `packs/core/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (published pack descriptions), `packs/core/README.md`, `workspace.toml` seed comment, `.claude/skills/README.md`, `docs/CONVENTIONS.md`, `docs/product/journeys/`, `docs/product/roadmap.md`, `docs/product/workspace-toml-deps.md`, `docs/product/projects/_template.md`, `docs/product/findings/README.md`, `site/docs/`, `web/`, cross-pack routing references, projected trees (`.claude/skills/`, `.agents/skills/` — adapter-specific copies generated from seeds by the build pipeline), `docs/rfc/README.md`, and `docs/rfc/0064-ini-001-ai-native-ecosystem.md` (Draft — body editable directly).
- **Historical** (leave as-is): frozen ADR bodies (ADR-0051, ADR-0053 — Accepted per CONVENTIONS §2, never edited), `docs/product/changelog.md` shipping entries, `docs/specs/` (all current spec references are in Shipped specs — historical records of what was specified; treated as shipped documentation per the repo's rename convention: rename operative refs, leave shipped-doc refs), and this RFC's own body.

Lint gate in the implementing PR: `grep -rn "check-workspace"` over the full `git ls-files` output, excluding the explicit historical set (frozen ADR bodies, `docs/product/changelog.md`, `docs/specs/`, this RFC's body), returns zero hits. The gate is derived from the full tracked-file set, not from the illustrative path list above.

**A2. Verb taxonomy in `docs/guides/_shared/how-to/author-a-skill.md`.**

Add a "## Naming your skill" section after "## Body structure":

| Verb | Meaning | Activation phrasing |
| --- | --- | --- |
| `status` | Orient — "where am I / what's next?" | Cold-start phrases, "what's on today", "orient me" |
| `start` | Create/begin a sustained project | "start a research project", "kick off an investigation" |
| `check` | Quality/health read — "is it good / saturated / done?" | "is this ready", "should I keep gathering" |
| `init` | Repo-scaffold only | `init-project`, `adapt-to-project`; cf. `git init` |
| `resume` | Return to prior work | Activation phrase — not a skill name; see work-loop's argless trigger |

Banned as skill names: `arrive`, `orient`, `onboard`, `return`, `onboarding` — these are UX-stage labels, not user-facing commands.

Add one sentence to the guide's intro: "If you're authoring the first skill in a new pack, read [Pack workflow design](../../explanation/pack-workflow-design.md) first — it tells you how to design the pack's arc before writing individual skills."

---

### Change B — New status skills

**B1. `desk-research-project-status` (desk-research pack).**

Reads the project's `overview.md` at the configured `[research] output_dir`. Surfaces: phase (`capture → digest → synthesize → feedback`), working hypothesis (may be empty at start), stop-signal verdict. Reports what the next step is given the current phase.

When no project exists (no folder + `overview.md` at `output_dir`): "No research project found — run `desk-research-project-start` for a sustained project, or `desk-research` for a one-off lookup." Does NOT advance phase.

Activation triggers: "where are we on the X research", "status of the Y investigation", "resume the Z project", any return-to-a-named-research-project phrasing.

Added to desk-research pack's `[pack.evals].skills` allowlist.

**B2. `experience-status` (experience-design pack).**

Resolves `[design] output_dir` read-only (same config chain as the writing skills — repo-root `agentbundle-layout.toml` first, then user-profile, then stop; no elicitation). (`agentbundle-layout.toml` is an adopter-owned config file that tells output-writing skills where to store durable artifacts — one `[section]` per pack, one `output_dir` key per section.) When not configured: "No `[design] output_dir` configured — run `journey-mapping` to create your first artifact (it will set the path)."

Reads artifact frontmatter from:
- `<output_dir>/journeys/*.md` — `type: customer-journey`
- `<output_dir>/screens/*-flow.md` — `type: screen-flow`
- `<output_dir>/blueprints/*.md` — `type: service-blueprint`

Steel-thread check (verifying that the minimal viable artifact chain exists end-to-end: journey map → screen flow → per-screen briefs): Does a journey map exist? Does a screen flow exist? Do all journey stage actions appear in screen-flow briefs? Reports what exists, what's missing, and which skill to run next. When no artifacts exist: points to `journey-mapping` as the thread entry skill.

Activation triggers: "where are we with the design", "what experience artifacts do we have", "status of the design thread", "what's next in the design".

Added to experience-design pack's `[pack.evals].skills` allowlist.

**B3. `design` type in workspace.toml.**

Add `design` as a valid `shaping_queue` entry type (joining `shape`, `research`, `strategy`, `signal`). Update `workspace-status`'s routing table: `design` entries route to `experience-status` (or `journey-mapping` if experience-status is not installed). Update the workspace.toml seed comment and `docs/product/workspace-toml-deps.md`.

---

### Change C — Argless work-loop resume

Add description triggers to `work-loop`: "resume", "continue", "keep going", "pick up where I left off", "let's get going".

Update Step 0's behavior in the `work-loop` SKILL.md body:

1. Collect all active spec paths: for every `["ini-NNN"]` section (ini = initiative — a named block of coordinated work in `workspace.toml`) whose `status = "active"`, collect every path in that section's `[work].active` array. Each path is one "active item."
2. **Exactly one active item (anywhere in the file)** → begin the loop on that spec without asking.
3. **Zero active items** → "No active spec found — run `workspace-status` to see what's ready to start."
4. **More than one active item** (whether from a single initiative's multi-element `.active` array or across multiple initiatives) → list all active paths and ask the user to pick before beginning.

This is a description + Step 0 body change only — no new skill, no new artifact. Per RFC-0025's no-new-skill precedent for `work-loop` changes: a description + body change is sufficient when no new activation surface is needed.

**Reconciliation with the existing Step 0 text.** The current SKILL.md Step 0 auto-picks "the first path in `["<slug>".work].active`" (line ~166) and refers to it in the singular: "The active spec path tells you which spec you are expected to be working on" (lines ~176–177). Rule 4 above explicitly replaces this auto-pick behavior — the implementing spec must remove the first-path default and update the singular-framing language to handle the pending-user-pick state (zero or multi-item cases).

---

### Change D — Pack workflow design guide

**D1. New guide: `docs/guides/_shared/explanation/pack-workflow-design.md`.**

Seven sections with a decision-framework structure, not a pure Diátaxis explanation (Diátaxis is a documentation methodology that separates tutorials, how-to guides, reference material, and explanations into four distinct types):

1. What a pack is — a cohesive set of workflows for a role's work; the session arc (from `workspace-design`) as the design vocabulary.
2. Step 1 — Characterize your workflow type (decision tree: episodic / sustained-project / sustained-derived / stateless).
3. Step 2 — Map the arc for your pack (walk each stage: Arrive, Orient, Work, Persist, Collaborate).
4. Step 3 — Name your skills (verb taxonomy; activation is description-driven; common mistakes).
5. Step 4 — Decide your vault-path shape (if your pack writes files: single `output_dir` base per pack, skill-specific subdirectories; `journey-mapping` references as canonical example).
6. Step 5 — Register with workspace-status (queue type, routing).
7. Reference: four worked archetypes — Episodic (product-strategy), Sustained-project (desk-research), Sustained-derived (experience-design), Stateless (converters/architect-review).

**D2. CONTRIBUTING.md "Adding a new pack" — insert step 0.**

Before the current step 1 ("Open an RFC"), add:

> **0. Design the pack's workflow arc first.** A pack is a set of cohesive workflows for a role's work — not a list of features. Before writing any `SKILL.md`, work through the pack workflow design framework at `docs/guides/_shared/explanation/pack-workflow-design.md`. It takes you through: characterizing whether your pack is episodic, sustained-project, or sustained-derived; mapping the Arrive → Orient → Work → Persist → Collaborate arc to your pack's skill set; naming your skills against the verb taxonomy; and deciding whether your pack needs a status skill, a `*-project-start` skill, and config-driven output paths. The RFC reviewers will ask these questions; answering them before you write the skill bodies saves a review cycle.

Also add to step 1: "The RFC should include your arc mapping from step 0 — which skills cover which arc stages, and why."

**D3. `author-a-skill.md` — naming section + intro link.**

Covered in Change A2 above: the "## Naming your skill" section and the intro sentence linking to the new guide.

## Options considered

Axis: post-rename compatibility guarantee (for Change A).

| Option | Trade-off | Outcome if accepted |
| --- | --- | --- |
| **Clean retire (recommended)** | Mechanical sweep (~46 tracked files, of which ~30 are operative; implementing spec derives the exact list from `git ls-files`); lint gate over operative surface closes missed-reference risk; no alias debt | Full operative-reference update in one PR |
| Alias (`check-workspace` → `workspace-status`) | Zero breaking change; permanently maintains two names and undermines the taxonomy | Two names forever; alias never cleanly removed |
| Do-nothing | No sweep cost | `check-workspace` persists; verb taxonomy has a named exception on day one |

Axis: new-skill vs. description+body change (for Change C).

| Option | Trade-off | Outcome if accepted |
| --- | --- | --- |
| **Description + body change to `work-loop` (recommended)** | Per RFC-0025 precedent; no second activation surface | Argless resume is a `work-loop` behavior, not a new skill |
| New `workspace-resume` skill | New activation surface; duplicates `work-loop` triggers; "resume" becomes ambiguous between two skills | Ongoing ambiguity |
| Do-nothing | No change cost | Users must always pass a spec path argument |

Axis: guide scope (for Change D).

| Option | Trade-off | Outcome if accepted |
| --- | --- | --- |
| **One shared framework at archetype level (recommended)** | Stable; archetype membership changes slowly; one doc to maintain | Single guide covers all future packs |
| Separate guide per pack | Zero staleness per pack; high maintenance N-way duplication | N guides, no shared vocabulary |
| Do-nothing | No authoring cost | Every future pack RFC catches the same gaps in review |

## Risks & what would make this wrong

**Pre-mortem:**
- The `check-workspace` operative-reference sweep misses a file. Mitigation: the implementing spec derives the sweep list from `git ls-files | xargs grep -l "check-workspace"`, classifies each hit operative/historical, and the lint gate (scoped to the operative path list, excluding frozen ADR bodies and changelog history) is the hard acceptance criterion.
- `workspace-status` and `experience-status` activation descriptions collide on "where am I with the design" phrasing. Mitigation: workspace-status is scoped to queue/initiative-level orientation; experience-status is scoped to design-thread artifacts. This difference is verified during evals authoring (Tier-A activation evals — automated tests checking whether a skill fires on the prompts it should and stays quiet on near-miss prompts it shouldn't — for each skill will include the other as a negative near-miss).
- The pack workflow guide drifts as new packs are added. Mitigation: the guide is framed at archetype level (episodic / sustained-project / sustained-derived / stateless), not skill-name level. Archetype membership changes slowly; skill names within an archetype don't affect the framework.

**Key assumptions (falsifiable):**
- All three experience-design writing skills write `type:` frontmatter — **verified** directly from `journey-mapping`, `user-flow`, and `service-blueprint` SKILL.md bodies.
- The argless-resume change is additive and doesn't break explicit spec invocations — **verified**: Step 0 is a conditional path; explicit arguments (a spec path passed to `work-loop`) bypass the argless-resume branch.

**Drawbacks:**
- The clean retire creates a brief window between merge and adopter update where any cached skill name `check-workspace` fails. Adopters running `check-workspace` from memory will hit a "skill not found" error. Mitigation: the rename is announced in the changelog entry; the new `workspace-status` description triggers include all the phrasing the old skill responded to.
- Adding `experience-status` before `design` is a valid workspace.toml type means existing files with `{type = "design"}` entries (hand-authored before this RFC) will be routed correctly, but the seed comment won't have listed it. Mitigation: B3 and B2 are implemented in the same PR.

## Evidence & prior art

**Repo:**
- `packs/governance-extras/.apm/skills/rfc-status/SKILL.md` — `*-status` orient precedent: read-only, groups by lifecycle state, triggers on "rfc status / show rfcs". The direct naming model for `workspace-status` and `experience-status`.
- `packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md` — `*-project-start` precedent; establishes that `*-status` is the natural complement for the sustained-project lifecycle.
- `packs/experience-design/.apm/skills/workspace-design/SKILL.md` — session arc vocabulary (Arrive → Orient → Work → Persist → Collaborate) confirmed; this is the design language Change D applies to pack authoring.
- `packs/experience-design/.apm/skills/journey-mapping/SKILL.md` — writes `type: customer-journey`; `user-flow/SKILL.md` writes `type: screen-flow`; `service-blueprint/SKILL.md` writes `type: service-blueprint`. All three confirmed; experience-status can derive thread state without a state file.
- `docs/rfc/0064-ini-001-ai-native-ecosystem.md` (Draft) — established the `check-workspace` name and the `type` enum for `shaping_queue` entries (`signal`, `research`, `shape`, `strategy`). Will be updated via direct body edit (Draft, not frozen).
- `docs/adr/0051-workspace-toml-toml-format-and-main-branch-coordination.md` (Accepted) — references `check-workspace` as a historical record of what shipped; body left as-is per CONVENTIONS §2 (frozen ADR bodies are never edited; a mechanical rename is not a decision reversal).
- `docs/adr/0053-product-strategy-pack-scope-and-discipline-boundaries.md` (Accepted) — same historical-record treatment as ADR-0051.
- RFC-0025 (`docs/rfc/0025-work-loop-light-mode-and-risk-based-escalation.md`) — no-new-skill precedent: description + body changes to `work-loop` are sufficient when no new activation surface is needed. (Status checked; filename confirmed.)
- RFC-0048 ("Scope-decouple and renames") — established the clean-retire rename approach for skill and pack renames: no aliases, no grace-period shims, operative references swept in the same PR.
- RFC-0055 ("RFC amendment and errata convention") — governs how to record corrections in an RFC body after it publishes. Referenced in this RFC's header because its mechanism applies to in-flight RFC-0064 (Amendments section); the ADR treatment follows the separate CONVENTIONS §2 rule (not RFC-0055).

**External:**
- Unix `git status` / `systemctl status` convention — the canonical `<resource> status` naming pattern for read-only orient commands. No citation needed; universally established.
- Plugin development guides (VS Code extensions, Figma plugins): surveyed via web search. None have a "pack workflow arc design" guide equivalent. The absence confirms this is a genuine gap; no external model to copy, so the guide must be authored from first principles using the existing session-arc vocabulary.

**Spike:** No spike needed. Both load-bearing assumptions verified directly from source (see Risks above).

## Open questions

None — all decisions resolved by research and confirmed in the pre-draft checkpoint.

## Follow-on artifacts

To be filled in on acceptance:

- ADR for the verb taxonomy and pack-type classification (episodic / sustained-project / sustained-derived / stateless).
- Spec: `docs/specs/spec-A-workspace-status-rename/` — Change A (rename sweep + verb taxonomy in author-a-skill.md).
- Spec: `docs/specs/spec-B-pack-status-skills/` — Change B (desk-research-project-status, experience-status, workspace.toml `design` type).
- Spec: `docs/specs/spec-C-workloop-argless-resume/` — Change C (description triggers + Step 0 wiring).
- Spec: `docs/specs/spec-D-pack-workflow-guide/` — Change D (new guide, CONTRIBUTING.md step 0, author-a-skill.md update).
