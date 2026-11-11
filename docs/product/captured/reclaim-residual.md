# Reclaim residual

- **Status:** Open
- **Kind:** defect
- **Detail:** docs/specs/loop-cohort-state-lock/notes/reclaim-residual.md

## Summary

A state-lock reclaim's identity check and its rename are two operations, so a holder acquiring between them is displaced and reports StateLockLost having done nothing wrong. Not closable by checking harder -- POSIX has no rename-if-unchanged. Atomic takeover is disproved and recorded: rename replaces unconditionally, so every contender with the same stale snapshot wins in turn, measured at three to five holders. The note carries the forced-interleaving reproduction
