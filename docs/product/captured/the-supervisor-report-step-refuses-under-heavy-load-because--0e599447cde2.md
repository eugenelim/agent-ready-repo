# The supervisor report step refuses under heavy load because its staging timeout is a fixed 60 seconds.

- **Status:** Open
- **Kind:** defect
- **Detail:** docs/knowledge/observations/work-item/2026-11.jsonl

## Summary

The supervisor report step refuses under heavy load because its staging timeout is a fixed 60 seconds.

## Observed

report stages with a fixed 60-second timeout, so under heavy machine load it refuses with denied-git-unavailable and the controller must retry it.

## Intended

report completes under heavy load, or its staging timeout can be raised without a code change.
