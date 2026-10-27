# Loop cohort

- **Status:** Open
- **Kind:** defect
- **Detail:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py

## Summary

Refuse or disambiguate a duplicate plan task heading: parse_plan keys deps by task ID so a second section with the same ID silently drops the first section's declared edges and the task schedules as if it depended on nothing, and the duplicate-section refusal that would catch it is only reachable once completed-task pins exist
