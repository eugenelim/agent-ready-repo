# Spec: m5-jira-align-brief-intake

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 M5 <!-- 1-way intake only; configuration-guided field mapping; generic portable sync explicitly not a goal (Known Unknowns — Unknowable) -->
- **Brief:** none
- **Contract:** none
- **Shape:** integration <!-- composes the jira-align credentialed CLI + receive-brief; ships choreography prose, not code; plan's `## Design (LLD)` intentionally empty -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Teams that plan delivery at the program level in **Jira Align** keep the
*what/why* of a body of work in a Jira Align **Feature** (and its child
stories, tasks, and defects), not in a written product brief. The
`receive-brief` skill is the front door to spec-driven delivery, but it
has no knowledge of Jira Align: it ingests a brief, elicits what's missing,
decomposes into specs, and hands each to `new-spec` → `work-loop`.
`jira-align-brief-intake` is the missing adapter between the two.

It pulls a Jira Align Feature (plus its child stories, tasks, and defects)
via the `jira-align` skill, maps the Jira Align–native shape onto a product
brief — Feature title/description → **Outcome**, child items → **Shape B
user stories** (`US-n`), Feature ID → **`Epic:`** provenance pointer —
writes a draft brief to `docs/product/briefs/<slug>.md`, and hands off to
`receive-brief` by name to elicit gaps, decompose, and build.

The mapping is **configuration-guided**: Jira Align workflow state names and
Program Increment cadences are org-specific. The skill carries a reference
table (`references/field-mapping.md`) the adopter annotates with their
instance's vocabulary before first use. This is the boundary RFC-0064 M5
drew explicitly — a generic portable sync is not a goal, and the 1-way
intake direction is intentional.

Like `jira-brief-intake` for Jira epics and `jira-defect-flow` for Jira
defects, this skill is choreography, not invention. It never writes a raw
Jira Align REST call (the `jira-align` skill owns that) and never
reimplements elicitation, decomposition, or spec authoring (`receive-brief`
and its downstream own that). Its sole contribution is the Jira Align →
brief mapping that neither side can do alone.

## Boundaries

### Always do

- Pull all Jira Align data through the `jira-align` skill addressed **by
  name**, never by path and never via a raw REST call.
- Fetch the Feature using `jira-align get features <ID> --expand
  ownerUser,milestones` to capture ownership and PI context.
- Enumerate a Feature's children by resource type with
  `jira-align list stories --filter "featureID eq <ID>"` (and optionally
  `list tasks` / `list defects` with the same filter) — never assume all
  children are stories; surface whichever types are present.
- Map Feature fields onto the brief using the config-guided reference table
  in `references/field-mapping.md`: Feature title → brief heading; Feature
  description + notes → Outcome; Feature ID → `Epic:` provenance pointer
  (full URL: `<JIRAALIGN_BASE_URL>/features/<ID>`); children → Shape B
  user stories.
- Tag each `US-n` with its Jira Align resource ID in parentheses so
  traceability is bidirectional (Jira Align ID ↔ `US-n` ↔ spec AC). Format:
  `- **US-n.** (stories/<id>) <story text>` (substitute `tasks/` or
  `defects/` per resource type).
- Stamp the source Feature ID into the brief's `Epic:` provenance pointer.
- Probe the `jira-align` skill before any read (`jira-align: check`): exit
  0 → proceed; exit 2 → tell the user to authenticate via `credential-setup`
  themselves (interactive) and stop. (`jira-align` is a hard runtime
  dependency — there is no degraded path without it.)
- Hand off elicitation, decomposition, and spec authoring to `receive-brief`
  by name; it is the owner of those stages.
- Gracefully degrade: when `receive-brief` is not installed, inline a
  compact decompose-and-execute instruction the agent can act on directly,
  using the brief shape the skill carries.
- Tell the adopter to customise `references/field-mapping.md` for their
  instance's workflow state vocabulary and PI cadence **before first use** —
  surface this as a one-time setup step, not a blocker.

### Ask first

- Before writing over an existing `docs/product/briefs/<slug>.md` — confirm
  the slug and whether to merge or replace.
- Before treating a **single Feature with no children** as a brief — a
  Feature with no child items is unusually thin; confirm the user's intent
  and recommend checking for subtasks or related stories before proceeding.

### Never do

- Never write a raw Jira Align REST call, or reimplement any `jira-align`
  subcommand, inside this skill.
- Never invoke any Jira Align **write** verb (`create`, `update`, `delete`,
  `raw` with a mutating method). Intake is **read-only** (`check`, `get`,
  `list`, `search` only).
- Never reimplement `receive-brief`'s Elicit stage — do not interrogate the
  user for missing Outcome/Scope; that is `receive-brief`'s job (and its
  degraded-path instruction is a *handoff of that job to the agent*, not a
  reimplementation here).
- Never invent an Outcome, Scope, or story the Jira Align source does not
  support — surface the gap and let `receive-brief` elicit it.
- Never reference a sibling skill, or the brief template, by hardcoded path.
- Never modify the `core` pack (or any pack other than `atlassian`), and
  never add a pack dependency or new module — scope is the atlassian pack
  only, and this skill is pure choreography over skills that already exist.
- Never become a cross-repo coordination hub: carry the Feature ID as an
  `Epic:` provenance pointer only; do not reimplement a tracker or
  coordinate work above this repo's slice (RFC-0064 boundary, same as
  `jira-brief-intake`).
- Never claim generic portability or attempt to produce a field mapping that
  works across all Jira Align instances without adopter configuration —
  RFC-0064 explicitly designates this Unknowable.

## Testing Strategy

This change ships **prose primitives** (a `SKILL.md`, a `manifest.json`,
a `references/field-mapping.md`) plus catalogue metadata — there is no new
executable logic, so no TDD-mode tasks.

- **Skill content + pack metadata: goal-based check.** The skill is
  well-formed and the pack still builds. Verified by `lint-packs`,
  `agentbundle validate`, `make build` (regenerates
  `.claude-plugin/marketplace.json`), and the agentbundle package pytest —
  the standing gate for a non-projected, user-scope-default pack.
- **Doc-drift: goal-based check.** Every place that enumerates the atlassian
  skill set names the new skill. Verified by `grep`.
- **Skill behavior: manual QA.** The skill is an agent-invoked artifact; its
  "happy path" is a reading-level dry-run — trace the documented procedure
  against a representative Jira Align Feature and confirm each step
  dispatches a real `jira-align` subcommand that exists, produces a brief
  conforming to the carried shape, and hands off correctly in both the
  core-present and core-absent paths. Recorded in the plan's Manual
  verification.

## Acceptance Criteria

- [x] A `jira-align-brief-intake` skill exists at
  `packs/atlassian/.apm/skills/jira-align-brief-intake/` with a `SKILL.md`
  whose frontmatter `description` triggers on turning a Jira Align Feature
  into a product brief, and a `manifest.json` declaring its `jira-align` and
  `receive-brief` dependencies by name (runtime-by-name contract, `source`
  as install hint only).
- [x] The skill's procedure pulls Jira Align data **only** through named
  `jira-align` subcommands that exist in the `jira-align` skill (`check`,
  `get`, `list`, `search`), and invokes **none** of the write verbs
  (`create`, `update`, `delete`, or `raw` with a mutating method) anywhere
  in the skill directory (`SKILL.md` **and** `references/`) — including in
  "don't do this" examples.
- [x] The skill fetches the Feature with
  `jira-align get features <ID> --expand ownerUser,milestones` and enumerates
  its children by resource type (`list stories`, `list tasks`, `list defects`)
  using `--filter "featureID eq <ID>"` for each — never assuming all children
  are stories, never using a Feature-type–specific workaround that would break
  for tasks or defects.
- [x] The skill maps Feature fields onto the brief using the config-guided
  reference table in `references/field-mapping.md`: Feature title → brief
  heading; Feature description + notes → Outcome; Feature ID → `Epic:`
  pointer (full URL); children → Shape B user stories.
- [x] The Jira Align child → `US-n` mapping has a **pinned, single format**
  the downstream `Satisfies: US-n` trace can consume: each story line is
  `- **US-n.** (<resource-type>/<id>) <story text>`, where the resource type
  and ID are a parenthetical immediately after the id (e.g.
  `(stories/4521)`) and `<story text>` is the child's title reshaped into
  the template's *As a … I want … so that …* grammar **when the source
  supports it**, else the child title carried verbatim for `receive-brief`
  to refine during Elicit — the skill never invents a role/benefit the child
  item does not state.
- [x] The skill probes `jira-align` (`jira-align: check`) as a Prerequisite
  before any read and defines the exit-2 (unauthenticated) path — tell the
  user to run `credential-setup` themselves and stop — mirroring
  `jira-defect-flow`'s and `jira-brief-intake`'s Prerequisites; `jira-align`
  is a hard dependency with no degraded path.
- [x] The skill hands off to `receive-brief` **by name** for Elicit /
  Decompose / Execute, and does **not** reimplement elicitation.
- [x] **Graceful degradation:** the skill's Prerequisites probe detects
  `receive-brief`'s absence (by-name dispatch unavailable / not installed),
  and in that case the `SKILL.md` carries a clearly-labelled core-absent
  branch holding (a) a compact brief shape and (b) a decompose-and-execute
  instruction the agent acts on directly — so the flow proceeds rather than
  stopping — and notes that downstream `new-spec` / `work-loop` may likewise
  be absent.
- [x] The skill carries a `references/field-mapping.md` that documents: (a)
  a standard Jira Align Feature field → brief field mapping table; (b) a
  clearly-labelled **"Customize for your org"** section on workflow state
  vocabulary (adopter fills in their instance's state names); (c) a section
  on PI / Program Increment mapping with common naming patterns; (d) the
  child → `US-n` provenance format; (e) a note that this mapping must be
  reviewed and annotated before first use on a new Jira Align instance.
- [x] Every doc that enumerates the atlassian skill set names the new skill:
  `packs/atlassian/README.md`, `docs/guides/atlassian/README.md`,
  `docs/guides/atlassian/reference/atlassian-skills.md` (a section mirroring
  the skill's frontmatter), `docs/guides/atlassian/explanation/atlassian-pack.md`,
  and `docs/architecture/overview.md` (the per-pack skill table). Each doc's
  count and role-grouping prose is kept internally consistent; hardcoded
  numbers are de-counted per the no-brittle-counts convention where the edit
  already touches the line.
- [x] `packs/atlassian/pack.toml` version is bumped (0.3.2 → 0.4.0) and its
  `description` reflects the new workflow skill; the skill is added to
  `[pack.evals].skills`; `packs/atlassian/.claude-plugin/plugin.json` is
  kept in sync (version + description); and `.claude-plugin/marketplace.json`
  is regenerated by `make build` to match (no build-drift).
- [x] A `docs/product/changelog.md` `[Unreleased]` entry records the new
  skill.
- [x] The pack gate is green: `lint-packs`, `agentbundle validate`,
  `make build`, and the agentbundle package pytest all pass.

## Assumptions

- Technical: the `jira-align` skill exposes read verbs `check`, `get`,
  `list`, and `search` against the `features`, `stories`, `tasks`, and
  `defects` resources, and these suffice to pull a Feature, its children,
  and ownership/PI context via `--expand` (source: read
  `packs/atlassian/.apm/skills/jira-align/SKILL.md`, probe 2026-07-21).
- Technical: Jira Align Feature responses include `state` (workflow state
  string), `acceptanceCriteria` (free-text ACs), and `points` (story
  points) as standard REST API 2.0 fields. These are adopted from the
  Jira Align field model and are expected on most instances; custom
  instances may omit or rename them. When absent, the skill's missing-
  field handling (leave placeholder, skip, note) applies per
  `references/field-mapping.md §What to do when fields are missing`
  (source: Jira Align REST API 2.0 documentation; adopter-verified per
  their instance's Swagger UI at `<base_url>/rest/align/api/docs`).
- Technical: Jira Align's OData `$filter` supports `featureID eq <ID>` for
  stories, tasks, and defects, making child enumeration uniform across
  resource types (source: jira-align SKILL.md Step 3 / OData filter table,
  probe 2026-07-21).
- Technical: `receive-brief` is robust to a sparse/incomplete brief — its
  Elicit stage ingests a file and elicits missing Outcome/Scope rather than
  rejecting (source: read `packs/core/.apm/skills/receive-brief/SKILL.md`,
  same assumption as `jira-brief-intake`).
- Technical: a Jira Align Feature's children are the natural source for
  `receive-brief` Shape B stories, and the brief template's `Epic:` field
  is defined for exactly this kind of external-tracker provenance pointer
  (source: read `packs/core/seeds/docs/product/briefs/_template.md`).
- Process: atlassian is a user-scope-default pack; adding a skill + bumping
  its version drifts `.claude-plugin/marketplace.json`, so the gate is
  `lint-packs` + `validate` + `build` + package pytest, not `build-self`/
  `pre-pr` (source: project memory + `packs/atlassian/pack.toml`).
- Product: a new composition skill (not a mode bolted onto `jira-align`) is
  the chosen shape — mirrors `jira-brief-intake`'s precedent for Jira and is
  the pattern the RFC-0064 M5 AC names explicitly.
- Product: scope stays in the atlassian pack; `receive-brief` (core) is not
  modified; 1-way intake only — no write verbs, no delta sync, no PI
  cadence mutation (source: RFC-0064 M5 AC + Known Unknowns — Unknowable).
- Product: RFC-0064 intentionally scopes this to Jira Align Feature → brief
  with configuration-guided field mapping; the integration surface is
  org-specific (custom workflow state names, PI cadences), and a generic
  portable sync is impossible — this is the Unknowable boundary the RFC drew
  (source: RFC-0064 Known Unknowns section, probe 2026-07-21).
