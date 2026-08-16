# Spec: m6-astro-work-index

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 Errata #8 (P5 Adopt); RFC-0083; ADR-0077; ADR-0078; adopter-persona research; platform-site aesthetic direction
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A PM or product lead can open a static `/work/` page and answer what is active,
what is ready, what needs attention, and what upstream shaping or brief work is
waiting without learning the repository's TOML structure. The page is a
read-only presentation of the existing `workspace-status` contract and the
canonical artifacts indexed by `workspace.toml`; it creates no Project record,
workflow, lifecycle, or routing rule. Display labels come only from fields that
the workspace contract already classifies as display-only.

The page follows the platform site's dominant “precision authority” aesthetic:
current state and, for attention findings, the canonical next safe action
appear before identifiers and supporting detail. It is a build-time repository snapshot, not the live dispatch,
telemetry, mutation, or exception-management control plane reserved for the
separate control-plane initiative.

## Boundaries

### Always do

- During the Astro build, invoke the production workspace-status CLI under the
  exact executable, root, and argv contract in AC1; treat its canonical
  classification, lifecycle, findings, and finding-level next actions as
  authoritative.
- Use `workspace.toml` directly only to join existing display-only initiative
  names, milestones, and five-field entry summaries onto exact CLI identities;
  direct TOML data never changes membership, readiness, blocking, dependencies,
  or next actions.
- Separate executable work, shaping/context, briefs, and repository backlog in
  the information hierarchy so a PM cannot mistake one class for another.
- Fail the build on CLI failure, unsupported schema version, malformed
  projection, or an ambiguous display join; never publish a partial status page.
- Use existing Astro layouts, `--ds-*` tokens, base-path helpers, semantic HTML,
  and the WCAG 2.2 AA floor.

### Ask first

- Any change to the workspace-status JSON contract, workspace-entry schema, or
  work-intake classification/materialization rules.
- Any navigation restructuring beyond adding one base-aware `Work` entry.
- Any client-side filtering, editing, API, authentication, telemetry, live
  refresh, or remote data source.

### Never do

- Create or restore `docs/product/projects/`, a Project artifact, Project schema,
  Project template, or Project lifecycle.
- Parse `workspace.toml` or artifact prose to reimplement routing, dependency
  evaluation, reconciliation, or dispatchability in TypeScript or Python.
- Let comments, display summaries, list order, or presentation grouping alter a
  canonical workspace-status result.
- Add a user-triggered workflow, server runtime, client framework, dependency,
  content database, top-level directory, or write-back path.
- Create a dependency on `m6-enterprise-rollout-playbook` or modify `ini-008`,
  work-intake files, workspace schemas, workspace-routing code, or RFC-0079's
  unrelated codebase project indexes.

## Testing Strategy

- **Projection boundary: TDD.** Python tests prove the build adapter accepts
  schema-version-1 workspace-status output, joins only existing display fields,
  preserves canonical classifications and finding-level next actions, filters
  attention work without reclassifying it, and fails closed on CLI/schema/join
  errors.
- **Static page construction: TDD plus goal-based checks.** Component tests cover
  populated and empty projections; the Astro build emits `/work/index.html`,
  invokes the real production status CLI, and ships no runtime JavaScript or new
  dependency.
- **PM comprehension and quality floor: visual/manual QA.** The rendered page
  answers the four business questions below at desktop and 375 px widths, has no
  horizontal body scroll, remains keyboard-readable, and receives no severity-3+
  design-review finding against the platform site's precision-authority and
  staged-revelation direction.

## Analytical surface contract

### Domain model

- **Initiative:** stable workspace identifier plus display-only name and current
  milestone.
- **Work item:** canonical artifact identity, initiative membership, lifecycle
  collection, display summary, dispatchability, findings, and any next safe
  action carried by a finding.
- **Upstream context:** shaping items, brief-queue membership, and repository
  backlog entries; these remain visually distinct from executable work.
- **Relationships:** an initiative contains indexed artifacts; workspace-status
  classifies each artifact; findings explain why an item needs attention.
- **Actions:** scan current state, identify the next review, and use the displayed
  canonical path or next action in the repository's existing workflow.

### Business questions

1. A PM needs to know which work is active or ready so they can focus the next
   delivery conversation.
2. A PM needs to know which queued or active work needs attention and why so they
   can take the smallest safe next action.
3. A PM needs to distinguish shaping, briefs, and backlog from executable work so
   they do not interpret upstream context as delivery-ready scope.
4. A PM needs an explicit empty or failed-snapshot state so they do not mistake
   missing data for a healthy or loading workspace.

### Hierarchy and states

- **Tier 1:** counts for active work, ready work, attention-needed work, ready
  briefs, shaping/context, and open repository backlog.
- **Tier 2:** initiative sections with active, ready, and attention worklists;
  each item leads with its display summary and status.
- **Tier 3:** canonical path for every work item; stable finding code and next
  safe action only for attention items whose CLI findings supply them; followed
  by separate shaping, brief, and backlog detail.
- **Empty:** state that no active, ready, or attention work exists; point to
  `work-intake` for creating or routing work and `workspace-status` for the
  operational view. No Project creation guidance appears.
- **Error:** the build fails with a confined, actionable error; the public page
  never silently omits malformed or unavailable state.
- **Populated:** active first, then ready, then attention-needed; initiatives and
  items are ordered deterministically by canonical identifier after status.
- **Loading and stale:** not applicable to the static build-time snapshot; no
  spinner, live-status claim, or freshness timestamp is shown.

## Acceptance Criteria

- [x] **AC1.** The build-time adapter resolves `<repo>` from its checked-in location, proves the resolved CLI and `workspace.toml` paths remain under that root, and invokes the shipped CLI with exact argv `[sys.executable, "<repo>/packs/core/.apm/skills/workspace-status/scripts/workspace_status.py", "status", "--root", "<repo>"]`. It performs one attempt with explicit timeout, stdout/stderr byte caps, JSON byte/item/depth caps, and no retries; non-zero exit, timeout, truncated or invalid JSON, non-finite JSON value, unsupported `schema_version`, missing required collection, path-resolution error, or ambiguous identity aborts the build with a bounded diagnostic containing no traceback, absolute path, stderr payload, or raw repository prose.
- [x] **AC2.** Lifecycle, dispatchability, and findings in the page projection are copied from the CLI result without recomputation. A next action appears only when supplied by a finding and is copied from that finding; the page does not synthesize next actions for ready or active items. Fixtures prove comment, summary, and array-order changes cannot change those values.
- [x] **AC3.** Direct `workspace.toml` reading is limited to initiative `name`/`milestone` and canonical entry `summary` display joins keyed by exact initiative, collection, and path. Every admitted identity is a normalized repository-relative path with no absolute/drive-qualified form or dot segment; every filesystem target is realpath-confined under `<repo>` after symlink resolution, and symlink escape/loop or resolution failure aborts the build. A canonically classified `missing_artifact` attention item may name an absent leaf only when its nearest existing ancestor is confined under `<repo>`. Display values cannot create, remove, reorder by priority, unblock, or reclassify an item.
- [x] **AC4.** The attention worklist includes only canonical `work.queue` or `work.active` evaluations carrying findings; legacy shipped memberships remain available to workspace-status reconciliation but do not flood the PM delivery worklist.
- [x] **AC5.** `/work/` is emitted by the static Astro build, follows established layout/token/base-path conventions, and ships no runtime JavaScript, server route, network request, dependency, or package-lock change. Every repository-derived string renders through Astro text-node/contextual escaping; `set:html`, raw HTML, or equivalent bypasses are forbidden, and script/markup payload fixtures remain inert visible text.
- [x] **AC6.** The populated page presents the six Tier-1 counts, initiative-grouped active/ready/attention work, exact finding-supplied next actions on attention items, and separately labelled shaping, brief, and backlog context while preserving text labels independent of color.
- [x] **AC7.** The valid empty state names `work-intake` as the existing creation/routing front door and `workspace-status` as the operational source; it contains no Project artifact, template, schema, or creation path.
- [x] **AC8.** Primary navigation exposes one base-aware `Work` link in desktop and mobile paths with no other navigation restructuring.
- [x] **AC9.** The rendered populated and empty states answer all four business questions, pass keyboard and semantic inspection, show no horizontal body scroll at 375 px, honor reduced motion, and receive no severity-3+ design-review finding against `precision authority` and `staged revelation`.
- [x] **AC10.** Projection tests, web unit/accessibility gates, rendered-link closure, and `npm run build --prefix web` pass; the build contains `build/work/index.html`.
- [x] **AC11.** Repository inspection finds no operative standalone Project artifact or consumer: `docs/product/projects/` is absent; living conventions, templates, roadmap, workspace-status references, and P5 records use the work-intake/workspace model. Frozen governance history, tracker labels, desk-research projects, and RFC-0079 codebase indexes are explicitly excluded from this assertion.
- [x] **AC12.** RFC-0064 Errata #8 is the authoritative design correction and Errata #9 records P5 closeout; `docs/specs/README.md` reports this spec as Shipped without rewriting frozen history.
- [x] **AC13.** At closeout, the exact five-field canonical entry `{path = "docs/specs/m6-astro-work-index/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Give PMs a static read-only view of canonical workspace status", needs = []}` exists once in `ini-002.work.shipped` and remains absent from `[work].queue` and `[work].active`. The enterprise-rollout slice remains independent with `needs = []`, and all `ini-008` memberships remain unchanged.

## Assumptions

- Technical: `workspace-status` exposes deterministic schema-version-1 JSON and is the sole production classification/reconciliation engine used by CLI and MCP (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`; `docs/specs/workspace-routing-invariants/spec.md`).
- Technical: the workspace-entry contract has exactly `path`, `kind`, `source`, `summary`, and `needs`, and excludes `project` from its kind vocabulary (source: `contracts/jsonschema/workspace-entry.schema.json`).
- Technical: `web/` is the existing static Astro 7.1.0 app and can run a bounded build-time Python subprocess without adding a package dependency (source: `web/package.json`; existing Python repository build tooling).
- Product: PM visibility means a static comprehension layer over canonical work state, while work creation stays in `work-intake` and live dispatch/telemetry remain outside this P5 slice (source: RFC-0083; user confirmation 2026-08-15).
- Product: the dominant design goal is precision authority followed by staged revelation; the page leads with status and, when a finding supplies one, its canonical next action rather than decorative dashboard widgets (source: `docs/specs/platform-site/aesthetic-direction.md`; user confirmation 2026-08-15).
- Process: RFC-0064 Errata #8 retires the standalone Project model and recuts its P5 Astro deliverable as this work index (source: `docs/rfc/0064-ini-001-ai-native-ecosystem.md`; user confirmation 2026-08-15).
- Process: this slice is independent of `m6-enterprise-rollout-playbook` and does not modify INI-008, work-intake, or workspace-routing (source: user confirmation 2026-08-15).
