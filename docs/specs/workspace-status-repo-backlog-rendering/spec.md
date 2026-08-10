# Spec: workspace-status repo backlog rendering

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (published JSON/output-contract change)
- **Constrained by:**
  - [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) — `workspace.toml` and `workspace-status` behavior authority
  - [`workspace-status-simplification-order-1a`](../workspace-status-simplification-order-1a/spec.md) — backend JSON compatibility baseline
  - [`workspace.toml` schema reference](../../../guides/core/reference/workspace-toml-schema.md) — repository backlog is visible and non-dispatchable; display metadata is non-semantic
- **Brief:** none
- **Discovery:** none
- **Contract:** none (internal skill JSON interface)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent invoking `workspace-status` receives every repository-level
`[backlog].open` entry from the backend and renders the complete backlog without
independently reconstructing that collection. `status` and `reconcile` expose
the same ordered, display-only `repo_backlog.open` projection. Untyped legacy
entries render in the build room and entries carrying a shaping `type` render
in the shaping room. Target five-field entries are preserved losslessly and
derive a display room from their artifact `kind`. The typed-only shaping guard
remains a separate contract.

## Boundaries

### Always do

- Preserve `[backlog].open` source order and every explicit `needs`, `source`,
  and `summary` value in `repo_backlog.open`.
- Emit an explicit `room` for every repository backlog entry and retain the
  shaping subtype as `entry_type` when one is declared.
- Keep the backend projection additive under `schema_version: 1` and consume it
  as the renderer's authoritative entry list.
- Keep legacy summary-comment fallback available only when an entry has no
  explicit `summary` field.

### Ask first

- Any change to the agreed `repo_backlog.open` field or per-entry key names.
- Any migration or rewrite of live `workspace.toml` entries.
- Any widening from repository backlog display to initiative queue metadata.

### Never do

- Broaden, rename, or remove `shaping.top_level_backlog` or its typed-only
  shaping-guard semantics.
- Let repository backlog display metadata affect routing, dependency
  satisfaction, reconciliation, repair planning, or dispatch.
- Reorder, deduplicate, classify as ready/blocked, or silently omit repository
  backlog entries.
- Add a dependency, a new module boundary, or a second independent backend.
- Pin tests or rendering to this repository's current backlog count.

## Testing Strategy

- **TDD, contract level:** invoke the production CLI against a small fixture
  containing an untyped build entry followed by a typed shaping entry. Assert
  that both `status` and `reconcile` emit the same ordered
  `repo_backlog.open` projection, preserve explicit dependencies and display
  metadata, and leave `shaping.top_level_backlog` typed-only.
- **TDD, empty state:** invoke both modes with an absent or empty repository
  backlog and assert `repo_backlog.open` is empty.
- **Goal-based check:** skill/eval assertions require the renderer to consume
  `repo_backlog.open`, render `Backlog — N open item(s)` only when nonempty,
  and label entries `[build]` or `[shape]`.
- **Visual / manual QA:** invoke the projected skill backend against a small
  mixed fixture and this worktree, record the JSON and rendered backlog shape,
  and verify the observed count is derived rather than hard-coded.

## Acceptance Criteria

- [x] **AC1.** Successful `status` and `reconcile` JSON includes a top-level
  `repo_backlog` object with an `open` array containing every parsed
  `[backlog].open` entry in source order.
- [x] **AC2.** A legacy `{slug, ...}` inline table produces exactly three
  required keys: `slug` (string copied from the inline table), `room`
  (`"build"` or `"shape"`), and `needs` (array of dependency strings, using
  the backend's established absent→empty-array and scalar→one-item-array
  normalization). Its optional output keys are `entry_type` (string copied
  from `type`), `source` (the explicit TOML string or table represented as the
  equivalent JSON string or object), and `summary` (string). Without `type`,
  `room` is `"build"` and `entry_type` is omitted; with `type`, `room` is
  `"shape"` and the value is copied to `entry_type`. Missing optional keys are
  omitted, not invented or emitted as null. Bare-string backlog entries remain
  outside the supported compatibility contract.
- [x] **AC3.** A target five-field inline table produces `path` (string),
  `kind` (`"intent" | "research" | "design" | "brief" | "spec" | "defect"`),
  `source` (JSON object equivalent to the declared TOML source table),
  `summary` (string), and `needs` (JSON array equivalent to the declared array
  of typed dependency tables), preserving each value exactly, plus a
  display-only `room`. The mapping is `"shape"` for upstream kinds `intent`,
  `research`, `design`, and `brief`; it is `"build"` for implementation kinds
  `spec` and `defect`. It emits neither `slug` nor `entry_type`; the renderer
  uses `path` as its display identifier. This projection does not validate,
  route, dispatch, or select a processor for the target entry.
- [x] **AC4.** An absent `[backlog]` table, absent `open` key, or empty `open`
  list yields `repo_backlog.open: []` without an error.
- [x] **AC5.** `shaping.top_level_backlog` remains present, typed-only, and
  backward-compatible; untyped build entries never enter it.
- [x] **AC6.** Adding the display projection does not change ready/blocked
  classifications, dependency satisfaction, reconciliation findings, repair
  plans, or routing results.
- [x] **AC7.** The renderer uses `repo_backlog.open` as the authoritative list,
  renders `Backlog — N open item(s)` whenever it is nonempty, labels each row
  from `room`, and preserves list order.
- [x] **AC8.** The renderer omits the backlog section only when
  `repo_backlog.open` is absent or empty and retains the legacy comment-summary
  fallback for entries without an explicit summary.
- [x] **AC9.** A contract-level regression fixture contains one untyped build
  entry, one typed shaping entry, explicit `needs`, `source`, and `summary`
  fields where relevant, plus empty-backlog coverage. A separate focused case
  covers a target five-field entry. No assertion names this repository's
  current backlog count.
- [x] **AC10.** The workspace-status behavior eval exercises a nonempty mixed
  repository backlog and checks the section heading plus `[build]` and
  `[shape]` rows.
- [x] **AC11.** Core pack metadata receives the required patch release,
  changelog entry, and regenerated self-host projections.
- [x] **AC12.** Targeted tests and repository gates pass in canonical order,
  followed by adversarial and quality review; security review runs only if the
  implementation crosses a security boundary.

## Assumptions

- Technical: `status` and `reconcile` share the CLI `_build_json` serializer
  (source: `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`).
- Technical: `shaping.top_level_backlog` deliberately contains only typed
  shaping entries for the work-loop guard (source:
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`).
- Technical: `.apm` is the source and self-host adapter trees are generated
  projections (source: `packs/AGENTS.md`).
- Product: the dedicated contract is `repo_backlog.open`, with `room` as the
  mixed-collection discriminator and optional `entry_type` for shaping subtype
  (source: user confirmation 2026-08-10).
- Product: display order and metadata are non-semantic and must not affect
  routing, dependencies, or dispatch (source: user confirmation 2026-08-10 and
  `guides/core/reference/workspace-toml-schema.md`).
- Process: this change runs the full work-loop because it changes a published
  JSON/output contract (source: `AGENTS.md` and user confirmation 2026-08-10).
