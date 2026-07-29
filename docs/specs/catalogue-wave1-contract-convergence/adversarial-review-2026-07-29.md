# Adversarial Review — catalogue-wave1-contract-convergence

**Reviewer:** adversarial-reviewer  
**Date:** 2026-07-29  
**Round:** post-EXECUTE (second pass after fixes)

## Findings (second pass — after fixes applied)

All blockers and nits from the first pass were resolved:

- **Blocker 1 (hub hyperlink depth):** Guide-to-guide links in hub used `../../packs/` (2 levels) instead of `../../../packs/` (3 levels from `guides/_shared/reference/`). Fixed with `replace_all`; scaffold re-synced. ✓
- **Blocker 2 (spec metadata drift):** Status left as `Implementing`, all 29 ACs unchecked. Fixed (current edit). ✓
- **Nit 5 (dead allowlist):** `_DATA_ONLY_ALLOWLIST` frozenset defined but never referenced in `check_contract_parity.py`. Removed. ✓
- **Nit 6 (packs/README hub reference):** Hub reference was plain-text instead of markdown hyperlink. Converted to `[...](../guides/_shared/reference/catalogue-authoring-standards.md)`. ✓

**Concern 4 (profile.schema.json):** Pre-existing drift discovered and fixed during D2 implementation; synced contracts/ → _data/ per D1 authority model. Recorded in changelog. Note added to spec Phase C. ✓

Clean — ready to commit.
