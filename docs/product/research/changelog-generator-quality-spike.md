# Changelog generator inputs — measurement spike

Measures the two questions left open by
[the collector/generator evaluation](changelog-collector-generator-spike.md):
how much of a shipped changelog bullet is present in its source commit, and what
the windows that yield no candidate actually contain.

- **Run date:** 2026-09-13
- **Owner:** eugenelim, Platform Core maintainer
- **Base:** `e45f7c355`
- **Verdict:** a bullet shares much more content-word vocabulary with its own
  release window than with a size-matched control, and the typical bullet was not
  copied wholesale from a single commit. **No generator was implemented**; two
  entries were drafted by hand-invoked model assistance and previewed (Result 4),
  which is an illustration, not an evaluation. See [Verdict](#verdict).
- **Scope:** evidence only. No production code was written; the prototype is
  throwaway and lives outside the repository.

## What this spike does and does not measure

It measures **word overlap** between a shipped changelog bullet and the commits
in its release window, under two metrics, against a size-matched control.

It does **not** measure generability. No generator was built, and Results 1–3
compare no draft against anything; every statement in them is about overlap, with
any inference about implementations marked `[inference]` and kept narrow.

Result 4 is different in kind and is bounded accordingly: two entries were
drafted by hand-invoked model assistance from collector output and compared as
rendered previews. Two cases illustrate failure modes. They measure no rate, and
they evaluate no implementation.

## Method and evidence

Two scripts with retained stdout as the evidence of record: `spike_generator.py`
(Result 2) and the zero-yield census (Result 3). Release records come from
`tools/build-site.py`'s `parse_changelog_releases`, so the spike counts what the
`/now/` projection sees.

Ten most recent released entries with a discoverable version-bump window; 47
shipped bullets; each scored against the best-matching commit unit in its own
window.

**The control arm** scores the same bullets against a *different artifact's*
window, because shared project vocabulary alone produces a floor. It is
**size-matched**: the control window is the different-artifact window whose unit
count is closest to the treatment's. Without matching, a best-of-N score rises
with N, and the treatment would win partly by being searched harder — one window
in the sample holds 122 units and another holds 2.

Both arms score the same 47 bullets, so the comparison is **paired** and is
reported that way rather than as a ratio of medians.

## Result 1 — the instrument was wrong first, and the correction changed the design question

The first run scored by **containment**: the share of the bullet's content words
appearing in the best-matching commit message. It looked decisive. It was
inflated, for a reason that turns out to matter to the collector too.

One commit message in the sample is **152,115 characters** — a squash-merged
pull request concatenating every constituent commit. Containment has no length
penalty, so a bag of words that large contains almost any bullet by accident.
Across the 939 window messages, the median is 1,607 characters but **33 (4%)
exceed 10,000**.

Two corrections:

1. **Report Jaccard as well as containment.** Jaccard is symmetric, so a match
   won by sheer size is penalised. It has its own bias in the opposite
   direction — a long source dilutes the score — so both are reported and
   neither is treated as the truth on its own.
2. **Split squash-merge messages** on the `* ` subject lines a squashed body
   carries. This is a collector requirement, not a measurement convenience: a
   collector that skips it sees one pull request as one change. Splitting turned
   the `core` 2.25.16 window from 2 units into 122.

The first run's numbers are superseded and not quoted here; the corrected run
retains both metrics so the difference is auditable.

## Result 2 — high containment, low symmetric overlap

| Metric | Treatment (own window) | Control (size-matched) |
| --- | ---: | ---: |
| **Containment** median | **0.55** | 0.25 |
| Containment ≥ 0.3 | 91% | 34% |
| Containment ≥ 0.5 | 62% | 9% |
| Containment ≥ 0.7 | 26% | 2% |
| **Jaccard** median | **0.107** | 0.039 |
| Jaccard ≥ 0.2 | 13% | 0% |
| Jaccard ≥ 0.3 | 2% | 0% |
| Jaccard ≥ 0.5 | 0% | 0% |
| **Paired: treatment scores higher** | **42 / 47 bullets (89%)** | 3 tied |

Three readings, in decreasing confidence.

**The window is the right window.** Treatment beats a size-matched control on 42
of 47 paired bullets, with a median Jaccard difference of 0.068. This is a fourth
independent confirmation of the *collector* — the material a bullet draws on is
in the window the boundary-plus-path rule selects.

**Vocabulary overlap is high.** 62% of bullets have at least half their content
words present in a single source commit, against 9% for the control. That is a
lexical measurement: shared content words are consistent with the commit
describing the same change, but a bag-of-words comparison cannot establish that
it states the same facts.

**Symmetric token-set overlap is low.** No bullet reached 0.5 Jaccard against
its best match. High containment alongside low Jaccard is *consistent with* the
bullet being a longer, differently-framed restatement — but the instrument cannot
distinguish that from a bullet that is simply longer than its source, or that
draws on several commits at once. What is measured is the overlap, not the
process that produced it.

The worked example is the clearest single piece of evidence — the same change,
0.54 containment and 0.10 Jaccard:

> **Shipped:** "**A legacy-only repository can activate its knowledge base even
> when the migration has nothing to import.** Activating was the first command
> such a repository runs, and it crashed on the state those repositories are
> actually in: an empty `patterns.jsonl`…"
>
> **Commit:** "fix(core): stage the migration root so a zero-row legacy corpus
> activates — `_stage_legacy_migration_locked` crashed with an unhandled
> `FileNotFoundError` whenever a legacy migration yielded zero importable
> topics…"

Read as prose, the subject changes from the function to the user and the lede
becomes what someone can now do — which is the transform `changelog.md`'s header
asks for ("Rewrite for users, not contributors", "Outcome, not activity"). That
reading is a human judgement about one example, not something the instrument
measured.

**What this does and does not license.** One distinction carries the weight, and
collapsing it in either direction would be wrong.

*Supported:* the typical bullet was not copied **wholesale from a single
commit**. Median containment is 0.55 — about half the bullet's content words are
absent from its single best-matching commit unit — so a whole-bullet copy is not
what usually happened. [inference]

*Not supported:* that extraction played no part. Jaccard compares a whole bullet
against a whole commit unit, so a copied *span* inside a longer source scores
low, and spans drawn from several commits score lower still. The instrument
cannot see span-level reuse at all, and a median says nothing about any
individual bullet.

*Also not supported:* that an extractive or templated generator could not produce
an **acceptable** bullet. That is a different question again — it asks about a
bullet nobody has written, judged by a reviewer nobody has asked. Deciding it
needs a draft and a verdict, not an overlap statistic.

## Result 3 — the include-list is the wrong filter, and change type should be carried

The sibling evaluation reported 13 of 166 windows (8%) yielding no candidate
under a `feat:`/`fix:` include-list, and left open whether those were doc or
tooling releases with legitimately nothing to say.

Partly yes. The 13 break down as:

| Kind | Count | What it means |
| --- | ---: | --- |
| No commits at all in the artifact's tree | 5 | boundary problem, all early history (`core` 1.0.0 → 2.3.0) |
| Every commit `docs`, `chore`, or `refactor` | 4 | doc/tooling releases by commit type |
| A single `perf:` commit | 1 | **user-impacting by any reading — 6 bullets shipped** |
| `release:` + `docs:` | 1 | release mechanics |
| Unparseable subjects | 2 | invisible to any type filter |

Switching from an **include-list** (`feat`, `fix`) to an **exclusion list**
(`docs`, `chore`, `test`, `ci`, `style`, `build`, `release`, `refactor`):

- Zero-candidate windows fall from **13 (8%) to 10 (6%)**.
- Those 10 split evenly: **5 have no commits at all**, and **5 are windows where
  every commit carries an excluded type**. That fifth all-excluded window is the
  `release:` + `docs:` row above, which the narrower three-type census counted
  separately — hence 4 in the table and 5 under the broader list.
- The include-list was dropping: **42 untyped commits, 4 `perf:`, 2 `revert:`,
  and 1 `Delivered`**.

The actionable finding: **the collector should carry each commit's change type as
data and apply an explicit exclusion list.** An exclusion list surfaces an
unrecognised or untyped commit for a human instead of silently dropping it, and
lets a doc/tooling release be *reported as such* rather than looking like a
collector failure.

**The limit on that finding.** Commit type is an author's label, not a
verified statement of user impact. The `perf:` case proves they diverge: it was
dropped by type while shipping six bullets. So the exclusion list above is a
**candidate policy**, not a validated one — it was derived from the observed type
vocabulary, never checked against a human judgement of which releases owed an
entry, and a misclassified commit is still dropped silently. The 5 of 166 (3%)
residual is a **no-commit rate**, not a measured true-failure rate.

## Result 4 — a rendered preview is both the review surface and the instrument

Per-bullet adjudication was rejected as a measurement: it imposes exactly the
review overhead a generator exists to remove. The substitute is a **rendered
preview of the entry**, judged whole. It costs one glance, and in these two cases
it exposed distinctions an overlap score cannot represent at all — which is a
statement about what the two instruments can express, not a ranking established
at this sample size.

Two entries were drafted from collector output alone — the admitted commits'
full messages, with the shipped entry deliberately not in view — then compared.

**`desk-research` 1.1.8 — close.** Two bullets, correct group, no invented
content. The shipped text is shorter and addresses the reader ("sets that
default up for you"); the draft explains the mechanism instead.

**`architect` 0.15.8 — three distinct failures, all visible at a glance:**

| Failure | Draft | Shipped |
| --- | --- | --- |
| **Over-publication** | invented a `Highlights` block | none — the maintainer chose not to publish to `/now/` |
| **Over-inclusion** | added a `Fixed` bullet on instruction ordering | omitted; judged not user-visible |
| **Missing prior value** | "output base is `docs/architecture`" | "defaults to `docs/architecture` **rather than `docs/design`**" |

The third is worth watching, and it held in **one of the two cases**. The
`architect` commit gave the new base without the prior `docs/design`, and said a
section was declared without naming `architecture`; both appear in the shipped
bullet. The `desk-research` commit, by contrast, *did* state its prior
documentation state, and the draft carried it through.

So the pattern is "a commit may state what changed without stating what it
changed from", and where it does not, no collector recovers the before-value from
the message — it comes from the diff or the author. How often that happens needs
a larger sample.

The first two are an over-emphasis failure mode: given material, this drafter
published it. The header's rule that a release may correctly carry *no*
`Highlights` is a judgement the commit record does not contain, and getting it
wrong pushes copy onto a public page that the maintainer withheld. Whether some
other generator could make that call was not tested.

**This is a two-case observation, not a rate**, and Result 5 supersedes its
reading: at n=10 the Highlights decision was right 7 times out of 10, and
over-publication is not the dominant failure. What survives from these two cases
is that the preview surfaces failures at a glance.

## Result 5 — ten drafted entries, judged independently: attribution fails before prose does

Result 4 ran at n=2 and pointed at over-publication. At n=10 that is not the
dominant failure, and the real one is more serious.

Ten entries were drafted from collector output alone, shipped entry not in view,
then judged by an independent reviewer who did not write them. Drafts were
scored on the Highlights decision, group match, coverage of shipped bullets,
over-inclusion, missing prior values, and an overall verdict.

| Verdict | Count |
| --- | ---: |
| Usable as-is | 2 |
| Usable after light edit | 4 |
| Needs rewrite | 2 |
| **Wrong content entirely** | **2** |

- **Highlights decision: 7 of 10 correct** — 1 over-published, 2 under-published.
  Result 4's n=2 reading, that over-emphasis is *the* failure mode, does not
  survive the larger sample.
- **Coverage: 18 of 26 shipped bullets (69%)** had a recognisable counterpart.
- **Over-inclusion: 7 drafted bullets across 5 entries** had no counterpart.
- **Missing prior value: 8 of 10 entries.** This one did generalise.

### The dominant failure is release attribution, not sentence quality

**Four of the ten windows are wrong or polluted** — two describe the wrong
release entirely, two more admit a neighbouring release's work:

| Entry | What the collector handed the drafter |
| --- | --- |
| `core` 2.25.15 | 2.25.14's event-envelope work |
| `core` 2.25.12 | 2.25.13's missing-`git` fix |
| `core` 2.25.7 | window reads `2.25.5 -> 2.25.7`, admitting 2.25.6's work **and a merged 2.25.4 fix** |
| `core` 2.25.4 | a commit whose own subject says `core 2.25.3` |

The root cause is in the boundary rule, not the drafter. The collector resolves a
window from **the first commit that declared a version in the manifest**, and
that is not release order: versions get renumbered when branches collide. One
admitted commit in the `core` 2.25.7 window says so outright — "main took 2.25.4
… the consumer seam becomes 2.25.5, and the cooling diagnosis becomes 2.25.6".
A window built on declaration order therefore skips releases and spans others.

Renumbering is demonstrated for the sampled failures — a merge commit in the
window says so — but it is **not** established as the cause of the 15
undiscoverable boundaries in Result 3. That cause remains unconfirmed and stays a
known unknown. What is established is that this is the first measured defect in
the collector, which until now had been confirmed four ways.

**No amount of better drafting repairs these two entries** — that is the
load-bearing result. It does not mean drafting is fine. Among the correctly
attributed drafts the judge named a distinct weakness: *commit-message
transcription instead of release synthesis*, preserving maintenance detail while
losing the consumer outcome. Prompt quality cannot repair a wrong window;
drafting quality remains measurable only once the window is right.

### The exclusion list hid a user-visible change

`core` 2.25.15 shipped a documentation correction, and the commit carrying it —
`docs(packs): correct what the layout append actually does, and release it` —
was **excluded by the `docs` rule** recommended in Result 3. A `docs:` commit
that changes what an install does is user-visible. The exclusion list is
therefore not only unvalidated but measurably over-broad on this corpus.

### Which omissions were the drafter's fault, and which the source's

This split is the most decision-relevant output, because only the first kind is
fixable by better generation:

**Drafting failures — the fact was in the admitted commits and the draft lost
it:** the literal section value `design`, stated plainly in the commit and
omitted from the `experience-design` draft; `core` 2.25.2's checkpoint cadence,
where the commit says "the third round and every second round after" and the
draft wrote "from the third round"; the legacy `spec/<slug>` path in `core`
2.25.4; and `product-engineering` 0.13.12, where the material for a Highlight
was present across three repair commits and the draft failed to synthesise it.

**Source limits — the fact was never in the commits.** Examples, not an
exhaustive list: the `strategy` section value, which its commit never names while
explicitly warning that section names are not derivable from pack names; the
exact retained and removed field names in `core` 2.25.11;
`product-engineering` 0.13.12's "second, advisory read" wording, absent because
the window opens on repair commits rather than the originating feature; and the
literal consumer name `architect-design` in `architect` 0.15.7.

### Where a draft beat what shipped

Three drafts carried material the shipped entry dropped: `architect` 0.15.7
enumerated the selection-failure classes rather than compressing them; `core`
2.25.11 kept the before/after measurements (220,195 → 86,510 characters; 646 → 3
lines) that substantiate its performance claim; and `core` 2.25.7 stated plainly
that the race window is narrowed rather than closed. None of the three drafts is
better *overall*, but "shipped" is the release of record, not automatically the
better artifact.

### What this sample cannot support

The two catastrophic misses are collector faults, so this is **not** a measured
rate of drafting quality — scoring them as drafting failures would be false. A
clean measurement of drafting needs a boundary rule that proves release
ownership first.

## Result 6 — four boundary rules at n=20: one never pollutes, none is complete

Result 5 named the boundary rule as the collector's first measured defect. Four
candidate rules were compared over the 20 most recent single-artifact entries,
scored by two detectors that do not depend on which rule produced the window:
**foreign** (an admitted commit's message names a different version of the same
artifact — the signal the independent judge used) and **span** (another release's
boundary falls inside the window).

| Rule | Clean | Polluted | Empty | No boundary |
| --- | ---: | ---: | ---: | ---: |
| R1 first manifest declaration *(shipped)* | 12 | **4** | 4 | 0 |
| R2 last manifest declaration | 12 | **4** | 4 | 0 |
| **R3 commit that added the changelog heading** | 12 | **0** | 8 | 0 |
| R4 commit that bumps the manifest *and* touches the changelog | 10 | 3 | 3 | 4 |

**Release tags were ruled out before testing.** 113 tags exist, but they cover
only `agentbundle` (60) and `credbroker` (7) — 2 of the 24 artifacts that
release. No pack carries one.

### R3 never admits another release's commits

Zero polluted windows, against four for both manifest rules. Keying the boundary
on the changelog heading also needs no manifest at all, which dissolves Result
3's 15 undiscoverable boundaries: every released entry has a heading by
construction.

### But no rule is complete, and R3 fails more often — differently

R3 returns 8 empty windows against 4. The counts of *usable* windows are
therefore identical at 12 of 20 for R1, R2 and R3; what differs is the failure
mode.

A hybrid — R3's boundary, falling back to R2 when empty — **recovers nothing**,
and this is derivable from the data rather than needing another run. R3's eight
empty windows are exactly R1/R2's four empties plus R1/R2's four *polluted*
windows. Every window R3 leaves empty is either empty under the manifest rules
too, or only non-empty there because it is polluted.

That splits the 20 cleanly:

- **12 — clean under R3.**
- **4 — empty under every rule.** `core` 2.25.20, 2.25.18, 2.25.14, 2.25.10 have
  no admitted commits in the artifact's subtree at all. That is a *path-filter*
  limit, not a boundary one: the work sat outside `packs/core/`.
- **4 — separable by no tested rule.** `core` 2.25.19, 2.25.17, 2.25.13, 2.25.9
  are empty under R3 and polluted under R1/R2.

### Why R3 is still the right rule

Equal usable rate, but its failures are **empty rather than wrong**. An empty
window reports that it found nothing to draft from; a polluted window produces a
confident entry describing the wrong release, which is exactly what produced
Result 5's two zero-coverage drafts. Fail-loud beats fail-wrong when the output
is published prose.

### A finding that outlives the rule choice

Both the heading and the version bump can enter the mainline through a **merge
resolution**, and `git log -S` does not show a merge's diff. The first run of
this comparison reported that `core` 2.25.19's heading — plainly present in the
file — had never been introduced by any commit. Eight boundaries were missing for
that reason alone. Any collector must search merge diffs (`--diff-merges=first-parent`)
or it will silently conclude that released versions do not exist.

## What this means for the design

The three parts separate along the line this spike measured — with the caveat
that only the first two were measured:

| Part | Mechanical? | Basis |
| --- | --- | --- |
| **Collector** — which commits are candidates | **Partly** | path filter and squash split hold; the version-bump *boundary* is defective — Result 5 shows 4 of 10 windows wrong or polluted |
| **Exclusion** — dropping non-user-impacting work | **Partly, and over-broad** | change type is recorded data, but type ≠ impact; Result 5 shows the `docs` rule hiding a user-visible install change |
| **Emphasis** — which change matters and how to say it | **Measured once, at n=10, confounded** | 2 usable as-is, 4 after light edit, 2 needing rewrite, 2 wrong content — but 4 windows were wrong or polluted, so the aggregate scores the collector as much as the drafter |

`changelog.md`'s header constrains where a model may sit. It forbids one **in the
automation path** — "no model runs in CI, release automation, or site
generation" — while expressly allowing model-assisted authoring under human
authority: "Drafting them with AI assistance is fine — the reviewer, not the
drafter, is the authority."

The same header also says highlights are written **"in the same PR as the
implementation"**, with "no separate editorial process". So a model-assisted
drafting step is admissible **in the implementation PR**. Moving that drafting
into a release PR would be a **policy change to the header**, not merely an
implementation choice — the same tension the fragmentation spike records.

## Verdict

The collector's *selection* is confirmed four ways — boundary discoverability,
path attribution, the type census, and a paired 42-of-47 margin over a
size-matched control. Its **boundary rule is not**: Result 5 found 4 of 10
windows wrong or polluted — two handing the drafter an entirely different
release, two admitting a neighbour's work — because manifest-declaration order is
not release order once versions are renumbered on merge. That is the first
measured defect in the collector and it precedes every generator question.

The generator question is **narrowed, not answered**. A shipped bullet shares
much of its content-word vocabulary with its source commit (median containment
0.55) while their two word-sets overlap little overall (median Jaccard 0.107).
Both are unordered token-set measurements. They say nothing about adjacency, so
they cannot detect span-level reuse; nothing about meaning; and nothing about
what a generator could produce. The one inference they carry is that the typical
whole bullet was not copied wholesale from one commit.

Whether extraction, templating, or a model-assisted step can do that is **not
determined here**, because no generator was implemented. Result 5 evaluates ten
hand-invoked drafts and returns 6 of 10 usable or near-usable — but with 4 of 10
windows wrong or polluted, that figure scores the collector as much as the
drafter. A clean drafting measurement needs a boundary rule that proves release
ownership first.

Nothing here decides between generation and fragmentation. The
[fragmentation spike](changelog-fragmentation-spike.md)'s three-way decision
stands.

## What this spike did not test

- **Any generator implementation.** Results 4 and 5 evaluate twelve entries
  drafted by hand-invoked model assistance; no mechanical, templated, or
  production generator was built or run, and no automated pipeline was tested.
- **Whether the exclusion list is right.** Derived from observed type vocabulary,
  not validated against a human judgement of user impact.
- **The 42 untyped commits.** Counted, not read.
- **Multi-artifact entries**, excluded here as in the sibling spike.
- **Whether 0.107 Jaccard is low in general** or only here. No reference project
  was measured with the same instrument.

## Known unknowns

- **Answered, with a confound**, by Result 5: ten drafts scored 2 usable as-is,
  4 after light edit, 2 needing rewrite, 2 wrong content. Four windows were wrong
  or polluted, so this measures the collector as much as the drafter. **Re-run it
  after the boundary rule is repaired** for a clean figure.
- **Answered** by Result 6: the changelog-heading rule admits no foreign
  commits in 20 windows, against 4 for both manifest rules; release tags cover
  only 2 of 24 artifacts and were ruled out. No rule is complete — 8 of 20
  windows come back empty under it.
- **Known-unknown:** Where does the work for the 4 windows that are empty under
  every rule actually live? Would be closed by: widening the path filter beyond
  the artifact's subtree for those four releases and seeing what appears.
- **Known-unknown:** Can the before-value be recovered mechanically? Would be
  closed by: checking whether the diff of the release commit yields the prior
  value for the kind of setting a changelog bullet cites, since the commit
  message does not.
- **Known-unknown:** Does an exclusion list drop user-impacting work? Would be
  closed by: labelling by hand which of the measured releases owed an entry, and
  scoring the list against that labelling rather than against itself.
- **Known-unknown:** Do the 42 untyped commits contain user-impacting change?
  Would be closed by: reading them; the answer decides whether untyped commits
  need a fallback rule.
- **Unknowable:** Whether a commit's author could have written the user-facing
  sentence at commit time. Why not: the counterfactual was never run, and the
  commit messages that exist were written for contributors by instruction.
