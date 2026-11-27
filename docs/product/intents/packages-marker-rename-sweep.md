# Pinned packages governance markers are renamed consistently

- **Slug:** `packages-marker-rename-sweep`
- **Status:** Fulfilled
- **Level:** feature
- **Owner:** eugenelim
- **Accepted:** 2026-10-21 by eugenelim, after a cold intent-mode shaping review returned no MALFORMED token
- **Fulfilled:** 2026-10-21 eugenelim: delivered by PR #1596 (commit `1a2e49add`, agentbundle 0.53.2). Both `commands/install.py` `pre-RFC-0012 dist-tree` messages now read `legacy dist-tree`, and the seven `tests/unit/test_install_inband_detection.py` assertions changed with them. The `--emit-install-routes` local-scope refusal states its rule, and its assertion lost the `or` branch. `tests/roster/test_agentbundle_governance_markers.py` now fails on any governance marker in shipped source. The intent has no decomposition, so the closure check had no descendants to wait on.
- **Shaping-reviewed:** 2026-10-21
- **Governed by:** the historical retained-set classification below; current package marker rules are owned by `packages/AGENTS.local.md` and `tests/roster/test_agentbundle_governance_markers.py`.

## Outcome

Every retained runtime governance-marker string has its matching pinning assertion updated in the same reviewed change.

## Opportunity

Phase-1 of the `packages/` marker sweep left runtime messages and their verbatim assertions embedding governance markers, including config errors and the legacy dist-tree name.

## What this absorbs

### packages-marker-sweep-pinned-strings

- The phase-1 classification rationale and a Git locator for its full inventory are preserved below. They record the input to this fulfilled rename, not an exemption from the current marker gate.
- For each retained string, rename the string and edit its pinning assertion in the same commit.
- The phase-1 naming decision concerned both `commands/install.py` `pre-RFC-0012 dist-tree` strings—the `--force will REMOVE` warning and the `install:` refusal—and the seven assertions that pinned them. This intent selected `legacy dist-tree`, as recorded in its Fulfilled receipt; the disk layout itself did not change.
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

## Historical phase-1 retained classification

The retired sweep's AC5 supplied the phase-1 classification. The full
inventory and its Boundaries section remain available in Git at
`7bdd03da0a93a35883ef1d32a121ec361b99211d:docs/specs/packages-governance-marker-sweep/spec.md`
(SHA-256 `2f79543922f2c052aa2757086898649ac90885727e58c421f773c1bb5183e073`). The current marker gate and this
intent's Fulfilled receipt supersede the pinned-runtime-string exemptions.
The template's protected `Specs:` sentinel was a recorded decision that phase 1
could not overturn; the current template and integration test no longer contain
that block or its named assertion. This transfer neither restores that old
requirement nor authorizes a new package change.

The retained classes had different reasons, not one permanent exemption:

- Pinned runtime messages had to change with their assertions. The legacy-layout
  token needed a naming decision; the install-routes assertion's alternative
  branch had to be removed so it could not mask an unchanged requirement.
- Governance-subject tests used document paths as functional inputs; generic
  fixture paths exercised a glob rather than citing a repository feature.
  Failure-message text and skip reasons were not asserted values.
- The template's `Specs:` block was protected by a specific assertion, so phase 1
  could not silently reverse it. Current source has since removed that block.
- The credbroker README design links retained working URLs with ordinal-free
  labels under the earlier explicit sentinel decision.
- Changelogs were confirmed absent from the wheel, sdist and init scaffold in
  that delivery, so historical wording was deliberately out of scope. Agent
  context files were insider guidance. Neither was a pending runtime rename.

The old `contracts-readme-governance-markers` suggestion is superseded by the
current contract-map role. `contracts/README.md` deliberately uses absolute
links to governing designs because catalogue archives include contracts and
omit docs. Those working provenance links serve its published readers; the
package-source marker rule does not require stripping them. This is no longer
a pending blanket README marker-removal task.
