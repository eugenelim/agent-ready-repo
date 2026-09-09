# Ask-first review: admitting `cooled_child_scope_unknown`

`docs/specs/workspace-routing-invariants/spec.md:30` lists "Add a new finding
code" under *Ask first*, and `:60` calls its § *Canonical findings* table the
public refusal contract. RFC-0096's 2026-09-03 Errata names the same boundary
for this closure. This is the record of that review.

- **Reviewed:** 2026-09-03
- **Decision:** granted — build the read-free link *and* the new finding code.
- **Code admitted:** `cooled_child_scope_unknown`, one code, on the child entry.

## What was measured before the decision

Measured on this checkout at HEAD `807fc8ef1`, 2026-09-03. Every number was
constructed and printed; none was read off a function body. The commands are in
`probes.md`.

| Fact | Number |
| --- | --- |
| `work.*` spec entries | 115 (114 `work.shipped`, 1 `work.active`) |
| …declaring no `source.parent` | 99 (86%) |
| …carrying a body-only parent link — the gap's live population | 0 |
| Briefs in `brief_queue.*` | 15 |
| …with zero attributed children | 11 |
| Live `kind = "brief"` dependencies | 5, all brief→brief, all in `brief_queue.draft` |
| Lifecycle records in `docs/lifecycle/` | 0 — nothing has cooled |

Two of those numbers decided the review.

**The gap's live population is zero, and it is zero because a control holds
it there.** `provenance_mismatch` (`workspace_status_engine.py:3172`) compares
the entry's `source.parent` against the body's parent and fires in both
directions, so a spec with a body-only brief link is already a live finding.
Probe 4 shows it firing on that exact divergence.

**That control is suppressed by cooling.** `_structural_findings` returns early
for a cooled membership at `:3138`, because every predicate below that line
reads the body. Probe 4 shows `provenance_mismatch` present on the uncooled run
and absent on the cooled one. So the sequence that produces the harm is: a
body-only link is a live finding, the artifact cools, and both the finding and
the child-scope protection vanish together.

**Nothing has cooled yet**, so the fail-closed path costs zero refusals today,
and its worst case is bounded at the 5 live brief dependencies.

## Why the two withdrawn repairs are not revived

Wave 6 tried marking every brief in the workspace, then every brief in the
initiative. Both refused brief dependencies whenever any parentless spec cooled,
and 99 of 115 entries are parentless, so the trigger was the common case. The
recorded cost was 81 of 92 specs in `ini-002`.

The material difference here is not the refusal — it is that the refusal is now
**escapable and attributed**. Under the withdrawn repairs, absence was the only
representable state, so a maintainer had no way to clear the refusal and no way
to learn which entry caused it. Under this closure the entry declares
`source.parent = "none"` and the refusal lifts, the finding names the exact
path to repair, and `provenance_mismatch` already validates the declaration
against the body on every uncooled run. `workspace-routing-invariants` §
*Always do* requires "the smallest safe next action"; that requirement is what
the new code buys, and it is why reusing `unsatisfied_dependency` alone was
rejected — that refusal names the brief, not the entry a maintainer must edit.

## Options offered, and why the third was declined

1. **Link plus new finding code** — admitted. Costs one code, two documentation
   rows, and an `Ask first` review.
2. **Link only, reuse `unsatisfied_dependency`** — declined. Avoids the boundary
   but leaves the refusal unattributable, breaching § *Always do*.
3. **Re-register the follow-on with a named owner** — declined for the mechanism
   half, retained for the residual. An *exact* closure needs the parent link
   stamped at closeout while the body is still readable, and that writer is
   `close-work`, whose `close_work.py` the concurrent Wave 7c delivery holds.
   That decision is recorded in `spec.md`'s Follow-ons table, which is the
   canonical list, as `cooled-parent-scope-declaration-writer` rather than
   blocking the closure:
   fail-closed-and-named is strictly better than silent, and does not depend on
   the writer existing.

## Contract consequences accepted with the code

- Consumers must preserve the code, its repository-relative path, its
  dispatchability, and its next action (`workspace-routing-invariants:60`).
- The code lands with rows in `packs/core/.apm/skills/workspace-status/SKILL.md`
  and `guides/core/reference/workspace-toml-schema.md` in the same commit,
  because `tests/roster/test_workspace_status_projection.py:485-495` checks a
  superset over `set(engine._FINDING_NEXT_ACTIONS)` across both homes.
- `workspace-routing-invariants` is frozen, so its § *Canonical findings* table
  is not edited. This record is the governance artifact instead.
