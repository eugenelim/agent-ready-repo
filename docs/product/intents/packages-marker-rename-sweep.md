# Pinned packages governance markers are renamed consistently

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/packages-governance-marker-sweep AC5](../../specs/packages-governance-marker-sweep/spec.md)

## Outcome

Every retained runtime governance-marker string has its matching pinning assertion updated in the same reviewed change.

## Opportunity

Phase-1 of the `packages/` marker sweep left runtime messages and their verbatim assertions embedding governance markers, including config errors and the legacy dist-tree name.

## What this absorbs

### packages-marker-sweep-pinned-strings

- The complete retained-string set is enumerated once in `docs/specs/packages-governance-marker-sweep/spec.md` AC5 and is not repeated here, so the two copies cannot drift.
- For each retained string, rename the string and edit its pinning assertion in the same commit.
- `pre-RFC-0012` needs a naming decision first because it names a legacy on-disk layout. `docs/specs/packages-governance-marker-sweep/spec.md:41` identifies both `commands/install.py` `pre-RFC-0012 dist-tree` strings—the `--force will REMOVE` warning and the `install:` refusal—and the seven `assertIn`/`assertNotIn` assertions in `tests/unit/test_install_inband_detection.py` that pin them.
- The RFC-0008 refusal needs its `or` branch removed so the assertion no longer silently passes on its second clause.
- Decide the legacy-layout rename and update every pinned message with its assertion in one reviewed change.
- **BLOCKER:** The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This applies at commit time.
- Unblocks when: picked up — no dependency.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
