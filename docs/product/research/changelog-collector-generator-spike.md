# Changelog collector and generator — evaluation spike

Evaluates a proposed alternative to fragmenting the changelog: a **collector**
that gathers repository changes, a **generator** that turns them into entries,
and a **bound** limiting each run to one window. Tests the design against this
repository's own history, and closes the attribution question left open by
[the fragmentation spike](changelog-fragmentation-spike.md).

- **Run date:** 2026-09-13
- **Owner:** eugenelim, Platform Core maintainer
- **Base:** `6848d547d`; changelog at 214 free-standing release entries
- **Verdict:** collector selection yes but its boundary rule is defective, generator permitted but untested, time-as-routing-key no — see [Verdict](#verdict). The boundary defect was measured later, in [the inputs spike](changelog-generator-quality-spike.md) Result 5.
- **Scope:** evidence only. No production code was written. The prototype is
  throwaway and lives outside the repository.
- **Supersedes:** nothing. It adds a third candidate alongside fragmentation and
  a separator gate; it does not replace either spike's results.

## The proposal, restated

Three parts, evaluated separately because they do not stand or fall together:

1. **Collector** — gather what changed in the repository, mechanically.
2. **Generator with logic** — turn the collected changes into changelog entries.
3. **Bounded to a time period** — run over one window at a time.

## How this relates to fragmentation

This is a **third candidate**, not a replacement. If a collector and generator
carried the whole job, fragments would be unnecessary — nobody would write the
changelog on a feature branch, so nothing could collide, and there would be no
fragment directory, assembler, drift gate, or migration to pay for.

Result 4 shows they do not carry the whole job, and one piece of repository
evidence cuts directly against release-time generation. The changelog's own
header requires that highlights be

> **Reviewed like code.** Write them in the same PR as the implementation,
> grounded in that diff and its verification evidence.

**That constraint may make the two designs converge — a hypothesis, not a
result.** If the draft and its highlights must exist in the implementation PR,
they have to persist somewhere per-PR, and two of the candidate locations are the
shared `changelog.md`, which reinstates exactly the feature-branch edit that
conflicts, and a separate per-PR file, which *is* a fragment whatever it is
called.

Two further locations exist and this spike evaluated neither:

- **Pull-request metadata** — a release-note block and labels on the PR itself,
  collected at release. The survey credits Kubernetes with exactly this shape. It
  satisfies "written in the same PR" without adding a tracked file, but it moves
  the durable record into mutable hosting metadata, which the survey already
  flags as a weaker source than a committed artifact.
- **A commit trailer** — a structured field in the commit message. Unlike PR
  metadata this *is* committed Git history, so it is immutable and travels with
  the repository, but it is amended rather than reviewed as a file and its
  standing under "reviewed like code" is untested.

So the conflict-removal claim above holds for a design that writes at release
time — which the header currently forbids — and possibly for a metadata- or
trailer-backed design that nobody here has assessed. Whether option 3 collapses
into option 2 is therefore open, and turns on those two locations. Choosing needs the
draft-acceptance measurement in [Known unknowns](#known-unknowns), the
conflict-rate measurement the fragmentation spike named, and an assessment of
per-PR metadata as a persistence site — none of which exists yet.

## Method and evidence

All figures below come from one script, `spike_collector_evidence.py`, run from
the repository root at base `6848d547d`; its stdout is the evidence of record.
The script prints its own classifier expressions and the complete miss list
rather than a sample, so a reader who cannot run it can still see what was
counted. Release records come from `tools/build-site.py`'s own
`parse_changelog_releases`, so the spike counts what the `/now/` projection sees.

An earlier attribution run did not path-filter the commit range. Its attribution
figures were wrong and made the design look unworkable; that run has been
discarded, its output deleted, and no figure from it appears in this document.

## Result 1 — the collector's raw material is richer than its output

| Source | Median length |
| --- | ---: |
| Commit subject | 73 chars |
| **Full commit message** | **1,114 chars** |
| Changelog bullet | 306 chars |

Measured over `--since='90 days ago'` ending at this document's base commit
`6848d547d`: **2,141 commits**, 1,998 of them (**93%**) carrying a body beyond the
subject.

Conventional-commit parsing uses a repository-specific loose classifier,
`^(\w+)(\([^)]*\))?(\+\w+(\([^)]*\))?)*!?:`, which accepts this repository's
compound `chore(core)+feat(core): …` subjects. It admits 1,841 of 2,141 (86%).
Strict Conventional Commits grammar, `^(\w+)(\([^)]+\))?!?: .`, admits 1,840 — so
the rounded share is the same either way. Loose type counts: `docs`=578, `fix`=481, `feat`=393,
`chore`=196, unparseable=300.

The subject line alone would not be enough — its maximum length, 156 chars, is
shorter than the *median* changelog bullet. The full message comfortably is.

What this establishes is **input sufficiency**: the candidate material exists, in
roughly the right volume, at the right granularity. 874 `feat`/`fix` commits
accompanied 1,023 top-level changelog bullets over the same 90 days, and the
per-entry measurement in Result 3 puts the median at **1.0 `feat`/`fix` commit
per bullet** — so the mapping is near one-to-one rather than a synthesis across
many commits.

What it does **not** establish is that a generator would draft well. Volume and
granularity are not semantic correspondence: no entry was generated and compared
against what shipped. Draftability stays undecided pending that comparison.
[inference]

## Result 2 — time alone cannot route a commit to an entry

A window defined by time cannot route a commit to an entry, because releases are
per-artifact and overlap heavily:

- **24 artifacts** carry independent versions (`core`=95 releases, `agentbundle`=26,
  `architect`=11, `product-engineering`=10, …).
- **26 of 36 release dates (72%) carry two or more artifacts.**
- One date carries **23**.

On 72% of release dates, a time window alone would have to guess which artifact a
given commit belongs to. The measurement rules out time as the *routing* key; it
does not rule out time as a *run* bound. A collector can still be invoked over a
period — what it cannot do is infer artifact identity from that period.

Routing needs the two keys Result 3 tests instead: artifact **paths**, and the
**version bump** as the window edge.

## Result 3 — path attribution works; the version-bump boundary is discoverable but not correct

This is the question that could have killed the design. Two halves — and the
first half measures only whether a boundary can be *found*, not whether it names
the right release. The inputs spike later measured that second question and the
answer is no; read this section against
[its Result 5](changelog-generator-quality-spike.md).

**Boundary discoverability.** Walking each artifact's manifest history
(`packs/<name>/pack.toml`, `packages/<name>/pyproject.toml`) for the commit that
first declared each version:

- **224 of 239 released `(artifact, version)` pairs — 94% — have a bump commit.**
  Discoverability is not correctness: the inputs spike later measured this rule
  selecting the wrong release's commits in 2 of 10 sampled windows, because
  manifest-declaration order is not release order once a version is renumbered.
- The 15 misses are all versions a manifest never declared. In full: `core`
  2.25.19, 2.25.17, 2.25.13, 2.25.9, 2.25.6, 2.24.4, 2.24.3, 2.24.2, 2.23.2,
  2.23.1, 2.18.2, 2.16.4, 2.15.3, 2.3.1, and `agentbundle` 0.43.0. Fourteen of
  the fifteen are `core`, which is consistent with versions superseded or
  re-derived before release, though the cause was not confirmed.

**Attribution.** For the 166 single-artifact entries where both the current and
previous boundary exist, filtering the bump-to-bump range by the artifact's own
subtree collapses it to a usable size:

| Window, progressively filtered | Median commits | Max |
| --- | ---: | ---: |
| Raw `prev-bump..this-bump` range | 31 | 1,183 |
| Filtered to the artifact's tree | **3** | 53 |
| …and to `feat:` / `fix:` | **2** | 41 |

Against the entries' actual bullet counts, that yields a **median of 1.0
`feat`/`fix` commit per changelog bullet** — the collector finds almost exactly
as many candidate changes as the entry contains.

The failure mode is bounded and measurable: **13 of 166 windows (8%) yield zero
`feat`/`fix` commits for an entry that does have bullets.** Those entries have no
*typed candidate* to draft from; whether some untyped commit in the window still
describes the change was not checked.

A worked case, checked by hand: `core` 2.25.18 → 2.25.20 spans 71 raw commits,
19 touching `packs/core`, 11 of those `feat`/`fix`, against 5 bullets across the
two changelog entries in that span.

## Result 4 — generation is permitted under human authority; its quality is untested

The repository already says this, in the changelog's own header:

> Entries can be drafted from conventional commits: `git log --oneline` filtered
> to `feat:` and `fix:` since the last tag is **a starting point, not a finished
> product. Rewrite for users, not contributors.**

So the proposal is the documented workflow with its two mechanical halves
automated. Whether a generator drafts the body *well* was never tested here or in
[the inputs spike](changelog-generator-quality-spike.md) — neither ran one. What
is established is where a generator may sit and what it must not decide. The hard
part is the `/now/` payload: **139 Highlights bullets across
99 entries, 91% opening with a bold outcome lede**, median 283 chars. A commit
message says what changed; a highlight says what someone can now do, and no
collector derives the second from the first.

Two qualifications the same header supplies, which keep this short of "a person
must type every highlight":

- It expressly permits AI-assisted drafting — "the reviewer, not the drafter, is
  the authority". So a generator may propose highlight prose; what it cannot do
  is be the authority for it.
- **Not every release owes one.** The header states that a released entry with no
  `Highlights` stays in the changelog and is simply absent from `/now/` — which
  matches the measurement: 99 of 214 entries carry them, not all 214.

The irreducible part is therefore the *decision* — whether this release changed
what a consumer can do, and whether the sentence says so — not the keystrokes.

Two further limits worth costing:

- **14% of commits (300 of 2,141) are not conventional-commit parseable** and are
  invisible to a type-filtered collector.
- **9 of 214 entries never appear as an added heading in history** — they were
  edited in place afterwards. A regenerator overwrites exactly that class of
  correction, which is the survey's first anti-pattern. The generated entry must
  be written once into the release commit and then frozen, never regenerated.

## Result 5 — commit order does not reconstruct the existing file

Testing whether commit order reproduces the changelog's entry order, for the 205
free-standing entries whose introducing commit is identifiable:

| Order source | Entries landing elsewhere | Adjacent contradictions |
| --- | ---: | ---: |
| Stable date-descending | 80 / 214 | 10 |
| **Commit order** | **107 / 205** | **22 / 204** |

Commit order is *worse* than date order at reproducing the file. The conclusion
matches the fragmentation spike's: **released history is not regenerable** and
stays a frozen baseline.

Forward-looking, the measurement says less than it first appears. The 22
contradictions establish only that the existing order departs from commit order in
roughly **1 adjacent pair in 9**. They do not establish *when* or *by whom* that
departure is decided.

The fragmentation spike left "ordering is decided at release time, by a single
owner" open as an explicit known-unknown, and the changelog header points the
other way — it names ordinary implementation-PR review as the only approval gate,
with no separate editorial step. So "a generator proposes an order and a human
reorders it in a serialized release PR" is a **compatibility hypothesis that
inherits that same open question**, not a conclusion this spike closes.

## Verdict

| Part | Verdict | Load-bearing evidence |
| --- | --- | --- |
| Collector | **Selection yes; boundary must move to the changelog heading** | 93% of commits carry a body; median message 1,114 chars vs 306-char bullet; 1.0 commit per bullet. The version-bump boundary resolves the *wrong release* (Result 5); the heading-commit rule never does, though it leaves 8 of 20 windows empty (Result 6) |
| Generator | **Undecided, bounded** | inputs are sufficient, but no draft was generated and compared; it may draft `Highlights` prose but cannot be the authority for it |
| Time as the routing key | **No** | 72% of release dates carry 2+ artifacts; route by path + version bump. Time remains fine as a run bound |

Two failure rates fall out, and they are **not additive** — they are measured
over different populations, so no combined figure is reported here:

- **15 of 239 released `(artifact, version)` pairs (6%)** have no discoverable
  bump commit, so no window can be computed for them at all.
- **13 of 166 single-artifact entries that had both boundaries (8%)** produced
  zero `feat`/`fix` candidates despite the entry carrying bullets. "Zero typed
  candidates" is not the same as "no material exists" — an untyped or
  differently-scoped commit may still describe the change.

Combining them would require an entry-level cohort neither rate uses. What can be
said without arithmetic: the mechanical path has a high hit rate on the entries it
reaches, and it reaches most of them. What stays with a person is the `Highlights`
*decision and its approval* — whether the release changed what a consumer can do,
and whether the sentence says so — on the 99 of 214 entries that carry one. That
is a drafting aid under human authority, not an automated changelog, which is
precisely what the repository's header already prescribes.

## Recommended order of work

1. **Key the boundary on the changelog heading, not the manifest.** Manifest
   declaration order is not release order. Measured over 20 windows, the
   heading-commit rule admitted no foreign release's commits where both manifest
   rules polluted 4; it also needs no manifest, which dissolves the 15
   undiscoverable boundaries above. It is not complete — 8 of 20 windows come
   back empty — but an empty window reports that it found nothing, where a
   polluted one confidently describes the wrong release. Search merge diffs when
   resolving it: a heading can enter through a merge resolution, which plain
   `git log -S` never shows. Detail in
   [the inputs spike](changelog-generator-quality-spike.md) Result 6.
2. **Collector only.** A read-only report: given an artifact, resolve its previous
   released version and list the commits in that subtree,
   **carrying each commit's change type** and applying the provisional exclusion
   list rather than a `feat`/`fix` include-list — the latter drops 42 untyped
   commits, 4 `perf:`, 2 `revert:` and 1 `Delivered` across the measured entries.
   No writes, so it cannot damage anything, and it makes the documented workflow
   faster.
3. **Generator to a draft in the implementation PR.** Emits `Added`/`Changed`/
   `Fixed` groups, leaves `Highlights` to a person. The implementation PR is
   where the changelog header requires highlights to be written — "the same PR as
   the implementation", with "no separate editorial process" — so drafting in a
   *release* PR instead would be a change to that header, not just an
   implementation choice.
4. **Carry the change type, and exclude rather than include.** The generator
   inputs spike measured that a `feat`/`fix` include-list drops 42 untyped
   commits, 4 `perf:`, 2 `revert:` and 1 `Delivered`, while an exclusion list
   lets a doc/tooling release report itself as such. Type is an author's label,
   not verified impact, and the inputs spike measured the `docs` rule hiding a
   user-visible install change — so treat the list as candidate policy.
5. **Then choose between generation and fragments** — not before. The two
   disagree about *when* the user-facing sentence is written, and the changelog
   header's "write them in the same PR as the implementation" currently favours
   the fragment side. Step 1 is compatible with either and costs little, so it is
   worth doing before the choice, not after.

The separator gate from the fragmentation spike remains worth doing independently
of all three, and is cheaper than any of them: eight defects are live on `main`
and no located gate detects them.

> **Done on 2026-09-13**, after this spike: the defects were normalized and
> `tools/test_build_site_routing.py::test_every_changelog_section_is_separated`
> gates the class at every heading in `docs/product/changelog.md`. The sentence
> above describes this document's base revision. It changes none of the three
> options, which stay open.

## What this spike did not test

- **Generated output quality.** No entry was actually generated and compared to
  its hand-written counterpart. The 1.0-commits-per-bullet ratio says the inputs
  are *present*, not that a generator would write them well.
- **Multi-artifact entries.** Result 3 measured only the 166 single-artifact
  entries; the 9 entries naming up to 6 artifacts were excluded and have a harder
  attribution problem.
- **Backport, revert, and squash paths.** The 93%-with-body figure describes
  ordinary history; whether every merge path preserves per-change messages was
  not checked.
- **The two adopter-facing changelogs** and the `packs/core/seeds/` template,
  out of scope by instruction.

## Known unknowns

- **Narrowed** by [the generator inputs spike](changelog-generator-quality-spike.md):
  the bullet's facts are largely present in its source commit (median containment
  0.55 against a size-matched control's 0.25) but the sentence is not reused
  (median Jaccard 0.107). Exact token reuse in the shipped bullets is
  content-word vocabulary is largely shared while the two word-sets overlap
  little overall, and the typical bullet was not copied wholesale from a single
  commit. Whether an extractive, templated or model-assisted draft would be
  acceptable remains untested and is the next measurement.
- **Known-unknown:** Why did 15 released versions never appear in their manifest?
  Would be closed by: reading those release commits; the answer decides whether
  6% is a fixable process gap or a permanent floor.
- **Answered** by [the generator inputs spike](changelog-generator-quality-spike.md):
  5 of the 13 have no commits at all in the artifact tree, 4 carry only
  `docs`/`chore`/`refactor` commits, 1 was a `perf:` commit the `feat`/`fix`
  include-list wrongly dropped, 1 is `release:`+`docs:`, and 2 are untyped.
  An exclusion list takes the rate from 8% to 6% and leaves a 5 of 166 (3%)
  no-commit residual.
- **Unknowable:** Whether the 22 order departures were editorial intent or
  accident. Why not: no retained artifact records the intended sequence.
