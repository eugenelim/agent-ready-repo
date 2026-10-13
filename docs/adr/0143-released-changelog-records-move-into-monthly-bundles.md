# ADR-0143: Released changelog records move into monthly bundles

- **Status:** Accepted
- **Date:** 2026-10-03
- **Areas:** documentation, tooling
- **Reversibility:** high
- **Decision-makers:** Platform Core maintainers
- **Supersedes:** none
- **Supersedes in part:** ADR-0123 D2,D4,D6
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0123 (the fragment decision this narrows — D1, D3, D5 and D7 hold unchanged); ADR-0112 (generated corpus views stay generated or absent)

## Decision summary

- **Decision:** We will move released changelog fragments into append-only, byte-exact monthly bundle parts through a validated compaction command, while every new update is still authored as its own fragment.
- **Because:** the build pays a fixed cost for every loose fragment, and bundles cap the loose count, keeping the fragment layout well under its 10% build-cost bar as history grows.
- **Applies to:** `docs/product/changelog.d/`, the new `docs/product/changelog.months/`, the new retraction list, the record reader and validator in `tools/changelog.py`, every consumer of the record set, and the release checklist.
- **Tradeoff accepted:** a bundled record can only be retracted whole, never edited, and its repository path changes once.
- **Revisit if:** a valid three-arm pass with at least the loose-fragment ceiling's count of released fragments loose measures the fragment layout at 5% or more, in which case lower the ceiling; or bundle parts start conflicting with ordinary pull requests, in which case revisit the part key.

## Context

ADR-0123 moved product changelog authoring to one file per update, so that
concurrent pull requests stop conflicting. That result holds: 20 synthetic
branches adding fragments produce 0 conflicting pairs out of 190, against 190
of 190 for the shared file.

The layout's cost grows with the number of files. § 7 Build performance
requires it to cost under 10% more than the same records held in one file, at
ten times today's 330 released entries. Pass 5, the valid quiet-machine
measurement on 2026-10-03, measured **+12.12%**: a `make site-build` median of
83.83 s for 2,970 fragments against 74.77 s for one file.

Four attribution spikes on pass 5's exact corpus located the gap. They are
recorded in the build-cost report under "Bundle attribution spikes". **Their
figures were taken under load averages of 20–170. They are attribution, not
results.**

- **The whole gap is the changelog projection.** Split into its three build
  steps, the projection took a median 13.89 s for fragments against 6.65 s for
  one file. The web and docs builds were not slower for fragments.
- **About 3 s of it is one defect.** The reader reloads the file-safety helper
  once per fragment, 2,971 times. Loading it once per projection saved a paired
  median of 3.07 s with byte-identical output. That fix belongs to plan task
  T16 inside ADR-0123, and this ADR does not decide it.
- **The rest scales with the number of loose fragments.** With the helper
  loaded once and the remaining records grouped into monthly files, the
  projection took these medians, each with byte-identical output:

  | Loose fragments | Projection |
  | --- | --- |
  | 2,970 | 5.42 s |
  | 1,000 | 2.79 s |
  | 300 | 1.46 s |
  | 0 | 0.41 s |

  That is about 1.6 ms per loose fragment, plus about 1 s whenever any are
  loose. The one-file projection took about 0.9 s.

**Why bundles, given the helper fix.** The bar is a ratio, and the monolith
grows too. From pass 5, the monolith adds about 19.7 ms of build per released
record: (74.77 − 16.17) / 2,970. A loose fragment adds about 1.7–2.0 ms on top.
So with the helper fix alone, the fragment layout's overhead tends toward
1.7–2.0 / 19.7 ≈ 8.6–10.2% as history grows. That is at or near the bar, with
no margin for noise.

A cap on loose fragments makes the overhead fall as history grows instead.
Scaled against pass 5's monolith build, the table above estimates about 6%
fully loose, 2.5% at 1,000 loose and 0.8% at 300. Those are projection-only
gaps. A whole-build basis, which adds pass 5's roughly 0.8 s of other gap,
gives about 8% fully loose and 3–4% at the ceiling. Both stay under the 5%
revisit line at the ceiling. The other figures stay spike estimates taken
under load.

Plan task T18 then measured a valid whole build on a quiet machine with 1,000
released fragments loose: **+7.22%**. That clears the 10% bar, but it reached
this ADR's own 5% revisit line, because the whole build costs more per loose
fragment than the projection-only spikes showed. So the ceiling is 500, not
the 1,000 first proposed. T18's figure bounds the 500 ceiling from above, since
fewer loose fragments cost less. The owner chose this headroom on 2026-10-03. It is a
judgement, not a § 7 requirement.

Three constraints shape the design:

- **Merge independence must survive.** An ordinary pull request still adds one
  new file and touches no shared one.
- **Published identity must not move silently.** `/now/<anchor>/`, the Atom
  `<id>` and the anchor in the complete view are permanent. A record's
  repository path is not published: no output reads it.
- **Pre-cutover history stays frozen.** ADR-0123 D1 still keeps
  `docs/product/changelog.md` read-only.

## Decision

**We will move released fragment records into append-only monthly bundle parts
that hold each record's exact original bytes, written only by validated
`compact` and `retract` commands; every new update is still authored as its
own fragment.**

What this narrows in ADR-0123:

- **ADR-0123 D2** said a post-cutover update lives at
  `docs/product/changelog.d/<id>.md`. Authoring still happens there. A released
  record may later live in a bundle part.
- **ADR-0123 D4** said the assembler reads frozen history and validated
  fragments. It also reads bundled records. Assembly itself stays offline, with
  no clock and no Git-history dependency. Only validation reads the merge-base
  tree, as it already does for fragments.
- **ADR-0123 D6** excluded any tracked combined changelog. Bundle parts are
  tracked files holding many records. They are authoring source, not a
  generated view. Only `compact` and `retract` write them, and no ordinary pull
  request touches them, so nothing on the merge-queue-critical path changes.

The binding constraints follow. The spec's acceptance criteria own their
mechanics and fixtures.

- **D1:** Authoring is unchanged. A new update is authored only as a fragment.
  A record whose `id` existed nowhere at the merge base may not appear in a
  bundle part.
- **D2:** A record's identity is its envelope `id`, in either form. A
  fragment's filename stem equals its `id`. A bundled record's part month
  equals the month of its envelope `date`. The spec's AC5 already forbids
  changing a merged record's `date`, so no release transition can move a
  record between months.
- **D3:** Parts live in `docs/product/changelog.months/` and are named
  `YYYY-MM-NN.bundle`, with a real month and a unique two-digit `NN`. Any other
  entry in that directory is refused. The `.bundle` extension keeps parts out
  of Markdown tooling.
- **D4:** A part is a sequence of records. Each record is an exact separator
  line, `+++ record +++`, followed by one fragment's exact bytes.
  - Records are UTF-8, LF-only and LF-terminated.
  - No record line equals the separator. The same rule binds every fragment,
    so any fragment can be bundled unchanged.
  - Records within a part are in canonical order, `date` descending then `id`
    ascending.
- **D5:** Parts are append-only. Each `compact` run for a month writes new
  parts numbered after that month's highest `NN`, each within the existing
  1,048,576-byte per-file bound. Only retraction (D7) changes an existing part.
  Order across parts carries no meaning, because assembly sorts every record.
- **D6:** A bundled record is byte-immutable. Validation compares the
  merge-base record set with the current one by `id`, never through Git rename
  pairing.
  - It reads from Git only the entries whose object id differs from the id
    computed over the bytes the reader already loaded, in the object format
    `git rev-parse --show-object-format` reports. A mismatch costs only an
    extra read.
  - It refuses a duplicate `id` across forms.
  - It refuses a bundled record whose bytes differ from its merge-base bytes,
    whether it was a fragment or a bundled record there.
  - It refuses a merge-base bundled record that is missing and not newly
    retracted.
  - It refuses a change to any record's `packages`, `date` or `id`.
  - In a change that adds a part, it refuses a merge-base fragment that is
    missing and not bundled.
  - The comparison runs even when either directory is absent or empty, and any
    Git failure refuses.
  - Deleting a loose fragment outside a part-adding change stays allowed, as
    it is today.
- **D7:** Retraction is the only way to remove a bundled record.
  - `python3 tools/changelog.py retract --id <id> --category <category>`
    removes the record from its part and appends one entry to
    `docs/product/changelog-retractions.toml`.
  - The category is one of `credential`, `personal-data`, `legal` and `other`.
    There is no free text, so the list cannot repeat the content it retracts.
  - The list is append-only against the merge base.
  - A retracted `id` may never reappear in either form.
  - A changed part must equal its merge-base bytes minus exactly the records
    newly listed in that change.
  - A part whose last record is retracted is deleted, leaving a gap in `NN`.
  - Retraction stops future publication only. Git history, feed readers and
    forks keep what was published. A leaked credential is rotated first, and any
    purge of history follows the repository's security workflow.
  - A corrected version is a new fragment with a new `id` and anchor.
- **D8:** Compaction is `python3 tools/changelog.py compact --month YYYY-MM`.
  - It moves only fragments dated in that month that are released against the
    build's released-version inventory. Pending fragments stay where they are.
  - It reads no clock.
  - It plans and validates the new record set in memory, then writes new parts
    inside a validated, non-link directory and re-reads them.
  - Only then does it delete the fragments it bundled.
  - A failure before any deletion removes the parts it created. A failure
    during deletion leaves the parts in place. Rerunning the command for that
    month then completes the deletions. Every record stays present in at least
    one form throughout.
  - A fragment too large to fit a part with its separator stays a fragment,
    and the command reports it.
- **D9:** The release checklist in `packs/AGENTS.local.md` runs `compact` for
  each closed month that has released fragments loose. `tools/build-site.py`,
  which every site build and the `pages.yml` job run, does two things:
  - it warns above 375 released loose fragments;
  - it refuses to build above 500;
  - it warns above 250 pending fragments.

  Compaction cannot move a pending fragment, so pending fragments sit outside
  the ceiling and outside its measured worst case. Their warning makes a
  version that is never released visible.

  At about 165 updates a month the warning comes after about two and a half
  months of missed compaction, and the refusal after about three. A compaction can ride in the same pull request as an
  urgent change.
- **D10:** Storage form never changes output. One reader in `tools/changelog.py`
  returns frozen history, bundled records and fragments as one model.
  - Every consumer calls it without a substitute directory enumerator, helper
    handle or Git runner: `tools/build-site.py`, `tools/check-core-release.py`,
    `tools/repo/check_release_impact.py` and the `render` command.
  - The complete view and `/now/` payload are byte-identical whichever form
    holds a record.
  - Records across both forms are capped at 65,536.
  - Every part, merge-base blob and the retraction list is read through a
    size-checked bound of 1,048,576 bytes.

## Decision drivers

- **Build-cost headroom.** The fragment layout should stay well under the § 7
  bar as history grows, not merely under it at ten times today's count.
- **Merge independence.** Ordinary pull requests touch only their own new file.
- **Published identity permanence.** A bundled record's anchor, URL segment and
  Atom `<id>` disappear only through an explicit, listed retraction.
- **Mechanical content assurance.** A compaction diff is too large to review by
  eye, so validation, not review, must prove nothing changed or went missing.
- **Operational restraint.** No bot writer, merge driver, protected-branch
  bypass or clock dependency.

## Consequences

**Positive:**

- The loose-fragment count is capped at 500. History lives in about one or
  two parts per month: about 6 parts at ten times today's rate.
- Plan task T18 measured the build overhead at +7.22% with 1,000 released
  fragments loose, on a quiet machine, against +12.12% for the fragment layout
  before bundles. That figure is an upper bound for the 500 ceiling, which
  admits fewer loose fragments.
- Ordinary pull requests are unchanged, so ADR-0123's merge-independence result
  still applies to them.
- Outside a retraction, no part is ever rewritten, so two ordinary pull
  requests can never edit the same part.
- Validation now sees a deleted or altered bundled record, which today's
  path-based check cannot.

**Negative:**

- A bundled record cannot be corrected in place. A correction is a retraction
  plus a new fragment, which moves the record's published URL.
- A record's repository path changes once. A GitHub link to
  `docs/product/changelog.d/<id>.md` stops resolving at compaction. Published
  links are unaffected.
- A pull request editing a fragment's body, against a concurrent compaction of
  that month, either reports a modify/delete conflict or, where Git treats a
  one-record part as a rename and merges cleanly, leaves a result `validate`
  refuses as a bundled record edited in place. Either way the edit never lands
  silently. After rebasing, the record is bundled, and the edit becomes a
  retraction.
- Two concurrent compactions of one month both create the same next part name
  and conflict. That case is limited to release work.
- Two concurrent retractions both append to the retraction list and conflict.
  That case is limited to incident work.
- The validator grows a second storage form, a container parser, an id-keyed
  merge-base comparison, Git object reads and a retraction list.
- Deleting a loose, released fragment still unpublishes it silently, as it
  does today. Only bundled records gain that protection.
- If compaction lapses for about three months, the site build stops until
  someone compacts.
- Compaction can be undone without loss. Writing each record's bytes back to
  `changelog.d/<id>.md` restores the original files exactly. That would need
  its own command and a change to D6.

**Revisit if:** a valid three-arm pass with at least the loose-fragment ceiling's count of released fragments loose measures the fragment layout at 5% or more, in which case lower the ceiling; or bundle parts start conflicting with ordinary pull requests, in which case revisit the part key.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:**
  - the spec's per-rule fixtures pass;
  - a month compacted twice, an interrupted compaction rerun, and a retraction
    each leave every other record's output byte-identical;
  - a pull request that leaves the record set unchanged reads no Git blobs;
  - a valid three-arm pass with at least the ceiling's count of released fragments loose, no
    pending fragments, and the rest bundled meets the § 7 Build performance
    bar;
  - the merge replay keeps 0 of 190 conflicting fragment pairs with parts
    present on the base.
- **Owner:** the `build-check` gate, the `pages.yml` build, the release
  checklist, and Platform Core maintainers.

## Alternatives considered

- **Load the helper once per projection and stop there.** This is necessary,
  but it leaves no headroom. It lands in T16 regardless. Alone it measures
  about 6% to 8% at ten times today's count, depending on the estimate, tending toward 8.6–10.2% as history
  grows, with nothing to reset it.
- **Append-only parts with no month key, one per compaction run.** Rejected
  against operational restraint: a month key lets a maintainer find a record by
  date and compact a named, closed unit. It also bounds the part count by
  months rather than by runs. Its only extra cost is D2's part-month binding.
- **Month parts rewritten in canonical order on every compaction.** Rejected
  against mechanical content assurance: each rewrite moves existing records
  between parts. Append-only parts never touch a record once written.
- **Fold released fragments back into `docs/product/changelog.md`.** Rejected
  against published identity: the frozen file renders monolith headings, whose
  anchors the slugger derives and can renumber, and ADR-0123 D1 freezes it.
- **Keep only the last seven days as fragments.** Rejected against operational
  restraint: an age cutoff needs a clock or a scheduled writer.
- **One file per month with a raised byte bound.** Rejected against the
  confinement contract: a busy month at ten times today's rate is about 3.9 MB.
  Raising the bound is an `Ask first` threshold change that parts make
  unnecessary.
- **A JSON or binary container.** Rejected against mechanical content
  assurance: escaping changes record bytes, so equality with the merge-base
  fragment can no longer be checked byte for byte.
- **A build-only cache or consolidated input.** Rejected against ADR-0123 D5
  and the spec's no-cache rule: the build would read a derived artifact or keep
  state between projections.
- **One confined directory read in place of per-file reads.** Rejected against
  ownership: the blessed helper reads one regular file per call, and changing a
  shared security helper to serve one consumer is out of proportion.
- **Have the build compact automatically.** Rejected against ADR-0123 D5 and
  D6: the build would write tracked source.

## Errata

- **2026-10-04 — D7's "security workflow".** D7 says a history purge follows
  the repository's security workflow. The repository has no incident or
  history-purge procedure. The `retract` procedure in `docs/product/AGENTS.md`
  states what holds instead:
  - contain or rotate a leaked credential first;
  - the retraction commit's diff, Git history, forks and feed readers still
    disclose the retracted bytes;
  - any history rewrite is a separate decision for the owner.

  This clarifies D7 and does not change what it decides.

## References

- [`docs/product/research/changelog-fragment-build-cost.md`](../product/research/changelog-fragment-build-cost.md)
  — pass 5, the valid +12.12% measurement, and the bundle attribution spikes.
- [`docs/specs/product-changelog-fragments/notes/adr-0143-design-review.md`](../specs/product-changelog-fragments/notes/adr-0143-design-review.md)
  — the three-lens design review: adversarial, architecture and security.
- [`docs/architecture/changelog-fragment-source.md`](../architecture/changelog-fragment-source.md)
  — the § 2, § 4, § 6, § 7 and § 8 rows this amends.
- [`docs/specs/product-changelog-fragments/spec.md`](../specs/product-changelog-fragments/spec.md)
  — AC5, which D2 relies on, and the amended acceptance criteria.
- ADR-0123 — the fragment decision this narrows.
