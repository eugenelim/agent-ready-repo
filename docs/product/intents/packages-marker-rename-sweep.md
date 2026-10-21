# Pinned packages governance markers are renamed consistently

- **Slug:** `packages-marker-rename-sweep`
- **Status:** Accepted
- **Level:** feature
- **Owner:** eugenelim
- **Accepted:** 2026-10-21 by eugenelim, after a cold intent-mode shaping review returned no MALFORMED token
- **Shaping-reviewed:** 2026-10-21
- **Governed by:** [spec/packages-governance-marker-sweep AC5](../../specs/packages-governance-marker-sweep/spec.md)

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

## Non-goals

- No exit code, refusal order or install behaviour changes. Only message wording and the assertions that pin it change.
- The legacy dist-tree layout on disk is not renamed or migrated. Only the words that name it in messages change.
- Historical entries in `packages/agentbundle/CHANGELOG.md` keep their original wording.

## Assumptions

- **Riskiest assumption:** an adopter who met the old `pre-RFC-0012 dist-tree` wording still recognises the same layout under the new `legacy dist-tree` wording. If that is false, someone with a legacy tree misreads the `--force will REMOVE` warning. Check: the warning still names the pack and the files it removes, so the layout is identified by its contents rather than by the label.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
