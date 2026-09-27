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

## [core][2.27.1] — 2026-09-27

### Highlights

- **Interrupted work-loop transitions now replay without separate cohort repair commands.** The five registered cohort-effect transitions apply their effects through `loop-cohort.py`, record one durable transition identity, and safely resume without double-advancing a wave, double-counting a retry, or duplicating a review round.

### Changed

- Cohort state moves to schema 2 with `pending_transition` and a unified, oldest-first-truncated `transition_history`; engine state remains schema 1. Runs crossing this boundary must use the authorized `loop-cohort reset` then `loop-engine reset` recovery pair.
