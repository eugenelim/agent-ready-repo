# Changelog fragment build cost — three-arm measurement run

Plan task T13 prices the delivered fragment layout against a monolith holding
the same records, at ten times today's released-entry count. This is the
re-measurement the
[assembly spike](changelog-fragment-assembly-spike.md) asked for: its control
arm ranged from 22.92 s to 75.41 s on identical input, so its `+66.08%` figure
carried no error bound.

- **Run date:** 2026-09-30. Two passes. Pass 1 ran 22:53–01:53 and could not
  produce a whole-build figure. Pass 2 ran after both of pass 1's blockers were
  fixed, and is the authoritative record below. Pass 1 is kept in
  [Pass 1](#pass-1-what-it-established-and-why-it-is-superseded) because it is
  what found the blockers.
- **Verdict, § 7 Build performance:** `INCONCLUSIVE`. All 18 whole builds
  completed this time, but the `today` arm's retained spread is 47.4% of its
  median, and the rule approved before the run refuses a ratio when any arm
  exceeds 20%.
- **Verdict, § 7 Published page count:** `SURVIVE`. Both large arms emit 3,369
  marketing pages, 3,319 `/now/` pages and 267 docs pages, identical in all six
  samples each, from a record set proved identical before timing.
- **Needs a Platform Core maintainer decision.** No observed pairing of the two
  large arms puts the fragment layout within § 7's 10% bar. The closest is
  +26.8%. See [What needs a maintainer](#what-needs-a-maintainer).

## The short version

`make site-build` now works, so § 7's bar can be read for the first time.

| Arm | Retained median | Retained range |
| --- | --- | --- |
| today | 23.69 s | 19.75 – 30.98 |
| monolith-10x | 86.57 s | 84.01 – 93.70 |
| fragments-10x | 129.41 s | 118.77 – 141.27 |

The two large arms hold the same 3,300 records and differ only in physical
layout. Their retained ranges **do not overlap**. The bar is under 10%.

The run is still reported inconclusive, because the approved validity rule is
not conditional on which arm fails. Why that matters, and what it does and does
not license, is in [Validity](#validity-against-the-approved-rule).

## Machine

Non-identifying description. No hostname or user name is recorded.

| Property | Value |
| --- | --- |
| OS and architecture | Darwin 25.5.0, arm64 |
| Logical CPUs | 10 |
| Memory | 34,359,738,368 bytes (32 GiB) |
| Python | 3.13.13 |
| Node | v26.7.0 |
| npm | 11.19.0 |
| Git | 2.50.1 (Apple Git-155) |
| Bare process-spawn latency | 37.9 ms for `/usr/bin/true`, mean of 60 spawns |

**Observed noise.** The machine was not monitored for quiet, and two signals say
it was not. During pass 1's setup another session ran `make build-check` and a
`pytest` suite; both had exited before timing began. In pass 2 the `today` arm's
isolated web phase recorded 39.50 s against 6.67 s and 8.31 s in its sibling
samples — a 4.8× outlier that no corpus property explains. The `today` whole-build
arm also carries the widest spread of the three. Treat the `today` arm as the
contended one. No throttling was observed, and none was checked for.

## Base and overlay identity

| Item | Pass 2 (authoritative) | Pass 1 |
| --- | --- | --- |
| Base commit | `d72fffe55a58d2835128e2967b7d52f2090c6243` | `708ae9cd1c87d16b034e183e7b577d1f80d095c4` |
| Tracked-diff SHA-256 | `de74509c3e23c64990df823cd8f438bf3a0e32f25fb2a94848388bea74fc5659` | `d3112015613d8898cc869b31278ccd31a6030ccf7935238ec4ec4a0fb67d02d5` |
| Overlay manifest SHA-256 | `6e87c7b97ee13a46396f7fa1128f97a031ce223de53418c9ba52b636fedd6719` | `d689726a688012b2639a5e14880a4cf3a42b0b8604601ca4c21c9b06686efdcb` |
| Files in the overlay | 7,008 | 6,743 |
| Files differing from the source worktree | 0 | 0 |

The tracked-diff hash is `git diff HEAD` over the source worktree. The overlay
manifest hash covers every path and content hash in the staged tree, sorted, so
it pins the exact state each pass measured.

Each pass used a disposable **clone**, never a Git worktree, because
`make site-build` cleans `build/` and a worktree shares the parent's Git
directory. The overlay excluded `.git`, `.context`, `build/`, `node_modules/`,
`.astro/`, `dist/`, the Python and test caches, and `.loop-run/`. Everything
else was copied, so each clone carried the untracked implementation —
`tools/changelog.py`, `tools/test_changelog.py`,
`docs/product/changelog-fragment-template.md`,
`tools/measure-changelog-anchor-drift.py` — and the tracked edits to
`tools/build-site.py`. A file-by-file hash comparison found zero content
differences against the source worktree in both passes.

In pass 2 the overlay also carried 262 generated, gitignored files under
`docs-site/src/content/docs/`, left by an earlier local build. They were removed
with `git clean -fdX` scoped to that directory before timing, so no arm inherited
another build's pages and the page counts below are not inflated.

## Setup and commands

```bash
CLONE_ROOT=$(mktemp -d /private/tmp/t13rerun.XXXXXXXX)
git clone --no-hardlinks <source-worktree> "$CLONE_ROOT/repo"
rsync -a --delete <excludes> <source-worktree>/ "$CLONE_ROOT/repo"/
git clean -fdX -- docs-site/src/content/docs        # drop inherited build output
make bootstrap-sites                                 # setup, never inside a measured duration
```

`make bootstrap-sites` installed 457 web packages and 466 docs-site packages,
8 seconds each, 0 reported vulnerabilities. Dependency install is setup and sits
outside every timed sample. Corpus generation, corpus commit and cleanup are
also outside every timed sample.

Timed commands:

```bash
make site-build                        # the metric § 7's bar reads
npm run build --prefix web             # isolated phase, attribution only
npm run build --prefix docs-site       # isolated phase, attribution only
```

All 18 `make site-build` samples returned exit 0. So did all 24 phase samples.

## Corpus

### What "ten times" means here

**Ten times the total, not ten times added.** The locked plan's T13 and the
rewritten § 7 Build performance row both say "a monolith carrying ten times the
released entries". The old spike read § 7's earlier wording as ten times
*added* and reported an 11.0× model; that reading is not inherited here.

| Quantity | Value |
| --- | --- |
| Parsed release records today | 389 |
| Of those, beneath `[Unreleased]` | 59 |
| Today's free-standing released entries | 330 |
| Large-arm total released entries | 3,300 |
| Generated records added to reach it | 2,970 |

### How the records were built

One canonical list of 2,970 records feeds both large arms. Each record is
rendered twice — once as an inline released section, once as a fragment file —
so layout is the only difference.

Each generated record reuses a **real released entry's body, byte for byte**.
The source pool is the 190 of today's 330 released entries that carry a
`Highlights` section and whose body holds no heading-shaped line. That second
filter is needed because the fragment body validator has no fenced-code state
machine, so a `# comment` inside a code block would be refused as a heading.
The pool cycles, so each real body is reused about 15 times.

Per record, only identity changes:

- **Package fan-out** copies the source entry's own fan-out. Today's released
  entries run 321 single-package, four two-package, four five-package and one
  six-package. Two historical package names are not current packs
  (`agentbundle`, `credbroker`); they map by a fixed rule to `core` and
  `credential-brokers` so every generated version resolves in the release
  inventory.
- **Version** is `0.0.<n>` for n = 1..2,970. Every current pack version is
  greater, so `_released_versions_from_packs` admits all of them, and the
  headings stay unique.
- **Date** is the source entry's real release date, so the date spread mirrors
  today's.
- **Fragment id** is a fixed UUIDv4 built from SHA-256 over a fixed namespace
  and the record index. Same inputs, same corpus, every time.

### The two passes measured the same corpus

Pass 2's normalized record-set hash is
`99fb73837c929fd3d0ea95835d90af7764ab7c475c79f7062ea45511ad6828f7` — **identical
to pass 1's**. Today's changelog was also unchanged between passes: 389 parsed
records, 330 released, 190 `/now/` groups, 645,855 characters. So the two passes
differ in code, not in corpus, and their figures are directly comparable.

### Body-size distribution

Bytes of section-body text per generated record:

| min | p25 | median | p75 | max | mean | total |
| --- | --- | --- | --- | --- | --- | --- |
| 148 | 680 | 1,129 | 1,833 | 7,045 | 1,434.5 | 4,260,483 |

These are complete real bodies, not one-bullet stubs. For comparison, today's
330 released sections run 116 to 10,302 bytes with a 911-byte median.

### Equality proof

The proof is a read-back, not an assertion about the generator. Both physical
layouts were written, then parsed back and normalized to
`(packages, date, sections)` with trailing blank lines trimmed.

| Check | Result |
| --- | --- |
| Records read back from the monolith | 2,970 |
| Records read back from the fragments | 2,970 |
| Records present only in the monolith | 0 |
| Records present only in the fragments | 0 |

So entry count, complete body text and bytes, `Highlights`, dates, package
names and versions, and package fan-out are identical across the two large arms.

### Physical layout difference

| Arm | `changelog.md` on disk | `changelog.d/` | Fragment bytes |
| --- | --- | --- | --- |
| today | 648,990 B | absent | — |
| monolith-10x | 5,132,870 B | absent | — |
| fragments-10x | 648,990 B | 2,970 files | 4,977,110 B |

The generated fragments were **committed** in each clone and `origin/main` was
pointed at that commit. That models the real steady state: at ten times today's
release count almost every fragment is old and already merged. It also puts each
fragment on the full identity path through `_enforce_committed_identity`, which
is the path a real build takes.

### Proof the corpus was traversed

Retained stdout from every arm's build:

```
today          0 fragment(s),  190 released highlight group(s),  338 highlight(s)
monolith-10x   0 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
fragments-10x  2970 fragment(s), 3160 released highlight group(s), 5648 highlight(s)
```

The two large arms report the **same 3,160 groups and 5,648 highlights** from
2,970 fragments versus none. The fragment arm's generated payload confirms it
reached the renderer:

```
schemaVersion: 1
groups in generated payload: 3160
bullets: 5648
fragment-sourced groups (UUID-suffixed anchor): 2970
example anchor: core001141--2026-09-29-02123a39434e4b11be4b00376f5531aa
```

## Timing protocol

### Predeclared order

Fixed before any pass-2 timing, and not changed afterwards:

```
today warm-up, monolith warm-up, fragments warm-up,
then five rounds of: today, monolith, fragments
```

One warm-up per arm is discarded. Five retained samples per arm then follow,
round-robin. Pass 2 executed this in full, with no truncation and no
substitution. The isolated phases ran the same interleaved shape, one warm-up
plus three retained per arm per phase, each sample preceded by an untimed
`build-site.py` run so its generated inputs existed before the timer started.

## Whole-build durations — `make site-build`

This is the only command § 7's Build performance row reads.

| Arm | Discarded warm-up | Retained samples (s) |
| --- | --- | --- |
| today | 46.39 | 23.69, 24.90, 30.98, 19.75, 23.12 |
| monolith-10x | 97.75 | 86.57, 90.63, 93.70, 84.47, 84.01 |
| fragments-10x | 140.80 | 131.40, 141.27, 129.41, 128.79, 118.77 |

| Arm | Median | Min | Max | Spread | Spread / median | 20% rule |
| --- | --- | --- | --- | --- | --- | --- |
| today | 23.69 | 19.75 | 30.98 | 11.23 | **47.4%** | **fail** |
| monolith-10x | 86.57 | 84.01 | 93.70 | 9.69 | 11.2% | pass |
| fragments-10x | 129.41 | 118.77 | 141.27 | 22.50 | 17.4% | pass |

## Validity against the approved rule

The rule was approved before any measurement was seen:

```text
(maximum retained duration - minimum retained duration) / median duration <= 20%
```

Applied to each arm on its own:

| Phase | today | monolith-10x | fragments-10x |
| --- | --- | --- | --- |
| whole build | 47.4% **fail** | 11.2% pass | 17.4% pass |
| isolated web | 395.1% **fail** | 38.0% **fail** | 9.2% pass |
| isolated docs-site | 19.0% pass | 10.8% pass | 11.3% pass |

The `today` whole-build arm fails. The rule says any arm failing makes the run
inconclusive, and it is not conditional on which arm, so **no ratio is accepted
or judged from this run.**

Two things are worth stating precisely, because they change what a maintainer
should do next without changing the verdict.

**First, the arms that form the fragment-layout ratio both pass.** That ratio is
the fragment median minus the monolith median over the monolith median. The
`today` arm appears only in the release-growth figure, which § 7 explicitly does
not own. So the failing arm is not one of the two the bar reads.

**Second, the two large arms' retained ranges do not overlap.** The monolith arm
spans 84.01–93.70 s and the fragment arm spans 118.77–141.27 s. Pairing the
fastest fragment sample against the slowest monolith sample — the pairing most
favourable to the design — still gives +26.8%. The bar is under 10%. No pairing
of the ten retained large-arm samples reaches it.

That is a statement about the observed range, not a point estimate, and it is not
drawn from the arm that failed the predicate. It does not convert an invalid
instrument into a result, and the verdict stays `INCONCLUSIVE`.

## Numbers recorded, not accepted

Recorded because the task requires every number even when the run is
inconclusive. **None of these is an accepted result** and none may be cited as a
measured ratio.

```text
whole build, from the medians above
  fragment layout cost  (129.41 - 86.57) / 86.57 = +49.5%
  release growth cost   (86.57 - 23.69) / 23.69  = +265.4%

bounding pairings over the retained large-arm samples
  most favourable to the design   (118.77 - 93.70) / 93.70 = +26.8%
  least favourable                (141.27 - 84.01) / 84.01 = +68.2%
```

## Published page count

Read from emitted HTML after each whole build, and **identical across all six
samples of each arm** — no sample of any arm produced a different count.

| Arm | Marketing pages | `/now/` pages | Docs pages | Release groups |
| --- | --- | --- | --- | --- |
| today | 251 | 201 | 267 | 190 |
| monolith-10x | 3,369 | 3,319 | 267 | 3,160 |
| fragments-10x | 3,369 | 3,319 | 267 | 3,160 |

The two large arms hold the same records at the same release count and emit
**the same page count**, which is what § 7 Published page count requires. Page
count tracks release count, not how entries are stored. Docs pages stay at 267
in every arm, because the changelog is one docs page however its source is
stored. Today's figures are recorded separately, as required; § 7's baseline row
of 216 pages at 157 release groups predates the 190 release groups the changelog
carries today.

## Isolated phases — attribution only

Not the whole-build metric. Each npm phase re-runs `build-site.py
--renderer-inputs` through its own `prebuild` hook, so these do not decompose a
`make site-build`.

| Arm | Web warm-up | Web retained (s) | Web median | Docs warm-up | Docs retained (s) | Docs median |
| --- | --- | --- | --- | --- | --- | --- |
| today | 7.45 | 6.67, 39.50, 8.31 | 8.31 | 15.14 | 16.15, 19.90, 19.72 | 19.72 |
| monolith-10x | 11.44 | 10.66, 16.21, 14.61 | 14.61 | 78.29 | 74.83, 75.60, 83.03 | 75.60 |
| fragments-10x | 27.85 | 37.82, 36.03, 34.51 | 36.03 | 93.88 | 106.41, 106.43, 94.41 | 106.41 |

**These medians sum to more than the whole build they came from.** The fragment
arm's two phase medians total 142.44 s against a 129.41 s whole-build median.
That is itself the proof that a phase sum is not the whole-build metric: inside
one `make site-build` the two prebuild hooks and the Astro content cache are
already warm from the `site-sync` that preceded them, and an isolated sample
pays that cost again. Read these as attribution and nothing else.

Both large arms emit the same page count, so the fragment arm's extra phase
time is fragment reading and assembly plus a slightly larger assembled docs
page — 5,362,696 bytes against the monolith arm's 5,136,434.

## Verdicts

**§ 7 Build performance: `INCONCLUSIVE`.**

All 18 whole builds completed, so the metric exists for the first time. The
`today` arm's retained spread is 47.4% of its median, and the rule approved
before the run refuses a ratio when any arm exceeds 20%.

**§ 7 Published page count: `SURVIVE`.**

3,369 marketing pages, 3,319 `/now/` pages and 267 docs pages in both large
arms, identical in all six samples each, from a record set proved identical
before timing.

## What needs a maintainer

**Whether the fragment layout ships against § 7's 10% bar.** T13's Approach
reserves that decision: "Stop and surface if the fragment-versus-monolith ratio
is at or above the § 7 bar. Whether that blocks delivery is a Platform Core
maintainer decision, not an implementer's." No pairing of the ten retained
large-arm samples puts the design within the bar, and the closest is +26.8%.

Two paths, and this report does not choose between them:

1. **Re-run the `today` arm until it satisfies the predicate**, then read the
   ratio and record a decided verdict. The cost is low now — the full 18-sample
   protocol took about 35 minutes. The `today` arm is the fastest and so the most
   jitter-sensitive, and it carried a 4.8× outlier in the same session, so a
   quiet machine is the whole task.
2. **Decide on the range instead.** The two large arms' retained ranges are
   disjoint and the bar is 10%. A maintainer may judge that sufficient without a
   further pass.

Pass 1's two findings are both already fixed in the tree this pass measured: the
`make site-build` break, and the per-fragment Git fan-out. Neither is open.

## Pass 1: what it established and why it is superseded

Pass 1 ran against base `708ae9cd1` and produced no whole-build figure, because
`make site-build` exited 2 on **all three arms**, today's unmodified corpus
included. `generate_changelog_views` wrote
`docs-site/src/content/docs/changelog.md` with a bare `write_text`, skipping the
Starlight frontmatter that `copy_file` supplied at that commit, and the docs
collection schema rejected the page with `title: Required`.

Pass 1 also counted, by instrumenting `_run_git`, that identity validation ran
**five Git subprocesses per fragment** — one each of `rev-parse`, `merge-base`,
`diff`, `ls-files` and `show`. At 2,970 fragments that was 14,850 spawns per
`build-site.py` run and 44,550 per `make site-build`, because both npm
`prebuild` hooks re-validated the whole directory. Per fragment: 413 ms with
enforcement on against 2.4 ms with it off. The fragment arm's site-sync median
was 1314.08 s, which is why pass 1 could not run the protocol as specified.

Both are fixed in the tree pass 2 measured. Validation now resolves the
repository root, the merge base, one directory-wide changed-path read and one
tracked-path read per pass, and skips the base blob for a path Git reports
unchanged. **Pass 1's fragment-arm durations therefore describe code that no
longer exists and must not be cited as current.** Its corpus, equality proof,
machine description and page-count result all carried forward unchanged.

## Limitations

- **No accepted ratio.** The `today` arm fails the approved dispersion rule at
  47.4%. Every ratio above is arithmetic over medians, recorded and not accepted.
- **The machine was not monitored for quiet**, and two signals say it was not:
  concurrent heavy work by another session during pass 1's setup, and a 4.8×
  outlier in pass 2's `today` web phase.
- **One machine, one session.** Spawn latency here is about 37.9 ms, roughly ten
  times an unmanaged machine's, which inflates any per-process work.
- **Isolated phases are attribution, never the whole-build metric.** Their
  medians sum to more than the whole build, as shown above.
- **Every generated record carries `Highlights`.** The fragment contract
  requires it, so keeping the two arms' record sets identical forces it. Today
  only 190 of 330 released entries carry one. The large arms therefore project
  more `/now/` groups per entry than today's corpus does, which inflates page
  count in **both** large arms equally and so does not affect their equality.
- **The release-growth figure is the weakest number here.** It is the one ratio
  that reads the failing arm, and § 7 does not own it.

## Disposable clones

| Pass | Exact resolved path | Size | Deletion proof |
| --- | --- | --- | --- |
| 2 | `/private/tmp/t13rerun.04f7nIIp` | 1.0 GB | `test -e` → false; no `/private/tmp/t13rerun.*` remains |
| 1 | `/private/tmp/t13-buildcost.9tLaEfdC` | 1.0 GB | `test -e` → false; no `/private/tmp/t13-buildcost.*` remains |

Each delete target was the resolved absolute path, checked against its expected
prefix before running. Both clones were created with `mktemp -d` and removed
after their pass.
