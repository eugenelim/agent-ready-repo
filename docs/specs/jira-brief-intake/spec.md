# Spec: jira-brief-intake

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0019 <!-- scoped this Jira intake adapter to the non-core atlassian pack and pinned the no-cross-repo-hub boundary (`Epic:`-pointer-only) -->
- **Brief:** none
- **Contract:** none
- **Shape:** integration <!-- composes the external Jira API + two sibling skills; ships choreography prose, not code, so the plan's `## Design (LLD)` is intentionally empty (the design lives in the Lifecycle prose, mirroring jira-defect-flow) -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Teams that run their delivery kanban-style in Jira keep the *what/why* of a
body of work in a Jira **epic and its child issues** (or a board / sprint /
JQL selection), not in a written product brief. The `receive-brief` skill is
the front door to spec-driven delivery, but it has no knowledge of Jira: it
ingests a brief, elicits what's missing, decomposes into specs, and hands each
to `new-spec` → `work-loop`. `jira-brief-intake` is the missing adapter
between the two. It pulls a Jira epic (plus its children), or a set of issues,
via the `jira` skill, maps the Jira-native shape onto a product brief — epic →
**Outcome**, child issues → **Shape B user stories** (`US-n`), epic key →
**`Epic:`** provenance pointer — writes a draft brief to
`docs/product/briefs/<slug>.md`, and hands off to `receive-brief` by name to
elicit gaps, decompose, and build. The user gets a single command —
*"turn PROJ-100 into specs"* — that turns a kanban epic into shippable work
without re-typing the brief.

It is choreography, not invention, in the exact mould of the pack's existing
`jira-defect-flow` (which maps a Jira defect onto the `bug-fix` skill). This
skill never writes a raw Jira REST call (the `jira` skill owns that) and never
reimplements elicitation, decomposition, or spec authoring (`receive-brief`
and its downstream own that). Its sole contribution is the Jira→brief mapping
that neither side can do alone.

## Boundaries

### Always do

- Pull all Jira data through the `jira` skill addressed **by name**, never by
  path and never via a raw REST call.
- Enumerate an epic's children with a **flavor-correct** child query through the
  `jira` skill's `search`: `parent = $KEY` (Cloud team-managed projects) and
  `"Epic Link" = $KEY` (Server/DC and company-managed Cloud). Try one and fall
  back to the other when it errors on a missing field or returns empty — never
  assume a single form, since `"Epic Link"` does not exist on team-managed Cloud
  and silently returns zero children there.
- Map a Jira epic's children onto **Shape B** user stories, tagging each `US-n`
  with its source Jira key so traceability is bidirectional
  (Jira key ↔ `US-n` ↔ spec AC).
- Stamp the source epic key into the brief's `Epic:` provenance pointer.
- Probe the `jira` skill as a Prerequisite before any read (`jira: check`):
  exit 0 → proceed; exit 2 → tell the user to authenticate via
  `credential-setup` themselves (interactive) and stop. Never dispatch reads
  into an auth failure. (`jira` is a hard runtime dependency — unlike
  `receive-brief`, there is no degraded path without it.)
- Hand off elicitation, decomposition, and spec authoring to `receive-brief`
  by name; it is the owner of those stages.
- Gracefully degrade: when `receive-brief` is not installed, inline a compact
  decompose-and-execute instruction the agent can act on directly, using the
  brief shape this skill carries.

### Ask first

- Before treating a **single non-epic issue with no children** as a brief —
  one issue is one feature, which is `new-spec` territory, not a multi-feature
  brief. Recommend `new-spec` and confirm before proceeding.
- Before writing over an existing `docs/product/briefs/<slug>.md` — confirm the
  slug and whether to merge or replace.

### Never do

- Never write a raw Jira REST call, or reimplement any `jira` subcommand,
  inside this skill.
- Never reimplement `receive-brief`'s Elicit stage — do not interrogate the
  user for missing Outcome/Scope yourself; that is `receive-brief`'s job (and
  its degraded-path instruction is a *handoff of that job to the agent*, not a
  reimplementation here).
- Never invoke any Jira **write** verb (`create-issue`, `update-issue`,
  `delete-issue`, `transition`, `comment`, `attach`). Intake is read-only.
- Never invent an Outcome, Scope, or story the Jira source does not support —
  surface the gap and let `receive-brief` elicit it.
- Never reference a sibling skill, or the brief template, by hardcoded path.
- Never modify the `core` pack (or any pack other than `atlassian`), and never
  add a pack dependency or new module — scope is the atlassian pack only, and
  this skill is pure choreography over skills that already exist.
- Never become a cross-repo coordination hub (RFC-0019 boundary): carry the
  Jira epic key as an `Epic:` provenance pointer only; do not reimplement a
  tracker or coordinate work above this repo's slice.

## Testing Strategy

This change ships **prose primitives** (a `SKILL.md`, a `manifest.json`,
reference docs) plus catalogue metadata — there is no new executable logic, so
no TDD-mode tasks.

- **Skill content + pack metadata: goal-based check.** The skill is well-formed
  and the pack still builds. Verified by `lint-packs`, `agentbundle validate`,
  `make build` (regenerates `.claude-plugin/marketplace.json`), and the
  agentbundle package pytest — the standing gate for a non-projected,
  user-scope-default pack.
- **Doc-drift: goal-based check.** Every place that enumerates the atlassian
  skill set names the new skill. Verified by `grep`.
- **Skill behavior: manual QA.** The skill is an agent-invoked artifact; its
  "happy path" is a reading-level dry-run — trace the documented procedure
  against a representative Jira epic and confirm each step dispatches a real
  `jira` subcommand that exists, produces a brief conforming to the carried
  shape, and hands off correctly in both the core-present and core-absent
  paths. Recorded in the plan's Manual verification.

## Acceptance Criteria

- [x] A `jira-brief-intake` skill exists at
  `packs/atlassian/.apm/skills/jira-brief-intake/` with a `SKILL.md` whose
  frontmatter `description` triggers on turning a Jira epic / board / set of
  issues into a product brief, and a `manifest.json` declaring its `jira` and
  `receive-brief` dependencies by name (runtime-by-name contract, `source` as
  install hint only).
- [x] The skill's procedure pulls Jira data **only** through named `jira`
  subcommands that exist in the `jira` skill (`get-issue`, `search`), and
  invokes **none** of the six Jira write verbs the Boundaries Never-do bans —
  `create-issue`, `update-issue`, `delete-issue`, `transition`, `comment`,
  `attach` — anywhere in the skill directory (`SKILL.md` **and**
  `references/`), including in "don't do this" examples.
- [x] The skill enumerates an epic's children with a flavor-correct child query
  — `parent = $KEY` **and** `"Epic Link" = $KEY`, with fallback between them —
  rather than a single hardcoded form, so it returns the children on
  team-managed Cloud as well as Server/DC and company-managed Cloud.
- [x] The skill maps an epic's children onto **Shape B** user stories, each
  `US-n` carrying its source Jira key, and stamps the epic key into the brief's
  `Epic:` pointer — the brief it writes conforms to the brief shape (the core
  template when present; the carried shape when core is absent).
- [x] The Jira-child → `US-n` mapping has a **pinned, single format** the
  downstream `Satisfies: US-n` trace can consume: each story line is
  `- **US-n.** (JIRA-KEY) <story text>`, where the Jira key is a parenthetical
  immediately after the id (this is the slot the brief template's bare
  `- **US-n.** …` line does not itself define), and `<story text>` is the
  child's summary reshaped into the template's *As a … I want … so that …*
  grammar **when the source supports it**, else the child summary carried
  verbatim for `receive-brief` to refine during Elicit — the skill never
  invents a role/benefit the child issue does not state.
- [x] The skill probes `jira` (`jira: check`) as a Prerequisite before any
  read and defines the exit-2 (unauthenticated) path — tell the user to run
  `credential-setup` themselves and stop — mirroring `jira-defect-flow`'s
  Prerequisites; `jira` is a hard dependency with no degraded path.
- [x] The skill hands off to `receive-brief` **by name** for Elicit /
  Decompose / Execute, and does **not** reimplement elicitation.
- [x] **Graceful degradation:** the skill's Prerequisites probe detects
  `receive-brief`'s absence (by-name dispatch unavailable / not installed), and
  in that case the `SKILL.md` carries a clearly-labelled core-absent branch
  holding (a) a compact brief shape and (b) a decompose-and-execute instruction
  the agent acts on directly — so the flow proceeds rather than stopping — and
  notes that downstream `new-spec` / `work-loop` may likewise be absent.
- [x] The skill recommends `new-spec` (and confirms before proceeding) when the
  input is a single non-epic issue with no children — it does not force a
  one-feature ticket into a brief.
- [x] Every doc that enumerates the atlassian skill set names the new skill:
  `packs/atlassian/README.md`, `docs/guides/atlassian/README.md`,
  `docs/guides/atlassian/reference/atlassian-skills.md` (a section mirroring
  the skill's frontmatter), `docs/guides/atlassian/explanation/atlassian-pack.md`,
  `docs/architecture/overview.md` (the per-pack skill table), and
  `docs/guides/README.md` (the pack-index row). The edit also keeps each doc's
  **count and role-grouping prose internally consistent** — two distinct kinds
  of count are corrected: the **total-skill count** ("seven skills" in the
  guides README → eight, or de-counted) and the **workflow/role-group counts**
  ("three workflow skills" in the pack README, "Three skills compose" in the
  explanation → four / four, or de-counted), with `jira-brief-intake` placed as
  a *composed/workflow* skill, not a CLI. Per the no-brittle-counts convention,
  de-count the prose where the edit already touches the line rather than
  perpetuating a hardcoded number.
- [x] `packs/atlassian/pack.toml` version is bumped and its `description`
  reflects the new workflow skill; `packs/atlassian/.claude-plugin/plugin.json`
  is kept in sync (version + description); and `.claude-plugin/marketplace.json`
  is regenerated by `make build` to match (no build-drift).
- [x] A `docs/product/changelog.md` `[Unreleased]` entry records the new skill.
- [x] The pack gate is green: `lint-packs`, `agentbundle validate`,
  `make build`, and the agentbundle package pytest all pass.

## Assumptions

- Technical: the `jira` skill exposes read verbs `get-issue` (with
  `--expand`/`--fields`) and `search` (JQL), which suffice to pull an epic, its
  children, and arbitrary issue selections (source: read
  `packs/atlassian/.apm/skills/jira/SKILL.md`).
- Technical: `receive-brief` is robust to a sparse/incomplete brief — its
  Elicit stage ingests a file and elicits missing Outcome/Scope rather than
  rejecting, so this skill need not validate brief completeness (source: read
  `packs/core/.apm/skills/receive-brief/SKILL.md` + its Shape B example,
  probe 2026-06-15).
- Technical: a Jira epic's child issues are the natural source for `receive-brief`
  Shape B stories, and the brief template's `Epic:` field is defined for exactly
  this kind of external-tracker provenance pointer (source: read
  `packs/core/seeds/docs/product/briefs/_template.md`).
- Process: atlassian is a user-scope-default pack, not projected into this
  repo's working tree; adding a skill + bumping its version drifts
  `.claude-plugin/marketplace.json`, so the gate is `lint-packs` + `validate` +
  `build` + package pytest, not `build-self`/`pre-pr` (source: project memory +
  `packs/atlassian/pack.toml`).
- Product: a new composition skill (not a progressive-disclosure mode bolted
  onto the `jira` primitive) is the chosen shape, mirroring `jira-defect-flow`
  (source: user confirmation 2026-06-15).
- Product: scope stays in the atlassian pack; `receive-brief` (core) is not
  modified (source: user confirmation 2026-06-15).
- Process: RFC-0019 (Accepted) explicitly anticipated this Jira intake adapter
  living in the non-core atlassian pack (`jira-defect-flow` intake precedent;
  Jira-specific work fails core's Universal principle) and pinned the
  no-cross-repo-hub boundary the skill honours via the `Epic:` pointer (source:
  read `docs/rfc/0019-product-brief-intake.md` §Decision 1 / :149, probe
  2026-06-15).
