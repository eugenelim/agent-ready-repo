# Changelog

Document notable user-visible changes to this project here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project may follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
when that matches its release model.

> Maintenance: add a `## [<artifact>][<version>] — YYYY-MM-DD` section in the
> same change that bumps a released artifact's version. Keep released entries
> newest-first and write them for users rather than contributors.

<!-- Example entry (replace with your first real version):

## [pack-name][version] — YYYY-MM-DD

### Added / Changed / Fixed

- Describe the user-visible change.

-->

## [core][2.27.6] — 2026-09-30

### Highlights

- **Work-loop can now explain a scheduled wave before dispatch without authorizing concurrent writes.** `loop-cohort wave-decision --json` reports unfinished tasks as `parallel-capable` or `sequential`, includes pairwise `Touches:` relations, and returns fixed public-safe JSON refusal envelopes while leaving the populated-branch post-write gate authoritative and concurrent wave execution disabled.

### Added

- Added the read-only `loop-cohort wave-decision` screen for scheduled cohorts. It reports task-level admission candidates, pair-level `disjoint` / `overlapping` / `unknown` relations, and `admission_pending: true` on verdicts.
- Added a versioned JSON contract for `wave-decision` verdict and refusal envelopes, including stdout JSON refusals under `--json` with bounded public-safe `detail` messages.

### Changed

- Supervisor guidance now separates the pre-dispatch `wave-decision` screen from the existing post-write `dispatch-decision` gate and names `_DANGER_PATH_RE` as shared by both consumers.

## [core][2.27.1] — 2026-09-27

### Highlights

- **Interrupted work-loop transitions now replay without separate cohort repair commands.** The five registered cohort-effect transitions apply their effects through `loop-cohort.py`, record one durable transition identity, and safely resume without double-advancing a wave, double-counting a retry, or duplicating a review round.

### Changed

- Cohort state moves to schema 2 with `pending_transition` and a unified, oldest-first-truncated `transition_history`; engine state remains schema 1. Runs crossing this boundary must use the authorized `loop-cohort reset` then `loop-engine reset` recovery pair.
