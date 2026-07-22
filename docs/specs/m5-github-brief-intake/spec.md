# Spec: m5-github-brief-intake

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0019
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
changelog. This applies to the spec body only — `plan.md` keeps its own
changelog of how the approach evolved. -->

## Objective

Teams that plan work in GitHub organise multi-feature bodies of work as
**Milestones** — a milestone groups related issues under a theme, with a title,
optional description, and due date. The `receive-brief` skill is the front door
to spec-driven delivery but has no knowledge of GitHub: it ingests a brief,
elicits what's missing, decomposes into specs, and hands each to
`new-spec` → `work-loop`. `github-brief-intake` is the missing adapter.

The skill pulls a GitHub Milestone and its issues via the `gh` CLI, maps the
GitHub-native shape onto a product brief — milestone title → **Outcome draft**,
open and closed issues → **Shape B user stories** (`US-n` tagged with the
source issue number), milestone URL → **`Epic:`** provenance pointer — writes a
draft brief to `docs/product/briefs/<slug>.md`, and hands off to `receive-brief`
by name to elicit gaps, decompose, and build. A user who types *"turn our Q3
milestone into specs"* gets the full spec-driven intake pipeline without
re-keying anything.

This is choreography in the mould of the atlassian pack's `jira-brief-intake`,
with two deliberate departures from that precedent: (1) it stands up a new
`github` pack rather than adding a skill to an existing pack, because no GitHub
pack exists; (2) it permits bounded post-intake write-back (comment / label /
close — never body edits), whereas `jira-brief-intake` is strictly read-only.
The skill invokes `gh` CLI commands directly (no separate `github` skill
primitive exists), owns only the GitHub Milestone→brief mapping that neither
side of the handoff can do alone, and ships in a new `github` pack alongside a
how-to guide (P4 phase-slice doctrine: tooling and guide ship together).

## Boundaries

### Always do

- Pull all GitHub data through `gh` CLI commands: `gh api
  repos/{owner}/{repo}/milestones` for milestone discovery and
  `gh issue list --milestone <title-or-number> --state all --json
  number,title,body,labels,url,state` for issue enumeration. Never hand-roll a
  raw GitHub REST API call inside the skill body.
- Enumerate **all** milestone issues (`--state all`) so closed issues are
  included in the story map — they represent work scoped to the brief even if
  already done.
- Map a milestone's issues onto **Shape B** user stories, each `US-n` carrying
  its source issue number (`#NNN`) in the pinned single format:
  `- **US-n.** (#NNN) <story text>`, where `<story text>` uses
  *As a … I want … so that …* grammar when the issue title supports it, else
  the title verbatim for `receive-brief` to refine. The skill never invents a
  role or benefit the issue does not state.
- Stamp the milestone's `html_url` into the brief's `Epic:` provenance pointer.
- Probe `gh auth status` before any read.
  - **Authenticated:** proceed normally for both public and private repos.
  - **Unauthenticated, read succeeds:** public repo accessible anonymously —
    note the unauthenticated posture in the brief's Assumptions section and
    continue.
  - **Unauthenticated, read returns 404:** GitHub returns 404 for both private
    repos and nonexistent repos when called anonymously; the two are
    indistinguishable. Surface an ambiguous-error message: "Repo or milestone
    not found — if this is a private repo, run `gh auth login` and retry; if it
    is public, check the owner/repo/milestone." Stop and do not retry.
  Never dispatch further reads after a 404 or other non-success response.
- Confirm the slug with the user before writing to
  `docs/product/briefs/<slug>.md`; check whether a file already exists at that
  path and require explicit confirmation to overwrite.
- Hand off elicitation, decomposition, and spec authoring to `receive-brief`
  **by name**; it is the owner of those stages.
- Gracefully degrade when `receive-brief` is not installed: carry a clearly-
  labelled absent-path branch that holds (a) a compact brief shape and (b) a
  decompose-and-execute instruction the agent acts on directly, so the flow
  continues rather than stopping.

### Ask first

- Before treating a **single issue without a milestone** as a brief — one issue
  is a feature, which is `new-spec` territory. Recommend `new-spec` and confirm
  before proceeding.
- Before any **post-intake write-back** (commenting on, labelling, or closing
  issues) — offer it after the brief is written and confirmed; never apply
  without explicit user confirmation per action type.
- Before using a **label filter or ad-hoc issue list** rather than a named
  milestone as the source — confirm the grouping is intentional.

### Never do

- Never edit the body of a GitHub issue. Post-intake write-back is limited to
  comments, labels, and close status — issue body text is immutable for this
  skill.
- Never reimplement `receive-brief`'s Elicit stage. The degraded-path branch
  hands the job to the agent via an instruction; it does not interrogate the
  user for Outcome or Scope inline.
- Never invent an Outcome, Scope, or story the milestone or its issues do not
  support — surface the gap and let `receive-brief` elicit it.
- Never reference a skill or the brief template by hardcoded file path; address
  `receive-brief` and `new-spec` by name only.
- Never become a cross-repo coordination hub (RFC-0019 boundary): carry the
  milestone URL as `Epic:` only; do not reimplement a tracker or coordinate
  work above this repo's slice.
- Never modify the `core` pack or any pack other than `github`, and never add a
  cross-pack code import or new Python/pack dependency. The `gh` CLI is a
  system tool (environmental assumption); it owns its own auth and credential
  handling — the skill carries no credentialed-skill frontmatter, matching the
  `jira-brief-intake` precedent (which also delegates to its credentialed
  sibling and carries no such flags).

## Testing Strategy

This change ships **prose primitives** (a `SKILL.md`, a `manifest.json`, a
how-to guide) and catalogue metadata — no new executable logic, so no TDD-mode
tasks.

- **Skill content + pack metadata: goal-based check.** The skill is well-formed
  and the pack builds. Verified by `lint-packs`, `agentbundle validate`,
  `make build` (regenerates `.claude-plugin/marketplace.json`), and the
  agentbundle package pytest — the standing gate for a user-scope-default,
  non-projected pack.
- **Doc-drift: goal-based check.** Every place that enumerates packs names the
  new `github` pack, and the guide appears in the guides index. Verified by
  `grep` and `ls`.
- **Skill behavior: manual QA.** Reading-level dry-run of `SKILL.md` against a
  representative milestone (a real repo with a milestone containing 3+ issues):
  confirm each `gh` command exists in the installed CLI and produces the expected
  field shape; confirm the produced brief conforms to Shape B (milestone title →
  Outcome draft, issues → `US-n #NNN`, milestone URL → `Epic:`); confirm
  hand-off to `receive-brief` by name in both the present and absent paths;
  confirm the auth-degradation path and the single-issue redirect. Results
  recorded under `notes/`.

## Acceptance Criteria

### Skill

- [x] **AC-S1.** A `github-brief-intake` skill exists at
  `packs/github/.apm/skills/github-brief-intake/` with a `SKILL.md` whose
  frontmatter `description` triggers on turning a GitHub milestone (or a
  milestone-filtered group of issues) into a product brief, and a `manifest.json`
  declaring its `receive-brief` dependency by name in `deps.skills` and `gh`
  in `deps.system` (no credentialed-skill frontmatter — `gh` owns its own auth,
  matching the `jira-brief-intake` precedent).
- [x] **AC-S2.** The skill pulls all GitHub data through `gh` CLI commands only:
  `gh api repos/{owner}/{repo}/milestones` for milestone discovery and
  `gh issue list --repo {owner}/{repo} --milestone <title-or-number> --state all --json
  number,title,body,labels,url,state` for issue enumeration (`state` annotates
  closed issues; `body` and `labels` are carried for `receive-brief` to use
  during Elicit; `url` enables per-issue deep-link tracing) — no raw REST calls
  implemented inline.
- [x] **AC-S3.** The skill probes `gh auth status` before any read. The
  `SKILL.md` procedure explicitly distinguishes three unauthenticated outcomes:
  (a) read succeeds → public repo, note unauthenticated posture and continue;
  (b) read returns 404 → ambiguous (private or not-found), surface the verbatim
  message "Repo or milestone not found — if this is a private repo, run
  `gh auth login` and retry; if it is public, check the owner/repo/milestone."
  and stop; (c) authenticated → proceed normally. The ambiguous-404 message is
  named verbatim in the SKILL.md procedure, not left to agent interpretation.
- [x] **AC-S4.** The skill maps a milestone's issues onto Shape B user stories
  in the pinned format `- **US-n.** (#NNN) <story text>`, with closed issues
  annotated `[closed]` using the `state` field (`"CLOSED"` uppercase, as
  returned by `gh issue list`), and the milestone's `html_url` in the brief's
  `Epic:` pointer.
- [x] **AC-S5.** The skill recommends `new-spec` (and confirms before
  proceeding) when the input is a single issue with no milestone container.
- [x] **AC-S6.** The skill hands off to `receive-brief` **by name** for Elicit
  / Decompose / Execute and does not reimplement elicitation.
- [x] **AC-S7.** **Graceful degradation:** when `receive-brief` is absent, the
  `SKILL.md` carries a clearly-labelled absent-path branch holding (a) a compact
  brief shape and (b) a decompose-and-execute instruction the agent acts on
  directly, and notes that downstream `new-spec` and `work-loop` may likewise be
  absent.
- [x] **AC-S8.** **Post-intake write-back:** after the brief is written and
  confirmed, the skill offers (does not require) to comment on, label, or close
  the milestone's issues — each action type requires separate explicit user
  confirmation; the skill never edits issue bodies.
- [x] **AC-S9.** **Empty milestone:** when a milestone contains zero issues, the
  skill produces a brief with an empty Shape B section and an elicit note
  instructing `receive-brief` to gather user stories — it does not abort or
  error on an empty issue set.

### Pack

- [x] A `github` pack exists at `packs/github/` with `pack.toml`
  (`name = "github"`, `default-scope = "user"`, a description naming the
  skill), `README.md`, and `.claude-plugin/plugin.json` — following the
  atlassian pack's layout as the structural precedent.
- [x] Root `.claude-plugin/marketplace.json` is regenerated by `make build`
  (aggregate; per-pack source is `plugin.json` only — no per-pack `marketplace.json`).
- [x] Pack gate is green: `lint-packs`, `agentbundle validate`, `make build`,
  and the agentbundle package pytest all pass.

### Guide

- [x] `docs/guides/github/README.md` exists and lists the how-to guide.
- [x] `docs/guides/github/how-to/intake-a-github-milestone-as-a-brief.md`
  covers: prerequisites (`gh` CLI installed + `gh auth status`), full intake
  flow (select milestone → enumerate issues → review story map → confirm slug →
  write brief → hand off to `receive-brief`), public-repo auth-degradation path,
  single-issue → `new-spec` redirect, and optional post-intake write-back
  (comment / label / close).
- [x] `docs/guides/README.md` lists the new `github` guide pack row.

### Cross-cutting docs

- [x] `docs/architecture/overview.md` pack table includes a `github` row naming
  `github-brief-intake` as the pack's skill.
- [x] `docs/product/changelog.md` `[Unreleased]` entry records the new `github`
  pack and `github-brief-intake` skill.

## Assumptions

- Technical: `gh` CLI v2.96.0 available; GitHub API accessible at 5000 req/h
  rate limit (probe: `gh --version` + `gh api rate_limit`, 2026-07-22)
- Technical: `gh milestone` is not a native subcommand; milestones are read via
  `gh api repos/{owner}/{repo}/milestones`; issues per milestone via
  `gh issue list --milestone <title-or-number>` (probe: `gh milestone --help` +
  `gh issue list --help`, 2026-07-22)
- Technical: No existing `github` pack — 17 packs confirmed, none named `github`
  (probe: `ls packs/`, 2026-07-22)
- Technical: Brief template's `Epic:` field accepts a URL as a free-form
  external coordinator pointer (probe:
  `packs/core/seeds/docs/product/briefs/_template.md`, 2026-07-22)
- Technical: GitHub Issue = leaf/spec level; GitHub Milestone = brief level, per
  tracker-projection.md where `spec / slice (leaf) → Linear Issue` and GitHub
  Issue maps to the same leaf level (probe:
  `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`,
  2026-07-22)
- Technical: Pure prose-choreography — SKILL.md + manifest.json + guide, no
  executable code; same shape as `jira-brief-intake` (probe:
  `docs/specs/jira-brief-intake/plan.md`, 2026-07-22)
- Process: RFC-0019 constrains tracker adapters: own-the-repo-slice, `Epic:`
  pointer only, hand off to `receive-brief`; RFC-0019 contains no read-only
  mandate (probe: `docs/rfc/0019-product-brief-intake.md`, 2026-07-22)
- Process: read-only baseline follows `jira-brief-intake` precedent (its own
  spec choice), not RFC-0019; bounded write-back is a deliberate departure from
  that precedent (source: user confirmation 2026-07-22)
- Process: workspace.toml P4 doctrine — each tracker spec ships with its guide
  slice in the same PR (probe: workspace.toml P4 comment, 2026-07-22)
- Process: `github` pack follows atlassian pack shape — user-scope-default,
  non-projected; gate is `lint-packs` + `validate` + `build` + package pytest
  (probe: `packs/atlassian/pack.toml` + `docs/specs/jira-brief-intake/plan.md`,
  2026-07-22)
- Product: New `github` pack (not in core or atlassian)
  (source: user confirmation 2026-07-22)
- Product: Auth posture: graceful degradation for public repos; clear error +
  `gh auth login` instruction for private repos
  (source: user confirmation 2026-07-22)
- Product: Milestone = brief level; single issue without milestone = `new-spec`
  territory (source: tracker-projection.md + user confirmation 2026-07-22)
- Product: Post-intake write-back (comment / label / close) permitted; editing
  issue body never permitted (source: user confirmation 2026-07-22)
