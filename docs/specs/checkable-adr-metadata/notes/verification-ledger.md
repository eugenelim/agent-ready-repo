# Verification ledger — checkable-adr-metadata

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here.

## T6 — goal-based checks, run 2026-09-17

T6's `Tests` are goal-based and name this file as their home.

| Check | Verifies | Observed |
| --- | --- | --- |
| The write gate surfaces the `Areas` tokens in use in the target directory and requires an explicit answer before an unused token is coined | AC-0025 | present at `new-adr/SKILL.md:208-214`, step 7 "Preview and confirm — the write gate"; the scan and the explicit-answer requirement both run *before* the general preview, so coining does not ride the preview confirmation |
| `new-adr`'s SKILL.md defines the `## Errata` convention; `new-rfc`'s sole-home sentence names RFCs | AC-0026 | `## Recording corrections (Errata)` present; `new-rfc/SKILL.md` sole-home sentence narrowed to RFCs |
| `new-adr` SKILL.md body lines under 500, measured after the six-line YAML frontmatter | — | **365** (371 total − 6). Command: `F=…/new-adr/SKILL.md; echo $(( $(wc -l < $F) - $(awk 'NR>1 && /^---$/{print NR; exit}' $F) ))`. The plan's "It is 335 today" was the pre-T6 baseline, not a target; CAT-S003 warns above 500 and errors above 1000, so the criterion holds with 135 lines of headroom |

Pack suite `packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py`:
49 passed, 0.53s. `make lint-packs`: ok, 1 pre-existing INFO finding
(`CAT-L032`, an unsatisfied optional runtime dependency in `packs/core`, not
this delivery's). `make lint-ruff lint-mypy`: clean, 148 source files.

## Two repairs landing outside any task's pinned `Touches`

Both were found by reading AC-0023 and AC-0024 against their own surface sets
rather than against the task that happened to be running. Recorded here because
`Touches` is pinned (`plan.md:29-32`) and neither repair is inside the task that
owns the criterion.

**`new-adr/SKILL.md` stated the retired rule in two places T6's `Approach` did
not name.** T6's `Approach` named two line locations; AC-0023's predicate is
file-wide. The surviving text was the "Reversing a decision" bullet ("flip the
old ADR's status to `Superseded by ADR-NNNN` — status line only") and the
anti-pattern entry ("ADRs are immutable … never an edit"). The first also
carried the compound `Superseded by ADR-NNNN` status value that RFC-0102 § 2
splits into a bare `Status` token plus a `Superseded by:` field, so it was
teaching a shape the new lint rejects. AC-0023 is T7's to close, but T7's
`Touches` does not admit this file, so T7 could not have repaired the surface
its own search reads. Repaired under T6, whose `Touches` does admit it; T7's
pinned search is now satisfiable within T7's own `Touches`.

**The template's zone block was a different taxonomy from the one it names.**
`assets/adr.md` (T5, already committed) headed the block "Lifecycle zones" and
keyed all four names to `Status` values — "Frozen — Status is Deprecated or
Superseded: body **and metadata** are stable". RFC-0102 § 4 divides a record by
content, not by lifecycle: all four zones apply to every ADR at once, and the
scope paragraph states there is no grandfathered set and no format threshold.
The template's reading froze `Status` and the supersession fields on exactly the
records that still need them writable — the superseded ones — which contradicts
the `Live` zone and would have taught an author not to record a supersession
discovered later. Re-derived from the § 4 table, including the `Consulted` /
`Informed` no-zone carve-out. No task's live `Touches` admits `assets/adr.md`.

Neither repair changes a criterion; both make an existing criterion hold on a
surface it already named.
