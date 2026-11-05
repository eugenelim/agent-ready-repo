# A git fetch from a sibling worktree during a supervisor run makes the next report refuse.

- **Status:** Open
- **Kind:** defect
- **Detail:** docs/knowledge/observations/work-item/2026-11.jsonl

## Summary

A git fetch from a sibling worktree during a supervisor run makes the next report refuse.

## Observed

An attempt record pins the shared info/refs file, so a git fetch from a sibling worktree during a run makes the next report refuse with denied-git-control-state until the owner re-baselines the record.

## Intended

A fetch from a sibling worktree does not refuse the next report.
