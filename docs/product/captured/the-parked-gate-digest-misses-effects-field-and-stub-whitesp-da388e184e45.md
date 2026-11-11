# The parked-gate digest misses Effects-field and stub-whitespace edits that change finish effects.

- **Status:** Open
- **Kind:** defect
- **Detail:** docs/knowledge/observations/work-item/2026-11.jsonl

## Summary

The parked-gate digest misses Effects-field and stub-whitespace edits that change finish effects.

## Observed

A plan-level Effects field inside the approval-entry region still feeds the finish effects, and stub lines keep their trailing whitespace. Adding an approval entry, a blank line at the region's end, or trailing whitespace on a stub line after park changes what the supervisor does while the gate digest stays the same (review findings adv7-1 and sec7-2).

## Intended

An edit after park that can change finish effects or stub bytes also changes the gate digest, or the supervisor refuses it.
