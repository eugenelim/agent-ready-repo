# Plan: m6-astro-work-index

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> record why in the changelog.

## Approach

Build one read-only presentation adapter around the existing workspace-status
CLI, then feed its bounded projection to a static Astro `/work/` page. The
adapter owns no lifecycle logic: it preserves canonical classifications and
joins only `workspace.toml` fields that RFC-0083 defines as display-only. Tests
lock that boundary before the UI is written. The page then renders a status-first
analytical hierarchy and one shared navigation entry. No Project replacement
artifact or user workflow is introduced.

## Constraints

- RFC-0064 Errata #8 recuts the P5 outcome; RFC-0083 and ADR-0077/0078 own
  intake, artifact identity, and workspace indexing.
- `workspace_status.py` remains the only source for classification,
  reconciliation, dispatchability, findings, and finding-level next actions;
  the page invents no ready/active action.
- Direct TOML access is presentation-only and cannot affect routing.
- `web/AGENTS.md` and the platform-site aesthetic direction own Astro,
  navigation, base paths, tokens, accessibility, and mobile checks.
- No dependency on `m6-enterprise-rollout-playbook`; no change to `ini-008`,
  work-intake, workspace schemas, workspace-routing code, package manifests, or
  lockfiles.

## Construction tests

**Integration tests:** run the adapter against controlled status/TOML fixtures
and the real repository; run the Astro build and assert `/work/index.html`
exists with source-derived status and no runtime script.

**Manual verification:** inspect populated and empty projections at desktop and
375 px widths for the four business questions, keyboard reading order, status
text, next-action prominence, and horizontal overflow.

## Design (LLD)

### Design decisions

- Treat the production CLI JSON as the status contract; do not parse artifacts
  or TOML to derive lifecycle. Traces to AC1–AC4.
- Join only initiative labels and entry summaries from TOML because the schema
  explicitly excludes summaries from routing. Traces to AC2–AC3.
- Generate the projection in a bounded Python build adapter so the Astro app
  needs no TOML/runtime dependency. Traces to AC1, AC3, AC5.
- Render one static overview/worklist/detail page with no filter state or client
  hydration. Traces to AC5–AC10.

### Component / module decomposition

- `tools/export_work_index.py`: invoke workspace-status, validate its public
  envelope, parse TOML display fields, join exact identities, and emit confined
  JSON to stdout. Traces to AC1–AC4.
- `tools/test_export_work_index.py`: projection-boundary and fail-closed tests.
  Traces to AC1–AC4.
- `web/src/lib/work-index.ts`: invoke the exporter with an argv array, validate
  the page projection, and expose typed data to Astro. Traces to AC1, AC5.
- `web/src/components/work/WorkIndex.astro`: semantic empty/populated analytical
  hierarchy. Traces to AC6–AC7, AC9.
- `web/src/pages/work/index.astro`: static route and real repository-data
  boundary. Traces to AC5, AC10.
- `web/src/test/work-index.test.ts`: component/projection integration and
  semantic-state tests. Traces to AC5–AC10.
- `web/src/components/layout/SiteNav.astro`: one shared `Work` link. Traces to
  AC8.

### State & control flow

At build time the TypeScript loader invokes the Python exporter with explicit
argv. The exporter follows AC1's single canonical CLI/root contract, validates
schema version and required collections, reads `workspace.toml` display fields,
and joins them only onto existing canonical identities. The loader validates the
bounded page projection and Astro renders either the empty or populated static
state. Any failure aborts the build; there is no browser-time loading state.

### Behavior & rules

- Canonical active/ready/blocked identity and next-action data pass through
  unchanged.
- Attention contains only `work.queue` and `work.active` canonical evaluations
  with findings; legacy shipped cleanup remains a reconciliation concern.
- Display joins require exact initiative, collection, and path identity.
- Work sorts active, ready, attention, then canonical identifier; shaping,
  briefs, and backlog render in separate sections.
- Every status and finding is text-labelled; color is supplemental.

Traces to AC1–AC9.

### Failure, edge cases & resilience

CLI failure, timeout, invalid JSON, unsupported schema, missing collections,
unsafe public paths, duplicate join identities, or missing required summaries
fail with a confined message. Empty canonical work is valid. Raw TOML comments,
artifact prose, stderr, absolute paths, and tracebacks never enter the public
projection. Traces to AC1–AC4, AC7.

### Quality attributes (NFRs)

- Deterministic: equal CLI/TOML inputs produce byte-equivalent sorted page data.
- Safe: fixed executable/argv, bounded timeout/output, confined paths, no shell,
  no network, and no mutation.
- Accessible: semantic landmarks/headings/lists, visible text statuses, keyboard
  order, no motion requirement, and 375 px body containment.
- Maintainable: one adapter boundary consumes the published CLI instead of
  copying its routing rules.

Traces to AC1–AC10.

## Tasks

### T1: The presentation projection preserves canonical status

**Depends on:** none

**Touches:** `tools/test_export_work_index.py`, `tools/export_work_index.py`

**Mode:** TDD

**Tests:**
- `stub: true`
- **Stub:** materialize projection tests before the exporter. They cover valid
  active/ready/attention work, exact summary/name/milestone joins, separate
  shaping/brief/backlog context, deterministic ordering, and the AC1 failure
  matrix, including fixed argv, confinement, timeout/output/data bounds, and
  sanitized failure.
- Paired fixtures change comments, summaries, and array order and prove status,
  findings, dispatchability, and finding-supplied next actions remain identical.

**Approach:**
- Implement pure validation/join functions, then a thin CLI that invokes the
  production workspace-status script using AC1's exact argv/root contract and
  bounded resources.
- Parse TOML only for display fields and refuse ambiguous joins.

**Done when:** AC1–AC4 projection tests pass and the real repository invocation
emits valid confined JSON without changing files.

### T2: Astro consumes the projection without a second data model

**Depends on:** T1

**Touches:** `web/src/lib/work-index.ts`, `web/src/test/work-index.test.ts`

**Mode:** TDD

**Tests:**
- `stub: true`
- **Stub:** import the absent loader and assert schema validation, empty and
  populated projections, exact status preservation, and exporter failure.
- Run the full web unit suite after the focused cases pass.

**Approach:**
- Invoke the exporter with `execFileSync` and an argv array, never a shell.
- Validate the small page-projection boundary and expose immutable typed data.

**Done when:** AC1–AC5 loader tests pass without a new dependency.

### T3: The static page answers the PM's four questions

**Depends on:** T2

**Touches:** `web/src/components/work/WorkIndex.astro`, `web/src/pages/work/index.astro`, `web/src/test/work-index.test.ts`, `docs/specs/m6-astro-work-index/notes/visual-qa.md`

**Mode:** TDD plus visual / manual QA

**Tests:**
- `stub: true`
- **Stub:** the shared web stub imports the absent projection validator and
  component before construction. It pins status preservation, empty/populated
  semantics, and contextual escaping of repository-derived markup payloads.
- Rendered-component tests cover six Tier-1 counts, initiative-grouped work,
  text findings and their next actions, the absence of invented ready/active
  actions, separated upstream context, and the valid empty state.
- `npm run build --prefix web` invokes the real adapter and emits
  `build/work/index.html` with no runtime script.
- `notes/visual-qa.md` records desktop/375 px, keyboard/semantic, overflow,
  design-review, fixture driver, and a scope boundary before the evidence:
  populated and empty static `/work/` are exercised; live dispatch, refresh,
  write-back, and the control plane are not exercised and remain out of scope.

**Approach:**
- Render one server-only Astro component inside existing layout primitives.
- Use status-first spatial hierarchy and progressive detail; add no charts,
  client state, public fixture route, or fake workspace record.

**Done when:** AC5–AC7 and AC9–AC10 pass.

### T4: Work is discoverable and the independent slice closes cleanly

**Depends on:** T3

**Touches:** `web/src/components/layout/SiteNav.astro`, existing navigation/link tests, `docs/rfc/0064-ini-001-ai-native-ecosystem.md`, `docs/specs/README.md`, `workspace.toml`, `docs/product/changelog.md`

**Mode:** goal-based check

**Tests:**
- Existing navigation tests assert one base-aware `Work` link in desktop and
  mobile output; rendered-link closure recognizes `/work/`.
- Repository audit proves the operative standalone Project surface is absent
  while excluded historical/unrelated uses remain untouched.
- `workspace-status reconcile` classifies this spec's five-field record
  independently and confirms no dependency on the rollout playbook.

**Approach:**
- Add one item to the shared navigation source.
- At closeout, append RFC errata history if needed, update the living spec index
  and changelog, and move only this exact workspace record to shipped.

**Done when:** AC8 and AC11–AC13 pass with all shared site gates green.

## Rollout

The route ships in the existing static Astro build and sitemap. Reverting the
page, adapter, tests, navigation item, and status records removes it cleanly.
There is no data migration, infrastructure, external system, or write path.

## Risks

- The CLI projection intentionally omits some display labels; the bounded TOML
  join must stay display-only or it becomes a competing status engine.
- A repository with many historical reconciliation findings can overwhelm the
  page; AC4 limits the delivery worklist without hiding them from
  workspace-status itself.
- A build subprocess can leak paths or hang if unbounded; fixed argv, timeout,
  output caps, and confined errors are part of AC1 and the security review.
- The static page can be mistaken for live state; the copy must call it a
  repository snapshot and direct operational use to workspace-status.

## Changelog

- 2026-08-15: Recut the rejected Project-index plan around RFC-0083's canonical work-intake and workspace-status model; removed the standalone Project artifact and added no replacement workflow.
- 2026-08-15: Spec and plan approved by eugenelim; the canonical queue record may now be registered.
- 2026-08-16: Rebased onto Core 2.7 work-intake, confirmed the read-only boundary remains current, and closed the shipped slice after build, link, accessibility, and browser verification.
- 2026-08-16: Allowed canonical `missing_artifact` attention identities to name an absent leaf while retaining nearest-existing-ancestor confinement and symlink-escape refusal.
