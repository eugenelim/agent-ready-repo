# Spec: adversarial-reviewer-deferral-resolution-update

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Mode:** light (no risk trigger fired)
- **Plan:** inline below

> **Spec contract:** this document defines what "done" means.

## Objective

Make `docs/backlog.md` purely historical. The m3-backlog-absorption migration
moved all open work to `workspace.toml [backlog].open`, leaving `docs/backlog.md`
as a tombstone for Frozen RFC anchor links only. However, `lint-spec-status.py`
still resolves `(deferred:)` markers against the union of `workspace.toml
[backlog].open` AND `docs/backlog.md` headings, and `adversarial-reviewer.md`
check (c) still instructs reviewers to look for `(deferred:)` anchors in
`docs/backlog.md`. Both need updating so the workspace.toml register is the single
authoritative source.

## Acceptance Criteria

- [x] `lint-spec-status.py` resolves `(deferred:)` anchors only against
  `workspace.toml [backlog].open` slugs — no `docs/backlog.md` read in the
  deferral check.
- [x] Dead helper code removed from `lint-spec-status.py`: `backlog_anchors()`,
  `slugify()`, `_HEADING_RE`, `backlog_path` local variable.
- [x] `adversarial-reviewer.md` check (c) reads: "resolves to a slug entry in
  `workspace.toml [backlog].open`" (not "points to a real heading in
  `docs/backlog.md`").
- [x] `lint-spec-status.py` run against the live repo produces no new hard
  violations — all existing `(deferred:)` markers already resolve against
  `workspace.toml [backlog].open`.
- [x] Projections synced: `.claude/agents/adversarial-reviewer.md` and
  `.claude/skills/work-loop/scripts/lint-spec-status.py` match their pack
  sources after `make build-self`.

## Tasks

1. Edit `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` — remove
   `docs/backlog.md` union from `check()`, remove dead helpers, update docstring
   and error message.
2. Edit `packs/core/.apm/agents/adversarial-reviewer.md` — update check (c).
3. Run `make build-self` to sync projections.
4. Run `lint-spec-status.py` to confirm no new violations.
