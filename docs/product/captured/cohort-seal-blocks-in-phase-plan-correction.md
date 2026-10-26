# Cohort seal blocks in phase plan correction

- **Status:** Open
- **Kind:** defect

## Summary

loop-engine applies `schedule check-current` to every CODE-* transition except `done`, so any plan.md edit blocks the rest of a run even though the plan contract requires in-phase correction while Status is Executing; the only escape is a cohort re-seal that clears the review-retry and stasis counters and resets current_wave_index
