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

## T9 — the closing corpus observation, run 2026-09-17

The corpus went from 8 finding lines over 4 record paths to 0. Command, run
against the projected copy the `check-adr-shape` chain step invokes:

    python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr
    read: 116  refused: 0  unreadable: 0      exit 0

Only two records were edited. `ADR-S010` is a mirror rule that reports from both
sides, so ADR-0042 and ADR-0109 each contributed a finding line without needing
a change; bare-tokening ADR-0023 and ADR-0050 and giving each a `Superseded by:`
field cleared all four `ADR-S010` lines along with both `ADR-S001` and both
`ADR-S007`. `check-adr-index` (`index-records.py --check docs/adr`) exits 0.

`tools/test_build_gate_chain.py`: 40 passed, 28 subtests, 21.8s — this is what
pins the step's presence and its `docs/adr` argv. The step body was also read
directly at `tools/repo/build_gate_chain.py:286-289` and matches the invocation
above, so the exit code recorded here is the step's own, not a proxy for it.

### `docs/adr/README.md` did not change, and that is the finding

AC-0013 asks that a supersession pointer render in the generated index. It
already did: rows 27 and 54 read `Superseded by ADR-0042` and `Superseded by
ADR-0109` both before and after, because `_status_token` stripped the link
markup out of the old compound `Status` value and arrived at the same text the
new field composition produces. The file has not been committed since an
unrelated change, and regenerating it is a no-op.

So the artifact cannot distinguish the two mechanisms, and AC-0013 is not
observable in it. The generator suite is the only thing pinning the new path.
Confirmed differentially rather than by reading the code: copying ADR-0023 into
a scratch directory and running the generator renders `Superseded by ADR-0042`;
deleting only its `Superseded by:` line and re-running renders a bare
`Superseded`. The field drives the cell.

Generator suite `tests/roster/test_index_records.py`: 48 passed, 2.46s, up from
44. The four added cases cover the composition, the missing-field fallback, the
`none` sentinel, and AC-0032's escaping. `cmp` confirms the two shipped
generator copies stay byte-identical, and both `.claude/` and `.agents/`
projections match their `packs/` source.

## T10 — the new record and ADR-0027's erratum, run 2026-09-17

### The new record: `docs/adr/0117-adr-shape-lint-ships-blocking-not-advisory.md`

Authored by walking `new-adr`'s procedure by hand against the projected
`.claude/skills/new-adr/SKILL.md` step order, rather than through the live
skill dispatcher (no interactive session here to hold the step-7 confirmation
gate open). `python3 .claude/skills/new-adr/scripts/next-ordinal.py docs/adr`
printed `0117`, and `--check docs/adr` reported "no duplicate ordinals" both
before and after the write. **Recording the allocated ordinal here, per the
task's instruction — the spec names this record by role
("the one new-format decision record"), not by number.**

Step 7's confirm-before-coining check was run, not skipped: scanning every
sibling record's `Areas` field (`grep -h "Areas:" docs/adr/*.md`) turned up 24
tokens already in use, including `governance` and `tooling`, so the drafted
`Areas: governance, tooling` value coined nothing and the explicit-confirmation
branch never fires. That is a true negative on the check, not an unexercised
one — the scan ran, found the value already covered, and the record proceeded
without asking. Exercising the branch where a real answer must be given (a
genuinely novel token) would need a separate fixture case in
`test_lint_adr_shape.py`, not a real corpus record — this repository's `Areas`
vocabulary is broad enough that a real, honest decision under governance/tooling
was never going to need one.

Subject, corrected: AC-0015 asks for "the ADR format decision," and RFC-0102's
own Follow-on artifacts list names this record by role — "An ADR recording
this format decision, authored in the new format, shipping with the lint as
its first fixture." The first draft of this record instead headlined the
blocking-vs-advisory rollout posture, which is a genuine and separately
settled decision but not RFC-0102's own format decision, and AC-0015 asks for
**one** record, not a second. Rewritten in place, same ordinal, to record
RFC-0102's actual decision — the metadata block is mechanically checkable
(RFC-0102 §§ 2–3) and acceptance's freeze binds prose, not metadata
(§ 4) — sourced from RFC-0102 §§ 2–5 directly rather than from memory. The
blocking-vs-advisory reasoning is kept, folded in as a Consequence and an
Alternative rather than the headline `Decision`. Renamed with `git mv` to
`0117-adr-metadata-is-mechanically-checkable-and-the-freeze-binds-prose.md` to
match; `git status --short` after the move showed only the rename (`R`), no
lingering empty directory.

**Pinned test — isolated single-record invocation (AC-0015), re-run against the corrected, renamed record:**

    mkdir -p <scratch>/adr-t10-isolated
    cp docs/adr/0117-adr-metadata-is-mechanically-checkable-and-the-freeze-binds-prose.md <scratch>/adr-t10-isolated/
    python3 .claude/skills/new-adr/scripts/lint-adr-shape.py <scratch>/adr-t10-isolated
    read: 1  refused: 0  unreadable: 0      exit 0

**What this isolated run proves, and what it does not.** All four supersession
fields on the new record are the `none` sentinel, so every per-record check
(`ADR-S001`–`ADR-S008`, `ADR-S011`–`ADR-S015`) ran against the record's own
content and is a real pass. The two mirror rules, `ADR-S009` (a cited D-ID
exists in the record it names) and `ADR-S010` (a supersession entry has its
mirrored counterpart), had nothing to pair against: with one record and no
non-`none` supersession field, both rules are vacuously satisfied rather than
exercised. A single-record directory cannot exercise either mirror rule
regardless of the record's content, unless the record cites a sibling that is
absent from the same directory — which would itself only prove the *absent*
branch, not the paired-mirror branch. That branch is what T2's and T3's fixture
suites cover; this run is the manual-QA instance the spec's Testing Strategy
asks for, over the real shipped lint and the real new record, not a substitute
for the fixture coverage of the mirror rules.

**Full-corpus re-run after the new record joined `docs/adr`:**

    python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr
    read: 117  refused: 0  unreadable: 0      exit 0

Up by exactly 1 from the 116 pre-T10 baseline (confirmed by re-running the
lint before making any change), all attributed to the new record; no other
corpus record's outcome changed.

### ADR-0027's erratum (AC-0016)

One dated `## Errata` entry appended after `## References`, at the position
every one of the eight pre-existing corpus records using `## Errata` already
uses (`0002`, `0013`, `0020`, `0022`, `0036`, `0061`, `0072`, `0079`). It
covers both facts the task names in one entry, dated 2026-09-17: that the
mechanical ADR-status lint this ADR's own `Confirmation` section deferred has
now shipped (citing RFC-0102 and the new ADR-0117 record of that decision),
and that `D5`'s forward-only-migration clause is overridden on RFC-0102's
authority, because the corpus — including this ADR's own frontmatter, which
already carried `Areas`, `Reversibility`, and all four supersession fields —
was migrated ahead of the lint shipping blocking.

**Was the convention usable, as the first real exercise of it?** Yes, and the
part expected to be awkward — picking the heading and deciding whether a
correction needs its own new supersession chain rather than an in-place
entry — was not. `new-adr/SKILL.md`'s "## Recording corrections (Errata)"
section fixes the heading to exactly `## Errata` and states plainly that a
changed decision is a new ADR, never an edit here; that left no judgment call
about *which* mechanism this correction needed. The corpus's eight pre-existing
`## Errata` sections (all predating this delivery, so the heading and the
dated-bold-headline entry shape were already established practice, not
something this delivery had to invent from the SKILL.md prose alone) gave a
real precedent for entry shape and placement, which is why the new entry above
matches their `**YYYY-MM-DD — headline.**` form.

One genuine ambiguity did surface, worth naming rather than papering over: the
convention states entries are "append-only" and a later entry supersedes an
earlier one "by being later," but says nothing about whether an erratum
entry may itself cite metadata-block fields that the `Live` zone still permits
to change after the entry is written (here, `Superseded by:` on a *different*
record, not this one). This record's erratum does not need that — it corrects
meaning, not a supersession pointer — so the gap did not block this task, but a
future erratum that does need to reference a still-mutable field would have no
stated rule for whether the erratum text itself must be treated as frozen
prose the moment it lands, or whether it may be read against the record's
current metadata. Left for whoever writes that erratum; not a defect in this
task's `Done when:`.

**Index regeneration (goal-based check), re-run after the ADR-0117 rewrite and rename:**

    python3 .claude/skills/new-adr/scripts/index-records.py --check docs/adr
    # exit 1 first: line 121 differed (old title/filename still on disk vs.
    # the corrected title/filename), naming exactly that mismatch
    python3 .claude/skills/new-adr/scripts/index-records.py docs/adr
    # exit 0
    python3 .claude/skills/new-adr/scripts/index-records.py --check docs/adr
    # exit 0

`docs/adr/README.md`'s `0117` row now reads the corrected title and links the
renamed file; no other row changed. `next-ordinal.py --check docs/adr` exits
0 (no duplicate ordinals) after the rename — the ordinal did not change, only
the filename and title did.

`tests/roster/test_index_records.py`: 48 passed (unchanged from T9 — T10 adds
no generator case). `tests/roster/test_lint_adr_shape_corpus.py`: 2 passed —
its partition assertion is computed from the live directory listing at run
time, so the new record is absorbed without a code or fixture change.
