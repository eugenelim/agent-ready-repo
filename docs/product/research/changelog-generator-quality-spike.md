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

**This is a two-case observation, not a rate.** It says the failure modes are
real and preview-visible; it does not say how often they occur.

## What this means for the design

The three parts separate along the line this spike measured — with the caveat
that only the first two were measured:

| Part | Mechanical? | Basis |
| --- | --- | --- |
| **Collector** — which commits are candidates | **Yes** | boundary, path filter, squash split; deterministic and verifiable, and confirmed by the paired margin above |
| **Exclusion** — dropping non-user-impacting work | **Partly** | change type is recorded data, but type ≠ impact; the list is reviewable policy needing validation |
| **Emphasis** — which change matters and how to say it | **Untested** | output shares few tokens with its source; no generator was implemented, and the two previewed drafts over-published |

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

The collector is confirmed again, now four ways: boundary discoverability, path
attribution, the type census, and a paired 42-of-47 margin over a size-matched
control.

The generator question is **narrowed, not answered**. A shipped bullet shares
much of its content-word vocabulary with its source commit (median containment
0.55) while their two word-sets overlap little overall (median Jaccard 0.107).
Both are unordered token-set measurements. They say nothing about adjacency, so
they cannot detect span-level reuse; nothing about meaning; and nothing about
what a generator could produce. The one inference they carry is that the typical
whole bullet was not copied wholesale from one commit.

Whether extraction, templating, or a model-assisted step can do that is **not
determined here**, because no generator was implemented. The two hand-invoked
drafts in Result 4 illustrate failure modes at n=2; they do not evaluate an
implementation. An overlap statistic cannot answer it either — the next
measurement is a set of rendered drafts compared against what shipped.

Nothing here decides between generation and fragmentation. The
[fragmentation spike](changelog-fragmentation-spike.md)'s three-way decision
stands.

## What this spike did not test

- **Any generator at all** — mechanical, templated, or model-assisted. This is
  the central limit: the spike measures inputs, never outputs.
- **Whether the exclusion list is right.** Derived from observed type vocabulary,
  not validated against a human judgement of user impact.
- **The 42 untyped commits.** Counted, not read.
- **Multi-artifact entries**, excluded here as in the sibling spike.
- **Whether 0.107 Jaccard is low in general** or only here. No reference project
  was measured with the same instrument.

## Known unknowns

- **Known-unknown:** How often does a drafted entry need correcting, and how
  badly? Would be closed by: drafting the last 10 entries from collector output
  and diffing each **rendered entry** against what shipped. Per-bullet
  accept/edit/reject was considered and rejected — it imposes the review overhead
  the tool exists to remove. Result 4 ran this at n=2.
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
