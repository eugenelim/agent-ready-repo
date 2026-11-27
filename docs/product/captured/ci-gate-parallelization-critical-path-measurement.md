# Ci gate parallelization critical path measurement

- **Status:** Closed
- **Resolution:** superseded
- **Kind:** defect
- **Detail:** https://github.com/eugenelim/agent-ready-repo/blob/7bdd03da0a93a35883ef1d32a121ec361b99211d/docs/specs/ci-gate-parallelization/notes/ci-gate-parallelization-critical-path-measurement.md

## Summary

Preserve the frozen deferral identity and completed docs-only CI measurement while the 302-second gate-main miss moves to its runtime-budget intent

## Resolution

Absorbed by intent `ci-gate-main-runtime-budget`, which carries the 2026-11-04 re-measurement and the 2026-11-05 re-profile (`gate-main` median 874 s over 19 pull-request runs).
