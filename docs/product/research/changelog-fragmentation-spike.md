# Changelog fragmentation — feasibility spike

Throwaway prototype testing whether `docs/product/changelog.md` can be authored as
one file per entry and assembled at build, closing the open question left by
[the append-log fragmentation survey](append-log-fragmentation-survey.md).

- **Run date:** 2026-09-13
- **Owner:** eugenelim, Platform Core maintainer
- **Base:** `4c924e068`, 273 parsed release entries, 465,239 bytes
- **Verdict:** feasible, with one design constraint the survey did not anticipate —
  see [Verdict](#verdict)
- **Scope:** evidence only. No production code, schema, or migration was written.
  The prototype lives in a scratch directory and is not part of the repository.
- **Compare against:**
  [Changelog collector and generator — evaluation spike](changelog-collector-generator-spike.md),
  which evaluates drafting entries from commit history bounded by version bumps.
  It is a third candidate, not a replacement: the results below still hold, and
  that spike's own evidence notes this changelog requires highlights to be written
  in the implementation PR — which favours a per-PR artifact. Read the "next
  decision" below as a three-way choice.

## What this spike tests

Three falsifiable questions, chosen because each one could have killed the idea on its own:

1. **Round-trip.** Can a typed renderer that owns every heading level and every
   blank-line separator reproduce the current file byte for byte, given only
   per-entry prose bodies and typed identity fields?
2. **Projection parity.** Does the `/now/` projection produce identical output from
   the assembled file?
3. **Invariant by construction.** Is the "released sections are free-standing"
   rule genuinely unrepresentable in the fragment model, or merely relocated?

A fourth question surfaced during the run and turned out to be the load-bearing
one: **can the file's order be derived at all?**

## Method

The prototype imports `tools/build-site.py` and reuses its scanner, so the split
agrees with production about which `##` lines are real headings. A naive `^## `
scan finds 219 headings; the fence- and comment-aware scan finds 218. The single
difference is line 7545, the commented-out `## [1.0.0] — YYYY-MM-DD` release
template at the foot of the file, which a naive split would turn into a fragment.

The split produces a 52-line preamble plus 218 top-level fragments (214 release
entries, 4 `[Unreleased]` sections). Each fragment is a typed record: kind, title,
packages, date, and the verbatim prose body. The renderer emits the heading level
and all separators itself; the author supplies only the body.

Every figure in the Results sections below is produced by one script,
`spike_evidence.py`, whose retained stdout is the evidence of record. Counts that
appear only in framing prose (how many changelogs exist, how large the prototype
is) are not in that file. The prototype is throwaway and lives
outside the repository, so a reader checking these numbers re-runs that script
rather than trusting the prose. Figures derived from Git — the commit count and
the hunk census — are reproducible directly:

```bash
git rev-list --count --since='30 days ago' HEAD -- docs/product/changelog.md
git log --since='30 days ago' -p --unified=0 -- docs/product/changelog.md | grep -c '^@@'
```

## Result 1 — the round-trip is byte-faithful except at eight defect sites

The renderer reproduces 465,235 of 465,239 bytes. The entire delta is **8 lines at
8 sites**, and every one is a pre-existing separator defect in the current file:

Line numbers below anchor the affected **heading** in `docs/product/changelog.md`
at `4c924e068`:

| Heading line | Entry | Defect |
| ---: | --- | --- |
| 287 | `[governance-extras][0.10.6]` | **no blank line before the heading** — the section is not free-standing |
| 796 | `[core][2.25.3]` | doubled blank line before the heading |
| 838 | `[core][2.25.1]` | doubled blank line before the heading |
| 969 | `[core][2.25.0]` | doubled blank line before the heading |
| 987 | `[core][2.24.4]` | doubled blank line before the heading |
| 1253 | `[core][2.19.0]` | doubled blank line before the heading |
| 1275 | `[core][2.18.2]` | doubled blank line before the heading |
| 5344 | `[Unreleased]` (third of four) | no blank line after the heading |

The first row is the same defect class described as having reached the published
page this session. All eight were live on `main` at this spike's base.

> **Superseded on 2026-09-13.** The instances live at this spike's base were
> normalized, and
> `tools/test_build_site_routing.py::test_every_changelog_section_is_separated`
> now gates the class at every heading in `docs/product/changelog.md`. Every
> statement in this section about live defects and about no gate existing
> describes the base revision, not the current tree.

**No located gate detects any of them.** Stated precisely, because the broader
negative is false: the docs site *does* configure remark, via `remarkPlugins` in
`docs-site/astro.config.ts`. What does not exist is any blank-line rule — no
markdownlint configuration, and no `MD022` / `blanks-around-headings` rule
anywhere in the tree. A search of the test suite for assertions on changelog
separator structure returned none; the tests that name the changelog check
version matching, nesting, link rewriting, and `/now/` projection content.

So the round-trip does not merely pass — it *locates* the drift. A renderer that
normalizes by construction would have prevented all eight.

## Result 2 — `/now/` projection parity is exact

Parsing the assembled file through `parse_changelog_releases` returns records
identical to the original: 273 entries, identical diagnostics, and an identical
publishable payload of 99 entries carrying `Highlights`.

This also sharpens where the free-standing invariant actually bites. The eight
separator defects change **nothing** in the `/now/` projection — its parser is
structural and blank-line blind. The harm is at the Markdown rendering and human
review layer, not the projection. Any future gate must therefore read the
Markdown rather than the projection; a `/now/` parity assertion would pass
straight through all eight defects.

> **Corrected on 2026-09-13.** The rendering half of that sentence is wrong.
> Rendered through CommonMark, a welded heading and a double-spaced one produce
> byte-identical HTML, so the harm is at the source-text and human-review layer
> only. This answers the known-unknown below, and it is why the gate that
> shipped that day reads source text.

## Result 3 — the invariant holds only if the *renderer* normalizes

The first mutation attempt failed, and the failure is the most useful result in
this spike.

**Experiment A.** Give all 218 fragments stray blank lines at both ends of their
bodies — the exact authoring edit that produces the defect in a monolith.

- First design: the *splitter* stripped body edges and the renderer emitted them
  verbatim. Result: the defect **leaked into the output**. The invariant was an
  accident of how the prototype read the old file, not a property of the model.
- Corrected design: normalization moved into the renderer, where a fragment
  author's bytes actually arrive. Result: output **identical** across all 218
  mutated fragments. The defect is unrepresentable by authoring.

The design requirement this yields is specific and easy to get wrong: *normalize
at assembly, never at ingest*. A renderer that trusts fragment bytes reintroduces
the whole problem while looking correct against a round-trip test.

**Experiment B** is the mutation proof for the golden test. Deleting the single
line in the renderer that emits the pre-heading blank changes 218 headings and
218 bytes, so a round-trip golden test does fail under mutation. The test would be
real.

## Result 4 — neither tested field-derived order reproduces the file, and that is the binding constraint

The survey assumed order could be derived from typed fields. Two derivations were
tested against the 214 free-standing entries; neither reproduces the file:

| Ordering scheme | Entries landing at a different index | Adjacent pairs inverted |
| --- | ---: | ---: |
| Stable sort by date desc (ties keep source order) | 80 / 214 | 10 |
| Total order from fields only (date desc, artifact desc) | 176 / 214 | 71 |

- **209 of 214 entries (98%) share their release date with at least one other
  entry.** The busiest single date carries 19 entries. Date orders almost nothing.
- The current file is not even in date order: **10 adjacent pairs are date
  inversions**, where an entry dated later sits below one dated earlier. Whether
  each was intended or accidental was not determined.
- A field-derived total order moves **82% of the file**.

The stable-sort row is a trap worth naming: it looks cheap, but stability needs a
source sequence to be stable *against*, and fragmenting the file is exactly what
destroys that sequence. It is not available in the target design.

So, for the derivations tested, the order must be **stored, not derived** — and a stored order key is precisely
the thing that collides across branches, which is the problem fragmentation was
meant to solve. Taken alone this is close to fatal.

## A hypothesis that would resolve it — assign order at release, not at authoring

This section is a **design hypothesis, not a result.** The spike measured that
neither tested derivation reproduces the order; it did not measure when the
ordering judgement is made in this repository.

The hypothesis: ordering is decided when a release is cut, and release assembly
is already serialized. The survey's Finding 3 establishes the second half for the
surveyed tools — every one of their collect/batch/build steps rewrites a shared
artifact under a single owner. It does not establish it for *this* repository's
release workflow, which was not examined.

If the hypothesis holds, the file splits cleanly:

- **Pending entries** — authored on concurrent feature branches, carry no order
  at all, live one-file-per-entry. This is where the conflicts are.
- **Released sections** — ordered once by editorial judgement at release time,
  then frozen. Their order is history, stored explicitly, and never recomputed.

The churn measurement is consistent with the split, within a named limit. Over
the last 30 days, **216 commits touched `docs/product/changelog.md`**, producing
251 hunks, bucketed by the hunk's start line in the new file:

| Hunk start line | Hunks | Share |
| --- | ---: | ---: |
| Before 120 | 207 | 82% |
| 120–399 | 33 | 13% |
| 400 or later | 11 | 4% |

**What this does and does not show.** It shows churn is concentrated at the head
of the file: the remaining ~95% of the file is effectively immutable, which is
what the survey's migration finding recommends leaving alone as a frozen
baseline. It does **not** show that 82% of hunks are pending-entry edits. The
sub-120 bucket also contains edits to the 52-line preamble — the authoring-rules
header — and the census did not classify hunks semantically. Read 82% as
*head-of-file churn*, not as the share fragmentation would remove.

That a top-of-file insertion genuinely conflicts is not assumed here. Two branches
each adding one entry at the insertion point, merged with `git merge-file`, exits
1 with three conflict markers and both entries stacked in a single hunk.

## Verdict

Question by question, and one of them is a genuine negative:

| # | Question | Result |
| --- | --- | --- |
| 1 | Byte-for-byte reproduction of the current file | **No.** 465,235 vs 465,239 bytes; 8 lines differ |
| 2 | `/now/` projection parity | **Yes.** 273 records and 99 highlight payloads identical |
| 3 | Separator defect unrepresentable by construction | **Yes**, conditional on the renderer normalizing |

Question 1's negative is the useful kind. The renderer reproduces the file
*modulo canonicalization*, and all 8 divergences are pre-existing defects in the
source rather than renderer errors. But the question as posed asked for byte
identity against the current file, and the answer to that is no.

**Feasible, with one shape ruled out on the evidence gathered.** Fragmenting the
*whole* changelog fails under both ordering schemes tested.

The measured facts: 209 of 214 entries (98%) share their release date; a stable
date-descending order moves 80 of 214 entries; a date-plus-artifact total order
moves 176. Two schemes are not all schemes — the measurement rules out *these*
derivations, not every conceivable one. [inference] What follows from it is that
reproducing the exact current order requires order to be **stored**, unless some
other derivation is separately proved against this corpus.

That the residual order is *editorial judgement* is a further inference, from
those numbers plus 10 date inversions whose intent was not determined. Plausible,
not measured. [inference]

Fragmenting only the **pending** entries **remains a plausible next design**, and
is the only shape still standing. It is not yet shown to work: the aggregation of
pending fragments into the `[Unreleased]` groups is exactly the part this spike
did not examine.

## What this spike did not test

- **Any production code.** No schema, renderer, gate, or migration was written.
  The measured renderer is a throwaway prototype that handles this one file, not
  an implementation with error handling or a fragment format.
- **The `[Unreleased]` region's own structure.** Its four sections carry ordinary
  `### Added` / `### Fixed` groups; how pending fragments merge into those groups
  at release time is unexamined and is where the real design work sits.
- **Fragment naming.** Left open deliberately. Note that `(artifact, version)` is
  *not* a unique key — `[core][2.3.0]` appears as two separate entries, both
  dated 2026-08-07 — so the obvious `<artifact>-<version>.md` scheme is already
  known to collide.
- **Randomized fragment enumeration.** The prototype assembles fragments in
  source order. Determinism under shuffled input, which the survey's known-unknown
  asks for, was not tested.
- **Review ergonomics.** Whether a release PR showing N fragment files reviews
  better or worse than one changelog hunk was not measured.
- **The two adopter-facing changelogs** (`packages/*/CHANGELOG.md`) and the
  `packs/core/seeds/` template, which were out of scope by instruction.

## Conflict rate, measured 2026-09-13

Closes this document's first known unknown. Every count below except the
abandoned-branch paragraph is printed by `tools/measure-changelog-conflicts.py`,
the evidence of record:

```bash
python3 tools/measure-changelog-conflicts.py --tip 0e339c978 --from d1bc469d5
```

The abandoned-branch figures need the forge, so they are reproduced separately:

```bash
gh pr list --state closed --limit 300 \
  --json number,author,closedAt,mergedAt,files \
  --jq '.[] | select(.mergedAt == null) | select(.closedAt > "2026-08-14")'
```

**Count the rebases, not the merges.** All 138 merges into `main` in the 30 days
to 2026-09-13 are linear — `merge-base(P1, P2) == P1` in every one. Each branch
is rebased or updated onto main before it merges, so `git merge-tree P1 P2`
conflicts on nothing and a naive merge replay returns **zero**. That zero
measures the workflow's serialization, not an absent problem: the cost is paid
during the rebase, which leaves no commit of its own.

The script reconstructs that rebase. The fork point `A` is the newest mainline
commit whose *committer* date is strictly before the branch's earliest *author*
date — author dates on the branch side because they survive a rebase, committer
dates on the mainline side because they are that commit's position — and
`git merge-tree --merge-base=P1 A P2` then conflicts on exactly the regions where
main's `A..P1` work and the branch's work touch the same lines. 96 of the 138
merges resolve a fork point behind the mainline parent. The other 42 are
*estimated* to have started from main's tip — that is what the date comparison
says, not an observation of when the branch was cut — and they are excluded from
the denominator below.

| | `docs/product/changelog.md` | `workspace.toml` |
| --- | ---: | ---: |
| Commits touching it in the window | 224 | 352 |
| Merges where the branch edited it **and** main moved it | 43 | 51 |
| ...of those, the replay conflicts textually | **39 (91%)** | **20 (39%)** |
| Share of the 96 replayed merges | 41% | 21% |

The 39 and the 224 are different units — 39 conflicting *merges* against 224
*commits* — so they are not a ratio. The window is a commit range rather than a
date so that the invocation above returns these figures on every run; successive
runs of an earlier date-windowed version disagreed, and the cause was not
established. Result 4's 216 came from a rolling 30-day window with no recorded
command, so it is not directly comparable.

**Negative control.** 53 merges where the two sides did not both touch the
changelog produce zero conflicts on it; 45 and zero for `workspace.toml`. The
replay does not manufacture conflicts.

**Mechanism, and its limit.** All 39 conflicting changelog rebases have both
sides adding a `## [` release heading — the same-anchor collision Result 2
already showed `git merge-file` rejects. So do all 4 of the exposed rebases that
did *not* conflict, so the anchor explains the class but does not discriminate
within it.

Falling **one** commit behind is enough: the conflicting rebases skip 1 to 32
mainline commits, and 2 of them conflicted at one.

**Abandoned branches add nothing here.** 12 pull requests were closed unmerged in
the window, 8 of them dependabot. None touched `docs/product/changelog.md`.
Three touched `workspace.toml`; whether those conflicted was not replayed
here, because the replay above covers merged branches only.

**Limits, in both directions, none quantified.** A branch rebased more than once
counts as one event, which understates. The fork point is a date estimate that
errs both ways: too early for a branch carrying a cherry-picked or
upstream-authored commit, which widens `A..P1` and can manufacture overlap; too
late for a branch cut well before its first commit was authored, which hides
overlap and is also what drops the 42 excluded merges. So 39 is a measurement
under a stated estimator, not a bound in either direction.

**What it decides.** A separator gate closes a presentation defect class and
leaves this rate untouched; they answer different problems. The rate supports
fragmenting the changelog's pending entries. It does not transfer to
`workspace.toml`. There the same replay conflicts in 20 of 51 exposed rebases
(39%) — a larger exposed population than the changelog's 43, at well under half
the rate — and
[the survey](append-log-fragmentation-survey.md) rates the `.d` analogy as weak.

## Known unknowns

- **Partly answered on 2026-09-13** by [Conflict rate](#conflict-rate-measured-2026-09-13):
  **39 of the 43 rebases that had to replay a changelog edit conflicted (91%)**,
  over a window in which 224 commits touched the file. Note the unit: this bullet
  asked per *commit* and the replay answers per *merge*, so the two are not a
  ratio. "Incorrect manual resolutions", the question's third term, is not
  answered — a textual replay cannot see it.
- **Answered on 2026-09-13, No.** Do the separator defects change rendered HTML
  on the published page? Rendered through CommonMark, both defect shapes — a
  heading welded to its neighbour, and one preceded by a doubled blank line —
  produce byte-identical HTML to the correct form. Blank lines between blocks
  and blank lines around an ATX heading are both insignificant in CommonMark.
  The harm is therefore confined to the source text and human review, which is
  what the gate added that day checks.
- **Known-unknown:** Is the ordering judgement actually made at release time in
  this repository, as the hypothesis above assumes? Would be closed by: reading
  the release workflow and checking, across the 10 date inversions, whether the
  ordering decision appears in the release commit or in the authoring commit.
- **Unknowable:** Which order two entries released on the same day "really" had.
  Why not: 98% of entries share a date, no field records intra-day sequence, and
  10 adjacent pairs invert date order, so wall-clock order does not reconstruct
  the file either. No retained artifact records the intended sequence.

## Next decision, for the owner

The spike closes the feasibility question and narrows the design, but does not
choose. Three live options remain, and the evidence does not select between them:

1. **Add a separator gate and stop there** — the eight live defects were the only
   demonstrated harm when this spike ran, though
   [Conflict rate](#conflict-rate-measured-2026-09-13) has since demonstrated a
   second and larger one, and a renderer or linter closes them without any
   fragmentation, migration, or new directory. Materially the cheapest, and it
   closes the defect class that prompted this work.
2. **Fragment pending entries only** — targets the 82% head-of-file churn, leaves
   released history untouched as a frozen baseline, and buys a build step, a
   fragment format, and a drift gate.
3. **Collect and generate from commit history** — evaluated in the
   [collector/generator spike](changelog-collector-generator-spike.md). It would
   remove the shared file from feature branches, but only if the entry is written
   at release time, which this changelog's header currently forbids: highlights
   are written in the implementation PR. Under the present header the draft has
   to persist per-PR, and **if** that is a tracked per-PR file it is option 2's
   artifact with a different author.

Options 2 and 3 may therefore not be independent. Two locations would keep them
distinct, and no spike has assessed either: a pull-request release-note block, as
Kubernetes uses, which keeps the record out of the tree but in mutable hosting
metadata; or a commit trailer, which is immutable committed history but is
amended rather than reviewed as a file. So the first questions are whether writing
the entry at release time is acceptable at all, and if not, whether PR metadata or
a commit trailer is an acceptable home. Both measurements that sentence waited on now exist: the conflict rate above, and
the clean drafting score in
[the inputs spike](changelog-generator-quality-spike.md) Result 7. The choice
among the three options is now an owner decision, not a blocked one.
